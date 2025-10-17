from BackPy.app.db.database import db
from BackPy.app.models.user import User

class UserService:
    @staticmethod
    def get_user_by_telegram_id(telegram_id):
        """Найти пользователя по Telegram ID"""
        return User.query.filter_by(telegram_id=telegram_id).first()

    @staticmethod
    def get_user_by_id(user_id):
        """Найти пользователя по ID"""
        return User.query.get(user_id)

    @staticmethod
    def create_or_update_user(telegram_id, username, first_name):
        """Создать или обновить пользователя"""
        user = UserService.get_user_by_telegram_id(telegram_id)
        if user:
            user.username = username
            user.first_name = first_name
        else:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def generate_auth_code_for_user(telegram_id):
        """Сгенерировать и сохранить код авторизации для пользователя"""
        user = UserService.get_user_by_telegram_id(telegram_id)
        if user:
            code = user.generate_auth_code()
            return code
        return None

    @staticmethod
    def authenticate_with_code(telegram_id, code):
        """Проверить код авторизации и вернуть JWT токен"""
        from BackPy.app.jwt_utils import create_access_token
        
        user = UserService.get_user_by_telegram_id(telegram_id)
        if user and user.check_auth_code(code):
            # Аутентификация успешна, генерируем токен
            token_data = {"sub": str(user.id), "telegram_id": str(user.telegram_id)}
            access_token = create_access_token(data=token_data)
            return access_token
        return None
    
    @staticmethod
    def update_user_city(user_id, city):
        """Обновить город пользователя"""
        user = UserService.get_user_by_id(user_id)
        if user:
            user.city = city
            db.session.commit()
            return True
        return False
