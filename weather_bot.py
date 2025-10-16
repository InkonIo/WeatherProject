import telebot
from telebot import types
import requests
from datetime import datetime
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler


BOT_TOKEN = "8431178178:AAGxroXfl2zRFAFOajRv66CJoWGa8vf6mRk"
API_KEY = "d25be7881e448482385df1a9ee215eac"

bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения данных пользователей
USERS_FILE = "users_data.json"


# === ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ===

def load_users():
    """Загрузка данных пользователей"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users(users):
    """Сохранение данных пользователей"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_user_city(user_id):
    """Получить город пользователя"""
    users = load_users()
    return users.get(str(user_id), {}).get('city')


def save_user_city(user_id, city, username=None):
    """Сохранить город пользователя"""
    users = load_users()
    users[str(user_id)] = {
        'city': city,
        'username': username,
        'registered_at': datetime.now().isoformat()
    }
    save_users(users)


# === ФУНКЦИИ ПОГОДЫ (из твоего Flask приложения) ===

def get_weather(city):
    """Получение текущей погоды для города"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("cod") != 200:
            return None

        return {
            "city": data["name"],
            "temp": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind": round(data["wind"]["speed"], 1),
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M"),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M"),
        }
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return None


def get_forecast(city):
    """Получение прогноза на 3 дня"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric&lang=ru"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("cod") != "200":
            return []

        forecast = []
        for i in range(0, min(24, len(data["list"])), 8):
            item = data["list"][i]
            date_obj = datetime.fromtimestamp(item["dt"])

            forecast.append({
                "date": date_obj.strftime("%d.%m"),
                "temp": round(item["main"]["temp"], 1),
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
            })

        return forecast[:3]
    except Exception as e:
        print(f"Ошибка получения прогноза: {e}")
        return []


def get_weather_advice(weather):
    """Генерация совета на основе погоды (твоя функция)"""
    if not weather:
        return None

    temp = weather["temp"]
    description = weather["description"].lower()

    if "дождь" in description or "ливень" in description:
        return "☂️ Не забудьте взять зонт!"
    elif "снег" in description or "метель" in description:
        return "❄️ Осторожно, на дороге может быть скользко!"
    elif temp > 30:
        return "🌡️ Очень жарко! Пейте больше воды и избегайте прямых солнечных лучей"
    elif temp > 25:
        return "☀️ Отличная погода для прогулки! Не забудьте солнцезащитный крем"
    elif temp < -10:
        return "🧥 Очень холодно! Одевайтесь максимально тепло"
    elif temp < 5:
        return "❄️ Прохладно, одевайтесь теплее!"
    elif "туман" in description:
        return "🌫️ Туман! Будьте осторожны на дорогах"
    elif "ветер" in description or weather["wind"] > 10:
        return "💨 Сильный ветер! Держите зонт крепче"
    elif "ясно" in description and 15 <= temp <= 25:
        return "✨ Прекрасная погода для прогулки!"

    return None


# === ФОРМАТИРОВАНИЕ СООБЩЕНИЙ ===

def format_weather_message(weather, forecast=None):
    """Форматирование сообщения с погодой"""
    if not weather:
        return "❌ Не удалось получить данные о погоде"

    message = f"🌍 <b>{weather['city']}</b>\n\n"
    message += f"🌡 Температура: <b>{weather['temp']}°C</b>\n"
    message += f"🤔 Ощущается как: {weather['feels_like']}°C\n"
    message += f"📝 {weather['description'].capitalize()}\n\n"
    message += f"💧 Влажность: {weather['humidity']}%\n"
    message += f"🌪 Ветер: {weather['wind']} м/с\n"
    message += f"📊 Давление: {weather['pressure']} мм рт.ст.\n\n"
    message += f"🌅 Рассвет: {weather['sunrise']}\n"
    message += f"🌇 Закат: {weather['sunset']}\n"

    # Добавляем совет
    advice = get_weather_advice(weather)
    if advice:
        message += f"\n💡 <b>Совет:</b> {advice}\n"

    # Добавляем прогноз
    if forecast:
        message += "\n📅 <b>Прогноз на 3 дня:</b>\n"
        for day in forecast:
            message += f"  • {day['date']}: {day['temp']}°C, {day['description']}\n"

    return message


# === КОМАНДЫ БОТА ===

