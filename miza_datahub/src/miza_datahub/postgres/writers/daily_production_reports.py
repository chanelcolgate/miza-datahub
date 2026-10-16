from itertools import groupby
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date

import openpyxl
import pandas as pd

import miza_datahub.postgres.excel as excel
import miza_datahub.services.grafana_time as grafana_time
from miza_datahub.postgres.postgres_repository import PostgresRepository
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient
from miza_datahub.influxdb.queries.oee.dongtien_realtime_query import (
    DongTienRealtimeQuery,
)
from miza_datahub.common.config_util import ConfigUtil
from miza_datahub.common import config_const as ConfigConst


class DailyProductionReports:
    PG_TABLE = "daily_production_reports"

    def __init__(
        self, pg_repo: PostgresRepository, influx_client: InfluxRestClient
    ):
        """
        Args:
            pg_repo: instance of PostgresRepository
            influx_client: instance of InfluxRestClient
        """
        config_util = ConfigUtil()

        self.report_temp = config_util.get_property(
            section=ConfigConst.EXCEL,
            key=ConfigConst.REPORT_TEMP,
            default_val="./data/report_template.xlsx",
        )
        self.pg = pg_repo
        self.realtime_repo = DongTienRealtimeQuery(influx_client)

        self.cycle = [
            ("C", "A"),
            ("C", "A"),
            ("B", "C"),
            ("B", "C"),
            ("A", "B"),
            ("A", "B"),
        ]
        # cols
        self.date_col = "A"
        self.finished_production_cols = {"A": "C", "B": "E", "C": "G"}
        self.roll_production_cols = {"A": "B", "B": "D", "C": "F"}

        self.min_ton = config_util.get_float(
            section=ConfigConst.REPORTS,
            key=ConfigConst.MIN_TON,
            default_val=20.0,
        )
        self.phase_loopback_days = config_util.get_int(
            section=ConfigConst.REPORTS,
            key=ConfigConst.PHASE_LOOPBACK_DAYS,
            default_val=12,
        )
        self.ndigits = config_util.get_int(
            section=ConfigConst.REPORTS, key=ConfigConst.NDIGITS, default_val=3
        )
        self.first_row = config_util.get_int(
            section=ConfigConst.REPORTS,
            key=ConfigConst.FIRST_ROW,
            default_val=16,
        )

    def ensure_table_exists(self) -> None:
        """
        Create table if not exists. Adjust schema as needed.
        """
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.PG_TABLE} (
                report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                report_date DATE NOT NULL,
                shift_no INT DEFAULT NULL,
                grade_id UUID,
                crew_id UUID,
                -- Sản lượng (Tấn)
                actual_production_ton FLOAT DEFAULT 0.0,
                warehouse_in_ton FLOAT DEFAULT 0.0,
                defect_ton FLOAT DEFAULT 0.0,
                -- Năng lượng & Nguyên liệu tiêu hao
                total_electricity_kwh FLOAT DEFAULT 0.0,
                spec_electricity FLOAT DEFAULT 0.0,
                total_steam_ton FLOAT DEFAULT 0.0,
                spec_steam FLOAT DEFAULT 0.0,
                total_water_m3 FLOAT DEFAULT 0.0,
                spec_water FLOAT DEFAULT 0.0,
                total_pulp_kg FLOAT DEFAULT 0.0,
                spec_pulp FLOAT DEFAULT 0.0,
                -- Thời gian vận hành & Hiệu suất
                run_time_hours FLOAT DEFAULT 0.0,
                downtime_hours FLOAT DEFAULT 0.0,
                availability_rate FLOAT DEFAULT 0.0,
                productivity_tph FLOAT DEFAULT 0.0,
                -- Nội dung văn bản điền vào cột Tình hình sản xuất
                production_notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT uk_report_date_shift UNIQUE (
                    report_date, shift_no
                )
            );
        """
        self.pg.execute(create_sql)

    def save_dataframe_to_postgres(self, df: pd.DataFrame) -> int:
        """
        Upsert DataFrame rows into Postgres. Returns number of affected rows.
        """
        if df.empty:
            return 0

        # ensure table
        self.ensure_table_exists()

        insert_sql = f"""
            INSERT INTO {self.PG_TABLE} (
                report_date, shift_no, grade_id, crew_id,
                actual_production_ton, downtime_hours, production_notes
            ) VALUES (
                :report_date, :shift_no, :grade_id, :crew_id,
                :actual_production_ton, :downtime_hours, :production_notes
            )
        """

        data: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            data.append(
                {
                    "report_date": row["report_date"].isoformat(),
                    "shift_no": row["shift_no"],
                    "grade_id": row["grade_id"],
                    "crew_id": row["crew_id"],
                    "actual_production_ton": row["actual_production_ton"],
                    "downtime_hours": row["downtime_hours"],
                    "production_notes": row["production_notes"],
                }
            )
        return self.pg.execute_many(insert_sql, data)

    # --- export excel ---
    def export_report_to_excel(
        self,
        from_time: str = "now-30d",
        to_time: str = "now",
        *,
        merge_spill: bool = False,
        write_dates: bool = True,
        phase: Optional[int] = None,
        week_start: int = 0,
        now: Optional[datetime] = None,
    ) -> None:
        """
        from_time/to_time: cú pháp time picker Grafana, ví dụ
            "2026-09-13T17:00:00.000Z" / "2026-10-04T16:59:59.000Z"
            "now-30d" / "now"   "now-1w/1w" / "now-1w/w"    "now/M" / "now/M"
        Mỗi ngày trong khoảng được điền Đủ 4 cột (ngày + kíp A, B, C): kíp nghỉ
        hoặc ngày không có dữ liệu = 0. Khoảng trải nhiều tháng thì điền vào
        từng sheet 'THANG MM-YYYY' tương ứng (không có sheet thì bỏ qua và
        cảnh báo)
        """
        days, start, end = grafana_time.resolve_days(
            from_time, to_time, now=now, week_start=week_start
        )
        print(
            f"Khoảng thời gian: {days[0]:%d/%m/%Y} -> {days[-1]:%d/%m/%Y} "
            f"({len(days)} ngày)"
        )

        q_start = datetime.combine(
            days[0] - timedelta(days=self.phase_loopback_days),
            datetime.min.time(),
            grafana_time.TZ,
        ).strftime("%Y-%m-%d")
        q_end = datetime.combine(
            days[-1], datetime.max.time(), grafana_time.TZ
        ).strftime("%Y-%m-%d")
        finished_production = self.get_finished_production(q_start, q_end)
        if phase is None:
            phase = (
                self.detect_phase(finished_production)
                if finished_production
                else 0
            )
        cols = self.build_columns(days, finished_production, phase, merge_spill)

        wb = openpyxl.load_workbook(self.report_temp)

        sheet_name = "THANG 10-2026"
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.activate

        # data = [[110.5], [110.5], [110.5]]
        # excel.write(ws, data, "D17")
        i = 0
        for (y, m), grp in groupby(days, key=lambda d: (d.year, d.month)):
            g_days = list(grp)
            n = len(g_days)

            row0 = self.first_row + g_days[0].day - 1

            if write_dates:
                excel.write(
                    ws,
                    [[datetime(d.year, d.month, d.day)] for d in g_days],
                    f"{self.date_col}{row0}",
                )
            for crew, col in self.finished_production_cols.items():
                excel.write(
                    ws, [[v] for v in cols[crew][i : i + n]], f"{col}{row0}"
                )
            print(f"Đã điền {n} ngày vào sheet '{ws.title}' từ hàng {row0}")
            i += n

        output_path = "./data/BAO_CAO.xlsx"
        wb.save(output_path)

        print(f"Đã cập nhật và lưu file thành công tại: {output_path}")

    def get_finished_production(self, from_date: str, to_date: str):
        query = f"""
            SELECT sum("weight") / 1000
            FROM "cut_roll_production"
            WHERE time >= '{from_date}T07:00:00+07:00' - 1d
                AND time <= '{to_date}T07:00:00+07:00'
            GROUP BY time(1d,-7h), "crew"::tag fill(none)
            ORDER BY time ASC
        """
        raw = self.realtime_repo.query(query)

        resp = raw["results"][0].get("series", [{}])
        prod: dict[date, Any] = {}
        for res in resp:
            crew = res["tags"]["crew"]
            for time, value in res["values"]:
                if value is None:
                    continue
                dt_utc = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
                dt_vn = dt_utc + timedelta(hours=7)
                d = dt_vn.date()
                prod.setdefault(d, {})[crew] = value

        return prod

    def get_roll_production(self, from_date: str, to_date: str):
        query = f"""
        SELECT SUM("hourly_production") AS "production"
        FROM (
            SELECT integral("ton_per_min", 1m) AS "hourly_production"
            FROM (
                SELECT
                    (
                        last("speed_machine") *
                        4.6 *
                        mean("basic_weight") *
                        0.97
                    ) / 1000000 AS "ton_per_min"
                FROM "dongtien_realtime"
                WHERE
                    "machine" = 'PM6'
                    AND time >= '{from_date}T07:00:00+07:00'
                    AND time <= '{to_date}T07:00:00+07:00'
                GROUP BY time(1m)
                fill(none)
            )
            GROUP BY time(1h)
            fill(0)
        )
        WHERE time >= '{from_date}T07:00:00+07:00'
            AND time <= '{to_date}T07:00:00+07:00'
        GROUP BY time(12h)
        fill(none)
        """
        raw = self.realtime_repo.query(query)
        return raw["results"][0].get("series", [{}])

    def on_duty(self, d, phase):
        """Cặp kíp theo chu kỳ xoay tua của ngày d."""
        return self.cycle[(d.toordinal() + phase) % len(self.cycle)]

    def detect_phase(self, prod):
        """Chọn pha khớp nhất: cộng tấn kíp đúng ca, trừ tấn kíp lẽ ra nghỉ."""

        def score(phase):
            s = 0.0
            for d, crews in prod.items():
                duty = self.on_duty(d, phase)
                for c, t in crews.items():
                    s += t if c in duty else -t
            return s

        return max(range(len(self.cycle)), key=score)

    def merge_spill(self, prod, phase):
        """Cuộn cắt lệch kíp: cộng tấn lẻ của kíp nghỉ
        vào ca gần nhất trước đó của chính kíp đó."""
        new = {d: dict(c) for d, c in prod.items()}
        log = []
        for d in sorted(prod):
            duty = self.on_duty(d, phase)
            for crew, t in prod[d].items():
                if crew in duty or t is None or not (0 < t < self.min_ton):
                    continue
                tgt = d - timedelta(days=1)
                while crew not in self.on_duty(tgt, phase):
                    tgt -= timedelta(days=1)
                new[d].pop(crew)
                new.setdefault(tgt, {})[crew] = (
                    new.get(tgt, {}).get(crew, 0.0) + t
                )
                log.append(
                    f" [+] {d} kíp {crew}: {t} tấn"
                    f" -> cộng vào {tgt} (kíp {crew})"
                )
        return new, log

    def build_columns(
        self,
        days: List[date],
        tons: Dict[date, Dict[str, float]],
        phase: int,
        merge_spill: bool = False,
    ) -> Dict[str, List[float]]:
        """
            days : các ngày cần điền (đã sắp xếp)
        tons : {ngày: {kíp: tấn}} (có thể rộng hơn `days`, dùng cho merge_spill)
            ->  {"A": [...], "B": [...], "C": [...]}, mỗi list dài len(days).
            Quy tắc: kíp đúng ca có dữ liệu -> số tấn;
                kíp nghỉ / thiếu dữ liệu / ngày không có dữ liệu -> 0
            (không bao giờ None để công thức Excel không lỗi).
        """
        if merge_spill:
            tons, log = self.merge_spill(tons, phase)
            for line in log:
                print(line)
        cols: Dict[str, List[Any]] = {c: [] for c in "ABC"}
        for d in days:
            duty = self.on_duty(d, phase)
            for c in "ABC":
                v = tons.get(d, {}).get(c) if c in duty else None
                cols[c].append(round(v, self.ndigits) if v else 0)
        return cols
