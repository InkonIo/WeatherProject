from flask import Flask
from flask_cors import CORS
from mainn_controller import main_bp
from moon_api import moon_bp

app = Flask(__name__)
CORS(app)

# Регистрируем наши маршруты
app.register_blueprint(main_bp)
app.register_blueprint(moon_bp)

if __name__ == "__main__":
    app.run(port=8080, debug=True)
