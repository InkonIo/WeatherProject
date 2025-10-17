import os
from dotenv import load_dotenv

# Берём корень проекта (где лежит папка BackPy)
BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..", "..")))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")

# Проверка, что .env существует
if not os.path.exists(DOTENV_PATH):
    raise RuntimeError(f".env файл не найден по пути {DOTENV_PATH}")

print("DEBUG: loading .env from", DOTENV_PATH)
load_dotenv(DOTENV_PATH)

class Settings:
    PROJECT_NAME: str = "MeteoSphere Backend"
    VERSION: str = "1.0.0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")
    OPENWEATHERMAP_API_KEY: str = os.getenv("OPENWEATHERMAP_API_KEY")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_jwt_secret_key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXP_MINUTES: int = int(os.getenv("JWT_EXP_MINUTES", 30))

settings = Settings()

print("DEBUG: settings loaded")
print("DEBUG TELEGRAM_BOT_TOKEN:", settings.TELEGRAM_BOT_TOKEN)

if not settings.TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден! Проверьте файл .env")
