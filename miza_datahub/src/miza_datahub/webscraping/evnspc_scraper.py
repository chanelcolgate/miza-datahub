import os
import time

import ddddocr
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from miza_datahub.common.config_util import ConfigUtil
from miza_datahub.common import config_const as ConfigConst
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient
from miza_datahub.influxdb.writers.electricity_writer import ElectricityWriter


class EVNSPCScraper:
    def __init__(self, headless=True):
        config_util = ConfigUtil()

        # Selenium
        self.url = config_util.get_property(
            section=ConfigConst.SELENIUM, key=ConfigConst.URL
        )
        self.username = config_util.get_property(
            section=ConfigConst.SELENIUM, key=ConfigConst.USERNAME
        )
        self.password = config_util.get_property(
            section=ConfigConst.SELENIUM, key=ConfigConst.PASSWORD
        )
        self.captcha_dir = config_util.get_property(
            section=ConfigConst.SELENIUM, key=ConfigConst.CAPTCHA_DIR
        )

        # InfluxDB
        influx_host = config_util.get_property(
            section=ConfigConst.INFLUX,
            key=ConfigConst.INFLUX_HOST,
            default_val="localhost",
        )
        influx_port = config_util.get_int(
            section=ConfigConst.INFLUX,
            key=ConfigConst.INFLUX_PORT,
            default_val=8090,
        )
        influx_db = config_util.get_property(
            section=ConfigConst.INFLUX,
            key=ConfigConst.INFLUX_DB,
            default_val="dongtien",
        )

        self.influx = InfluxRestClient(influx_host, influx_port, influx_db)

        edge_options = Options()
        # edge_options.add_argument("--kiosk")
        edge_options = Options()
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")

        # Bắt buộc đặt độ phân giải lớn để layout không bị vỡ/chồng đè
        edge_options.add_argument("--window-size=1920,1080")

        if headless:
            edge_options.add_argument("--headless=new")

        service = Service(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=service, options=edge_options)
        self.wait = WebDriverWait(self.driver, 20)
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _solve_captcha(self) -> str:
        os.makedirs(self.captcha_dir, exist_ok=True)
        captcha_path = os.path.join(self.captcha_dir, "captcha.png")

        img_element = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, '//img[@id="imgCaptcha"]')
            )
        )
        img_element.screenshot(captcha_path)

        with open(captcha_path, "rb") as f:
            img_bytes = f.read()
        return self.ocr.classification(img_bytes).upper()

    def login(self, max_retries: int = 3) -> bool:
        for attemp in range(1, max_retries + 1):
            try:
                self.driver.get(self.url)
                # self.driver.maximize_window()
                login_card = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//*[@class="login-choice-card"]')
                    )
                )
                login_card.click()

                user_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@name="Username"]')
                    )
                )
                user_input.clear()
                user_input.send_keys(self.username)

                pass_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@name="Password"]')
                    )
                )
                pass_input.clear()
                pass_input.send_keys(self.password)

                captcha_code = self._solve_captcha()
                # print(captcha_code, self.username, self.password)
                captcha_input = self.wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//input[@name="clientCaptcha"]')
                    )
                )
                captcha_input.clear()
                captcha_input.send_keys(captcha_code)

                login_btn = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//input[@id="btnDangNhap"]')
                    )
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", login_btn
                )
                time.sleep(0.5)
                login_btn.click()

                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//input[@id="first-day"]')
                    )
                )
                return True
            except Exception as e:
                print(
                    f"[Attemp {attemp}/{max_retries}] Đăng nhập thất bại: {e}"
                )
                time.sleep(2)
        raise RuntimeError("Đăng nhập EVNSPC thất bại sau nhiều lần thử lại.")

    def scrape_data(self, start_date: str, end_date: str) -> list[dict]:
        first_day = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@id="first-day"]')
            )
        )
        first_day.clear()
        first_day.send_keys(start_date)

        last_day = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//input[@id="last-day"]')
            )
        )
        last_day.clear()
        last_day.send_keys(end_date)

        search_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//input[@id="idTraCuu"]'))
        )
        # search_button.click()
        self.driver.execute_script("arguments[0].click();", search_button)

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@class="quantity-tbl"]/table/tbody/tr[1]')
            )
        )
        time.sleep(1)

        TIER_MAP = {
            "Bình thường": "normal_tier",
            "Cao điểm": "peak_tier",
            "Thấp điểm": "off_peak_tier",
        }

        rows = self.driver.find_elements(
            By.XPATH, '//div[@class="quantity-tbl"]/table/tbody/tr'
        )

        results = []
        current_data = {}

        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")

            if len(tds) == 5:
                date_text = tds[1].text.strip()
                type_name = tds[2].text.strip()
                val = float(tds[4].text.strip().replace(",", ""))

                current_data = {
                    "timestamp": date_text,
                    "normal_tier": 0.0,
                    "peak_tier": 0.0,
                    "off_peak_tier": 0.0,
                    "total": 0.0,
                }

                if type_name in TIER_MAP:
                    current_data[TIER_MAP[type_name]] = val

            elif len(tds) == 3:
                type_name = tds[0].text.strip()
                val = float(tds[2].text.strip().replace(",", ""))

                if type_name in TIER_MAP:
                    current_data[TIER_MAP[type_name]] = val

            elif len(tds) == 2:
                total_val = float(tds[1].text.strip().replace(",", ""))
                current_data["total"] = total_val

                results.append(current_data.copy())

        return results

    def close(self):
        if hasattr(self, "driver") and self.driver:
            self.driver.quit()

    def write(self, raw_data):
        writer = ElectricityWriter(self.influx)
        writer.write(raw_data)
        return True
