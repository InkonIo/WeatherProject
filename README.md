# 🌦️ WeatherProject

Интеллектуальный погодный сервис с интеграцией Flask API, Telegram-бота и React-фронтенда. Проект сочетает в себе удобный веб-интерфейс и возможность получать погоду прямо в Telegram.

## 📁 Архитектура проекта

```
WeatherProject/
│
├── .env                  # Конфигурация: токены, API ключи, JWT и т.п.
├── BackPy/               # Backend на Flask + Telegram Bot
│   ├── main_runner.py    # Главный запускатель Flask API и Telegram-бота
│   ├── requirements.txt  # Зависимости Python
│   ├── app/
│   │   ├── api/          # HTTP-контроллеры (Blueprint'ы)
│   │   │   ├── auth.py   # Авторизация и Telegram-коды
│   │   │   └── weather.py# Работа с погодой
│   │   ├── services/     # Бизнес-логика
│   │   ├── models/       # SQLAlchemy-модели
│   │   └── db/           # Подключение к БД
│   ├── bot/              # Telegram Bot
│   │   └── bot_handlers.py
│   ├── controller/       # Эндпоинты для сайта (например /main)
│   ├── core/             # JWT и middleware
│   └── config/           # Настройки и загрузка .env
│
└── FrontReact/           # Фронтенд (React + TypeScript)
    ├── src/
    ├── package.json
    └── README.md
```

## 🚀 Как запустить проект

### 1️⃣ Клонировать репозиторий

```bash
git clone https://github.com/InkonIo/WeatherProject.git
cd WeatherProject
```

### 2️⃣ Создать и активировать виртуальное окружение

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Установить зависимости

```bash
pip install -r BackPy/requirements.txt
```

### 4️⃣ Создать файл `.env` в корне проекта

Пример:

```env
FLASK_ENV=development
FLASK_APP=BackPy/main_runner.py

# API ключи
OPENWEATHERMAP_API_KEY=ваш_ключ
TELEGRAM_BOT_TOKEN=ваш_тг_бот_токен

# JWT
JWT_SECRET_KEY=секретный_ключ
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=30

# База данных
DATABASE_URL=sqlite:///./sql_app.db
```

### 5️⃣ Запустить сервер

```bash
python -m BackPy.main_runner
```

После запуска:
- 🌍 **Главная страница** — http://localhost:8080/
- 📘 **Swagger API Docs** — http://localhost:8080/api/docs

## 💬 Telegram Bot

Бот автоматически запускается вместе с Flask API. При первом запуске бот:

1. Принимает команду `/start`
2. Отправляет вам 6-значный код
3. Вы используете этот код в `/api/auth/telegram_code` для получения JWT токена

## 🧠 Работа с Git

Чтобы внести изменения:

```bash
git add .
git commit -m "описание изменений"
git push origin <имя_ветки>
```

- `master` — основная ветка
- Можно создать свою ветку:

```bash
git checkout -b feature/my-feature
```

## 🛠️ Требования для корректного запуска

- Python 3.10+
- Flask, Flask-SQLAlchemy, python-dotenv, pyTelegramBotAPI — всё есть в `requirements.txt`
- Правильно создан `.env` в корне проекта
- Порты 8080 и 5000 не заняты другими процессами
- Если используешь Telegram-бота, убедись, что токен актуален и Webhook не установлен (бот работает через polling)

## ✨ Пример структуры работы

- Пользователь пишет боту → бот создаёт код и сохраняет его
- Пользователь вводит код на сайте → получает JWT
- Сайт обращается к API (`/api/weather`) → получает прогноз
