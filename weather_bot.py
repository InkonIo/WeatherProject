import telebot
from telebot import types
import requests
from datetime import datetime, timedelta
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = "8431178178:AAFtsjoVuXFPVeBU7G0pDViYRCf2et8vaZY"
API_KEY = "d25be7881e448482385df1a9ee215eac"
bot = telebot.TeleBot(BOT_TOKEN)

# Файлы для хранения данных
USERS_FILE = "users_data.json"

# Настройки подписки
SUBSCRIPTION_PRICE = 10  # Цена в Telegram Stars
SUBSCRIPTION_DAYS = 30  # Длительность подписки в днях

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

def get_user_data(user_id):
    """Получить данные пользователя"""
    users = load_users()
    return users.get(str(user_id), {})

def get_user_city(user_id):
    """Получить город пользователя"""
    user_data = get_user_data(user_id)
    return user_data.get('city')

def save_user_city(user_id, city, username=None):
    """Сохранить город пользователя"""
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]['city'] = city
        users[str(user_id)]['username'] = username
    else:
        users[str(user_id)] = {
            'city': city,
            'username': username,
            'registered_at': datetime.now().isoformat(),
            'subscription_end': None,
            'is_premium': False
        }
    save_users(users)

def check_subscription(user_id):
    """Проверить статус подписки пользователя"""
    user_data = get_user_data(user_id)
    
    # Если подписка не активирована
    if not user_data.get('subscription_end'):
        return False
    
    # Проверяем срок действия подписки
    subscription_end = datetime.fromisoformat(user_data['subscription_end'])
    if datetime.now() < subscription_end:
        return True
    
    # Подписка истекла
    users = load_users()
    users[str(user_id)]['is_premium'] = False
    save_users(users)
    return False

def activate_subscription(user_id):
    """Активировать подписку для пользователя"""
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            'city': None,
            'username': None,
            'registered_at': datetime.now().isoformat()
        }
    
    # Устанавливаем дату окончания подписки
    subscription_end = datetime.now() + timedelta(days=SUBSCRIPTION_DAYS)
    users[user_id_str]['subscription_end'] = subscription_end.isoformat()
    users[user_id_str]['is_premium'] = True
    users[user_id_str]['last_payment'] = datetime.now().isoformat()
    
    save_users(users)
    return subscription_end

def get_subscription_days_left(user_id):
    """Получить количество оставшихся дней подписки"""
    user_data = get_user_data(user_id)
    if not user_data.get('subscription_end'):
        return 0
    
    subscription_end = datetime.fromisoformat(user_data['subscription_end'])
    days_left = (subscription_end - datetime.now()).days
    return max(0, days_left)

# === ФУНКЦИИ ПОГОДЫ ===
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
    """Генерация совета на основе погоды"""
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

def get_main_keyboard(user_id):
    """Получить главную клавиатуру с учетом статуса подписки"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if check_subscription(user_id):
        markup.row("🌤 Погода сейчас", "📅 Прогноз")
        markup.row("⚙️ Сменить город", "👤 Профиль")
        markup.row("ℹ️ Помощь")
    else:
        markup.row("⭐ Оформить подписку")
        markup.row("ℹ️ Помощь")
    
    return markup

# === КОМАНДЫ БОТА ===
@bot.message_handler(commands=['start'])
def start(message):
    """Команда /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    city = get_user_city(user_id)
    
    # Инициализируем пользователя, если его нет
    if not get_user_data(user_id):
        save_user_city(user_id, None, username)
    
    has_subscription = check_subscription(user_id)
    
    if has_subscription and city:
        days_left = get_subscription_days_left(user_id)
        markup = get_main_keyboard(user_id)
        bot.send_message(
            message.chat.id,
            f"👋 С возвращением!\n\n"
            f"📍 Ваш город: <b>{city}</b>\n"
            f"⭐ Подписка активна: <b>{days_left} дн.</b>\n\n"
            f"Выберите действие:",
            reply_markup=markup,
            parse_mode='HTML'
        )
    elif has_subscription and not city:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(
            message.chat.id,
            "📍 Для начала укажите ваш город:",
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, register_city)
    else:
        markup = get_main_keyboard(user_id)
        bot.send_message(
            message.chat.id,
            f"👋 Добро пожаловать в Weather Bot!\n\n"
            f"🌟 Этот бот показывает актуальную погоду и прогнозы\n"
            f"📬 Ежедневные утренние уведомления\n"
            f"💡 Персональные советы на основе погоды\n\n"
            f"💳 Стоимость подписки: <b>{SUBSCRIPTION_PRICE} ⭐ Telegram Stars</b>\n"
            f"⏱ Длительность: <b>{SUBSCRIPTION_DAYS} дней</b>\n\n"
            f"Нажмите кнопку ниже для оформления подписки:",
            reply_markup=markup,
            parse_mode='HTML'
        )

def register_city(message):
    """Регистрация города пользователя"""
    city = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Проверяем существование города
    weather = get_weather(city)
    if weather:
        save_user_city(user_id, weather['city'], username)
        markup = get_main_keyboard(user_id)
        bot.send_message(
            message.chat.id,
            f"✅ Отлично! Ваш город <b>{weather['city']}</b> сохранен!\n\n"
            f"Выберите действие:",
            reply_markup=markup,
            parse_mode='HTML'
        )
        # Сразу показываем погоду, если есть подписка
        if check_subscription(user_id):
            show_weather(message)
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Город <b>{city}</b> не найден.\n\n"
            f"Попробуйте ещё раз:",
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, register_city)

