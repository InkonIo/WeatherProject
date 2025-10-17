from flask import Blueprint, request, jsonify
from BackPy.app.services.user_service import UserService
from BackPy.core.auth_middleware import jwt_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/telegram_code', methods=['POST'])
def authenticate_by_code():
    """
    POST /api/auth/telegram_code
    Аутентификация с помощью 6-значного кода из Telegram.
    """
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    code = data.get('code')

    if not telegram_id or not code:
        return jsonify({"msg": "Missing telegram_id or code"}), 400

    try:
        telegram_id = int(telegram_id)
    except ValueError:
        return jsonify({"msg": "Invalid telegram_id format"}), 400

    access_token = UserService.authenticate_with_code(telegram_id, code)

    if access_token:
        return jsonify({
            "msg": "Authentication successful",
            "access_token": access_token
        }), 200
    else:
        return jsonify({"msg": "Invalid code or code expired"}), 401

@auth_bp.route('/user/me', methods=['GET'])
@jwt_required
def get_current_user(current_user):
    """
    GET /api/user/me
    Получение информации о текущем пользователе (защищенный маршрут).
    """
    return jsonify({
        "id": current_user.id,
        "telegram_id": current_user.telegram_id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "city": current_user.city,
        "is_premium": current_user.is_premium
    }), 200
