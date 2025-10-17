from BackPy.app.db.database import db
from datetime import datetime, timedelta
import random
import string

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    first_name = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(100), nullable=True)

    # Поля для аутентификации через Telegram
    auth_code = db.Column(db.String(6), nullable=True)
    code_expiry = db.Column(db.DateTime, nullable=True)

    # Поля для подписки (из старого кода)
    subscription_end = db.Column(db.DateTime, nullable=True)
    is_premium = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def generate_auth_code(self):
        """Генерирует 6-значный код и устанавливает время его жизни (5 минут)"""
        self.auth_code = ''.join(random.choices(string.digits, k=6))
        self.code_expiry = datetime.utcnow() + timedelta(minutes=5)
        db.session.commit()
        return self.auth_code

    def check_auth_code(self, code):
        """Проверяет код и его время жизни"""
        if self.auth_code == code and self.code_expiry and self.code_expiry > datetime.utcnow():
            # Код верный и не истек
            self.auth_code = None  # Сброс кода после успешной авторизации
            self.code_expiry = None
            db.session.commit()
            return True
        return False

    def __repr__(self):
        return f"<User {self.username or self.telegram_id}>"
