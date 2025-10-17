from flask import Blueprint, request, jsonify
from BackPy.app.services.weather_service import WeatherService
from BackPy.app.services.user_service import UserService
from BackPy.core.auth_middleware import jwt_required

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/data', methods=['GET'])
@jwt_required
def get_weather_data(current_user):
    """
    GET /api/weather/data
    Получение всех данных о погоде для города пользователя.
    """
    city = current_user.city
    
    if not city:
        # Если город не установлен, можно принять его как query-параметр для первого запроса
        city = request.args.get('city')
        if not city:
            return jsonify({"msg": "City not set for user. Please provide 'city' query parameter or set it in your profile."}), 400

    # Обновляем город пользователя, если он был передан в запросе и отличается от текущего
    if request.args.get('city') and request.args.get('city') != current_user.city:
        UserService.update_user_city(current_user.id, city)
        
    full_data = WeatherService.get_full_weather_data(city)

    if full_data:
        return jsonify(full_data), 200
    else:
        return jsonify({"msg": f"Could not retrieve weather data for city: {city}"}), 404

@weather_bp.route('/city', methods=['POST'])
@jwt_required
def set_user_city(current_user):
    """
    POST /api/weather/city
    Установка города для пользователя.
    """
    data = request.get_json()
    city = data.get('city')

    if not city:
        return jsonify({"msg": "Missing 'city' in request body"}), 400

    # Проверяем, что город существует
    weather = WeatherService.get_current_weather(city)
    if not weather:
        return jsonify({"msg": f"City '{city}' not found by weather API."}), 404

    UserService.update_user_city(current_user.id, weather['city'])
    
    return jsonify({"msg": f"City set to {weather['city']}"}), 200