@bot.message_handler(commands=['subscribe', 'subscription'])
def subscribe_command(message):
    """Команда подписки"""
    show_subscription_offer(message)

@bot.message_handler(commands=['profile'])
def profile_command(message):
    """Команда профиля"""
    show_profile(message)

@bot.message_handler(commands=['weather'])
def weather_command(message):
    """Команда /weather"""
    if not check_subscription(message.from_user.id):
        show_subscription_offer(message)
        return
    show_weather(message)

@bot.message_handler(commands=['forecast'])
def forecast_command(message):
    """Команда /forecast"""
    if not check_subscription(message.from_user.id):
        show_subscription_offer(message)
        return
    show_forecast(message)

@bot.message_handler(commands=['city'])
def change_city_command(message):
    """Команда /city"""
    if not check_subscription(message.from_user.id):
        show_subscription_offer(message)
        return
    change_city(message)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Команда /help"""
    help_text = """
📖 <b>Доступные команды:</b>

/start - Начать работу с ботом
/subscribe - Оформить подписку
/profile - Посмотреть профиль
/weather - Текущая погода
/forecast - Прогноз на 3 дня
/city - Сменить город
/help - Показать эту справку

🔔 <b>Уведомления:</b>
Бот автоматически присылает прогноз погоды каждое утро в 8:00

💡 <b>Советы:</b>
Бот дает полезные советы в зависимости от погоды!

⭐ <b>Подписка:</b>
Стоимость: {price} Telegram Stars
Длительность: {days} дней
    """.format(price=SUBSCRIPTION_PRICE, days=SUBSCRIPTION_DAYS)
    
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# === ОБРАБОТЧИКИ КНОПОК ===
@bot.message_handler(func=lambda message: message.text == "⭐ Оформить подписку")
def show_subscription_offer(message):
    """Показать предложение о подписке"""
    user_id = message.from_user.id
    
    # Создаем инвойс для оплаты через Telegram Stars
    prices = [types.LabeledPrice(label="Подписка на Weather Bot", amount=SUBSCRIPTION_PRICE)]
    
    bot.send_invoice(
        chat_id=message.chat.id,
        title="Подписка на Weather Bot",
        description=f"Доступ ко всем функциям бота на {SUBSCRIPTION_DAYS} дней:\n"
                   f"• Актуальная погода\n"
                   f"• Прогноз на 3 дня\n"
                   f"• Ежедневные уведомления\n"
                   f"• Персональные советы",
        invoice_payload=f"subscription_{user_id}",
        provider_token="",  # Пустой для Telegram Stars
        currency="XTR",  # Валюта Telegram Stars
        prices=prices,
        start_parameter="subscribe"
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout(pre_checkout_query):
    """Обработка предварительной проверки платежа"""
    bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True
    )

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    """Обработка успешного платежа"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Активируем подписку
    subscription_end = activate_subscription(user_id)
    
    # Если город не указан, просим его указать
    city = get_user_city(user_id)
    if not city:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(
            message.chat.id,
            f"✅ Спасибо за подписку!\n\n"
            f"⭐ Ваша подписка активна до: <b>{subscription_end.strftime('%d.%m.%Y')}</b>\n\n"
            f"📍 Теперь укажите ваш город для получения прогноза погоды:",
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, register_city)
    else:
        markup = get_main_keyboard(user_id)
        bot.send_message(
            message.chat.id,
            f"✅ Спасибо за подписку!\n\n"
            f"⭐ Ваша подписка активна до: <b>{subscription_end.strftime('%d.%m.%Y')}</b>\n\n"
            f"Теперь вам доступны все функции бота!",
            reply_markup=markup,
            parse_mode='HTML'
        )

@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def show_profile(message):
    """Показать профиль пользователя"""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.send_message(message.chat.id, "❌ Данные не найдены")
        return
    
    city = user_data.get('city', 'Не указан')
    
    if check_subscription(user_id):
        days_left = get_subscription_days_left(user_id)
        subscription_end = datetime.fromisoformat(user_data['subscription_end'])
        status = f"✅ Активна до {subscription_end.strftime('%d.%m.%Y')}\n📅 Осталось дней: <b>{days_left}</b>"
    else:
        status = "❌ Не активна"
    
    profile_text = f"""
👤 <b>Ваш профиль</b>

📍 Город: <b>{city}</b>
⭐ Статус подписки: {status}

💡 Для продления подписки используйте команду /subscribe
    """
    
    bot.send_message(message.chat.id, profile_text, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "🌤 Погода сейчас")
def show_weather(message):
    """Показать текущую погоду"""
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        show_subscription_offer(message)
        return
    
    city = get_user_city(user_id)
    if not city:
        bot.send_message(
            message.chat.id,
            "❌ Сначала укажите ваш город с помощью команды /city"
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
    
    if not check_subscription(user_id):
        show_subscription_offer(message)
        return
    
    city = get_user_city(user_id)
    if not city:
        bot.send_message(
            message.chat.id,
            "❌ Сначала укажите ваш город с помощью команды /city"
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
    if not check_subscription(message.from_user.id):
        show_subscription_offer(message)
        return
    
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

# === ПЛАНИРОВЩИК ===
def send_morning_weather():
    """Отправка утренних уведомлений всем пользователям с активной подпиской"""
    users = load_users()
    for user_id, user_data in users.items():
        try:
            # Проверяем подписку
            if not check_subscription(int(user_id)):
                continue
            
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