from flask_sqlalchemy import SQLAlchemy
from BackPy.config.settings import settings

db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Импортируем модели, чтобы SQLAlchemy их увидел
        from BackPy.app.models.user import User
        db.create_all()
