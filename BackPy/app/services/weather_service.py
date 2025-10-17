import requests
from datetime import datetime
from BackPy.config.settings import settings

class WeatherService:
    BASE_URL = "http://api.openweathermap.org/data/2.5"
    API_KEY = settings.OPENWEATHERMAP_API_KEY

    @staticmethod
    def _make_request(endpoint, params):
        """Внутренняя функция для выполнения запросов к OpenWeatherMap"""
        params['appid'] = WeatherService.API_KEY
        params['units'] = 'metric'
        params['lang'] = 'ru'
        url = f"{WeatherService.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса к OpenWeatherMap: {e}")
            return None

    @staticmethod
    def get_current_weather(city: str):
        """Получение текущей погоды для города"""
        data = WeatherService._make_request("weather", {"q": city})
        if not data or data.get("cod") != 200:
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
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
        }

    @staticmethod
    def get_forecast(city: str):
        """Получение прогноза на 3 дня"""
        data = WeatherService._make_request("forecast", {"q": city})
        if not data or data.get("cod") != "200":
            return []
        
        forecast = []
        # Выбираем прогноз на 12:00 каждого из следующих 3 дней
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

    @staticmethod
    def get_air_pollution(lat: float, lon: float):
        """Получение данных о качестве воздуха"""
        data = WeatherService._make_request("air_pollution", {"lat": lat, "lon": lon})
        if not data or not data.get("list"):
            return None
        
        # Берем текущие данные
        current = data["list"][0]
        return {
            "aqi": current["main"]["aqi"],
            "co": current["components"]["co"],
            "no": current["components"]["no"],
            "no2": current["components"]["no2"],
            "o3": current["components"]["o3"],
            "so2": current["components"]["so2"],
            "pm2_5": current["components"]["pm2_5"],
            "pm10": current["components"]["pm10"],
            "nh3": current["components"]["nh3"],
        }

    @staticmethod
    def get_uv_index(lat: float, lon: float):
        """Получение данных об УФ-индексе (используем One Call API для простоты)"""
        # OpenWeatherMap не предоставляет отдельный эндпоинт для УФ,
        # но он есть в One Call API. Используем его.
        data = WeatherService._make_request("onecall", {"lat": lat, "lon": lon, "exclude": "minutely,hourly,daily,alerts"})
        if not data or not data.get("current"):
            return None
        
        return {
            "uv_index": data["current"].get("uvi", 0)
        }

    @staticmethod
    def get_full_weather_data(city: str):
        """Объединяет все данные в один комплексный ответ"""
        weather = WeatherService.get_current_weather(city)
        if not weather:
            return None
        
        forecast = WeatherService.get_forecast(city)
        air_quality = WeatherService.get_air_pollution(weather["lat"], weather["lon"])
        uv_index = WeatherService.get_uv_index(weather["lat"], weather["lon"])

        # Удаляем lat/lon из основного объекта, они нужны только для внутренних запросов
        del weather["lat"]
        del weather["lon"]
        
        return {
            "weather": weather,
            "forecast": forecast,
            "air_quality": air_quality,
            "uv_index": uv_index,
        }
