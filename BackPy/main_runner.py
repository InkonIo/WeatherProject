import threading
from flask import Flask
from BackPy.app.db.database import init_db
from BackPy.app.api.auth import auth_bp
from BackPy.app.api.weather import weather_bp
from BackPy.config.settings import settings
from BackPy.bot.bot_handlers import init_bot
from BackPy.controller.main_controller import main_bp
from flask_swagger_ui import get_swaggerui_blueprint

HOST = 'localhost'
PORT = 8080

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
init_db(app)  # инициализация базы данных

# Регистрируем API
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(weather_bp, url_prefix='/api/weather')

app.register_blueprint(main_bp)


# Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "MeteoSphere API"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def run_flask_app():
    print(f"🌐 Flask API запущен на http://{HOST}:{PORT}")
    print(f"📄 Документация API доступна на http://{HOST}:{PORT}/api/docs")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)

def run_telegram_bot():
    with app.app_context():
        print("🤖 Telegram Bot запущен...")
        try:
            bot_instance = init_bot(app)
            bot_instance.infinity_polling()
        except Exception as e:
            print(f"❌ Ошибка при работе бота: {e}")

if __name__ == '__main__':
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.start()

    # Flask в основном потоке
    run_flask_app()
