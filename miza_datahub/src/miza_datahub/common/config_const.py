from datetime import timezone, timedelta

EXCEL = "Excel"
DATA_PATH = "data_path"

TELEGRAM = "Telegram"
TOKEN = "token"
URL_GET_FILE_PATH = "https://api.telegram.org/bot{token}/getFile"
URL_GET_FILE_CONTENT = "https://api.telegram.org/file/bot{token}/{file_path}"

INFLUX = "Influx"
INFLUX_HOST = "host"
INFLUX_PORT = "port"
INFLUX_DB = "db"

POSTGRES = "Postgres"
POSTGRES_HOST = "host"
POSTGRES_PORT = "port"
POSTGRES_DB = "db"
POSTGRES_USERNAME = "username"
POSTGRES_PASSWORD = "password"

VN_TZ = timezone(timedelta(hours=7))

DEFAULT_CONFIG_FILE_NAME = "./config/miza_datahub_config.props"
