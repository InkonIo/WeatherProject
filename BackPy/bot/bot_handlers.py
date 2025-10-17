import telebot
from BackPy.config.settings import settings
from BackPy.app.services.user_service import UserService
from BackPy.app.services.weather_service import WeatherService
from BackPy.app.models.user import User
from functools import wraps

bot = None

def init_bot(app_instance):
    global bot
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не найден! Проверьте файл .env")

    bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)

    # --- Декоратор для контекста Flask ---
    def with_app_context(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with app_instance.app_context():
                return func(*args, **kwargs)
        return wrapper

    # Применяем декоратор ко всем хендлерам
    bot.message_handler(commands=["start"])(with_app_context(start_handler))
    bot.message_handler(commands=["login"])(with_app_context(login_handler))
    bot.message_handler(commands=["city"])(with_app_context(city_handler))
    bot.message_handler(commands=["weather"])(with_app_context(weather_handler))
    bot.message_handler(commands=["forecast"])(with_app_context(forecast_handler))
    bot.message_handler(func=lambda message: True)(with_app_context(echo_all))

    return bot

# --- Основные обработчики ---
def get_main_keyboard():
    from telebot import types
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("/weather", "/forecast")
    markup.row("/city", "/login")
    return markup

def start_handler(message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    user = UserService.create_or_update_user(telegram_id, username, first_name)
    welcome_message = (
        f"👋 Добро пожаловать, {first_name or username or 'Пользователь'}!\n\n"
        f"Я бот MeteoSphere. Я могу показать вам актуальную погоду и прогноз.\n"
        f"Ваш Telegram ID: <b>{telegram_id}</b>\n\n"
        f"Для входа на наш веб-сайт используйте команду /login."
    )
    bot.send_message(message.chat.id, welcome_message, reply_markup=get_main_keyboard(), parse_mode='HTML')

def login_handler(message):
    telegram_id = message.from_user.id
    code = UserService.generate_auth_code_for_user(telegram_id)
    if code:
        login_message = (
            f"🔑 <b>Ваш 6-значный код для входа на сайт:</b>\n<code>{code}</code>\n"
            "Действителен 5 минут."
        )
        bot.send_message(message.chat.id, login_message, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: не удалось найти аккаунт. Попробуйте /start.")

def city_handler(message):
    bot.send_message(message.chat.id, "📍 Введите название города:")
    bot.register_next_step_handler(message, set_city_step)

def set_city_step(message):
    city = message.text.strip()
    telegram_id = message.from_user.id
    weather = WeatherService.get_current_weather(city)
    if weather:
        user = UserService.get_user_by_telegram_id(telegram_id)
        if user:
            UserService.update_user_city(user.id, weather['city'])
            bot.send_message(message.chat.id, f"✅ Город установлен: <b>{weather['city']}</b>.", parse_mode='HTML', reply_markup=get_main_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Попробуйте /start.")
    else:
        bot.send_message(message.chat.id, f"❌ Город <b>{city}</b> не найден.", parse_mode='HTML')
        bot.register_next_step_handler(message, set_city_step)

def weather_handler(message):
    telegram_id = message.from_user.id
    user = UserService.get_user_by_telegram_id(telegram_id)
    if not user or not user.city:
        bot.send_message(message.chat.id, "❌ Сначала установите город командой /city.")
        return
    full_data = WeatherService.get_full_weather_data(user.city)
    if full_data and full_data.get('weather'):
        weather = full_data['weather']
        msg = (
            f"🌍 <b>{weather['city']}</b>\n"
            f"🌡 Температура: <b>{weather['temp']}°C</b>\n"
            f"🤔 Ощущается как: {weather['feels_like']}°C\n"
            f"📝 {weather['description'].capitalize()}\n"
            f"💧 Влажность: {weather['humidity']}%\n"
            f"🌪 Ветер: {weather['wind']} м/с\n"
            f"📊 Давление: {weather['pressure']} мм рт.ст.\n"
            f"🌅 Рассвет: {weather['sunrise']}\n"
            f"🌇 Закат: {weather['sunset']}\n"
        )
        bot.send_message(message.chat.id, msg, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "❌ Не удалось получить данные о погоде.")

def forecast_handler(message):
    telegram_id = message.from_user.id
    user = UserService.get_user_by_telegram_id(telegram_id)
    if not user or not user.city:
        bot.send_message(message.chat.id, "❌ Сначала установите город командой /city.")
        return
    full_data = WeatherService.get_full_weather_data(user.city)
    if full_data and full_data.get('forecast'):
        forecast = full_data['forecast']
        msg = f"📅 <b>Прогноз на 3 дня для {user.city}:</b>\n"
        for day in forecast:
            msg += f"  • {day['date']}: {day['temp']}°C, {day['description']}\n"
        bot.send_message(message.chat.id, msg, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "❌ Не удалось получить прогноз.")

def echo_all(message):
    bot.send_message(message.chat.id,
                     "Неизвестная команда. Используйте /start, /login, /city, /weather, /forecast",
                     reply_markup=get_main_keyboard())
