from flask import Blueprint, jsonify, request, render_template
from datetime import datetime
from astral import moon
from astral import LocationInfo

moon_bp = Blueprint("moon", __name__, url_prefix="/api")

@moon_bp.route('/moon-phase-page')
def moon_page():
    return render_template('moon.html')

@moon_bp.route('/moon-phase')
def get_moon_phase():
    date_str = request.args.get('date')
    lat = float(request.args.get('lat', 43.238949))
    lon = float(request.args.get('lon', 76.889709))

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    city = LocationInfo(latitude=lat, longitude=lon)

    phase_value = moon.phase(date)
    illumination = (1 - abs(14 - phase_value) / 14) * 100

    if phase_value < 1:
        phase_name = "NEW_MOON"
    elif phase_value < 7:
        phase_name = "WAXING_CRESCENT"
    elif phase_value < 8:
        phase_name = "FIRST_QUARTER"
    elif phase_value < 14:
        phase_name = "WAXING_GIBBOUS"
    elif phase_value < 15:
        phase_name = "FULL_MOON"
    elif phase_value < 22:
        phase_name = "WANING_GIBBOUS"
    elif phase_value < 23:
        phase_name = "LAST_QUARTER"
    else:
        phase_name = "WANING_CRESCENT"

    result = {
        "Phase": phase_name,
        "Illumination": round(illumination, 1),
        "PhaseValue": round(phase_value, 2),
        "Latitude": lat,
        "Longitude": lon
    }

    print("🌙 MOON RESPONSE:", result)
    return jsonify(result)