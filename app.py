from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

# Ваш API ключ от OpenWeatherMap
API_KEY = "d25be7881e448482385df1a9ee215eac"


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
        # Берем прогноз на каждый день (каждые 24 часа = 8 записей по 3 часа)
        for i in range(0, min(24, len(data["list"])), 8):
            item = data["list"][i]
            date_obj = datetime.fromtimestamp(item["dt"])

            forecast.append(
                {
                    "date": date_obj.strftime("%d.%m"),
                    "temp": round(item["main"]["temp"], 1),
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                }
            )

        return forecast[:3]  # Возвращаем только 3 дня

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


@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    forecast = []
    advice = None

    # Определяем город для поиска
    if request.method == "POST":
        city = request.form.get("city", "").strip()
    else:
        city = "Алматы"  # Город по умолчанию

    if city:
        # Получаем данные о погоде
        weather = get_weather(city)

        if weather:
            # Получаем прогноз
            forecast = get_forecast(city)
            # Генерируем совет
            advice = get_weather_advice(weather)

    return render_template("index.html", weather=weather, forecast=forecast, advice=advice)


@app.errorhandler(404)
def not_found_error(error):
    return render_template("index.html", weather=None, forecast=[], advice=None), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("index.html", weather=None, forecast=[], advice=None), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
