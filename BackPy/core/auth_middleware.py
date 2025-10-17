from functools import wraps
from flask import request, jsonify
from BackPy.core.jwt_utils import decode_access_token
from BackPy.app.services.user_service import UserService

def jwt_required(f):
    """Декоратор для защиты маршрутов с помощью JWT токена"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"msg": "Missing Authorization Header"}), 401

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({"msg": "Token format is 'Bearer <token>'"}), 401

        payload = decode_access_token(token)

        if "error" in payload:
            return jsonify({"msg": payload["error"]}), 401

        # Получаем пользователя из базы данных по ID, который мы сохранили в токене
        user_id = payload.get("sub")
        current_user = UserService.get_user_by_id(user_id)

        if not current_user:
            return jsonify({"msg": "User not found"}), 401

        # Передаем объект пользователя в функцию
        return f(current_user, *args, **kwargs)

    return decorated
