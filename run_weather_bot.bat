@echo off

REM Переходим в директорию, где находится скрипт бота
cd /d "D:\WeatherProject"

REM Запускаем бота
python weather_bot.py

REM Оставляем окно открытым, чтобы увидеть вывод и ошибки
pause
