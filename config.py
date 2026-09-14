
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError(
        "Не задан TELEGRAM_BOT_TOKEN. Создайте файл .env на основе "
        ".env.example и укажите там реальный токен бота."
    )

SERVER = os.environ.get("DB_SERVER")
DATABASE = os.environ.get("DB_NAME")

if not SERVER or not DATABASE:
    raise RuntimeError(
        "Не заданы DB_SERVER и/или DB_NAME. Проверьте файл .env."
    )

CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"
)

_admin_ids_raw = os.environ.get("ADMIN_USER_IDS", "")
ADMIN_USER_IDS = {
    int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip().isdigit()
}