@bot.message_handler(commands=['start'])
def start(message):
    """Команда /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    city = get_user_city(user_id)

    if city:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🌤 Погода сейчас", "📅 Прогноз")
        markup.row("⚙️ Сменить город", "ℹ️ Помощь")

        bot.send_message(
            message.chat.id,
            f"👋 С возвращением!\n\n"
            f"Ваш город: <b>{city}</b>\n\n"
            f"Выберите действие:",
            reply_markup=markup,
            parse_mode='HTML'
        )
    else:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать в Weather Bot!\n\n"
            "📍 Для начала работы укажите ваш город:",
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, register_city)


def register_city(message):
    """Регистрация города пользователя"""
    city = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем существование города
    weather = get_weather(city)

    if weather:
        save_user_city(user_id, weather['city'], username)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🌤 Погода сейчас", "📅 Прогноз")
        markup.row("⚙️ Сменить город", "ℹ️ Помощь")

        bot.send_message(
            message.chat.id,
            f"✅ Отлично! Ваш город <b>{weather['city']}</b> сохранен!\n\n"
            f"Теперь вы будете получать уведомления о погоде.\n\n"
            f"Выберите действие:",
            reply_markup=markup,
            parse_mode='HTML'
        )

        # Сразу показываем погоду
        show_weather(message)
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Город <b>{city}</b> не найден.\n\n"
            f"Попробуйте ещё раз:",
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, register_city)


@bot.message_handler(commands=['weather'])
def weather_command(message):
    """Команда /weather"""
    show_weather(message)


@bot.message_handler(commands=['forecast'])
def forecast_command(message):
    """Команда /forecast"""
    show_forecast(message)


@bot.message_handler(commands=['city'])
def change_city_command(message):
    """Команда /city"""
    change_city(message)


@bot.message_handler(commands=['help'])
def help_command(message):
    """Команда /help"""
    help_text = """
📖 <b>Доступные команды:</b>

/start - Начать работу с ботом
/weather - Текущая погода
/forecast - Прогноз на 3 дня
/city - Сменить город
/help - Показать эту справку

🔔 <b>Уведомления:</b>
Бот автоматически присылает прогноз погоды каждое утро в 8:00

💡 <b>Советы:</b>
Бот дает полезные советы в зависимости от погоды!
    """
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')


# === ОБРАБОТЧИКИ КНОПОК ===

@bot.message_handler(func=lambda message: message.text == "🌤 Погода сейчас")
def show_weather(message):
    """Показать текущую погоду"""
    user_id = message.from_user.id
    city = get_user_city(user_id)

    if not city:
        bot.send_message(
            message.chat.id,
            "❌ Сначала укажите ваш город с помощью команды /start"
        )
        return

    weather = get_weather(city)
    forecast = get_forecast(city)

    bot.send_message(
        message.chat.id,
        format_weather_message(weather, forecast),
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda message: message.text == "📅 Прогноз")
def show_forecast(message):
    """Показать прогноз"""
    user_id = message.from_user.id
    city = get_user_city(user_id)

    if not city:
        bot.send_message(
            message.chat.id,
            "❌ Сначала укажите ваш город с помощью команды /start"
        )
        return

    weather = get_weather(city)
    forecast = get_forecast(city)

    if forecast:
        message_text = f"📅 <b>Прогноз на 3 дня для {city}:</b>\n\n"
        for day in forecast:
            message_text += f"📆 {day['date']}\n"
            message_text += f"   🌡 {day['temp']}°C\n"
            message_text += f"   📝 {day['description'].capitalize()}\n\n"
    else:
        message_text = "❌ Не удалось получить прогноз"

    bot.send_message(message.chat.id, message_text, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text == "⚙️ Сменить город")
def change_city(message):
    """Сменить город"""
    markup = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        "📍 Введите название нового города:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, register_city)


@bot.message_handler(func=lambda message: message.text == "ℹ️ Помощь")
def help_button(message):
    """Кнопка помощи"""
    help_command(message)




def send_morning_weather():
    """Отправка утренних уведомлений всем пользователям"""
    users = load_users()

    for user_id, user_data in users.items():
        try:
            city = user_data.get('city')
            if not city:
                continue

            weather = get_weather(city)
            forecast = get_forecast(city)

            if weather:
                message = "🌅 <b>Доброе утро!</b>\n\n"
                message += format_weather_message(weather, forecast)

                bot.send_message(
                    int(user_id),
                    message,
                    parse_mode='HTML'
                )
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user_id}: {e}")



def start_scheduler():
    """Запуск планировщика задач"""
    scheduler = BackgroundScheduler()

    # Отправка уведомлений каждое утро в 8:00
    scheduler.add_job(
        send_morning_weather,
        'cron',
        hour=8,
        minute=0
    )

    scheduler.start()
    print("✅ Планировщик запущен")



if __name__ == '__main__':
    print("🤖 Бот запущен...")
    start_scheduler()

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Ошибка: {e}")