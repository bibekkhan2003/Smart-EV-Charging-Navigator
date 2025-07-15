from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.data.stations import get_stations_data


app = Flask(__name__)
CORS(app)

@app.route('/api/stations', methods=['GET'])
def get_stations():
    city = request.args.get('city', 'Mumbai')
    return jsonify(get_stations_data(city))
    '''city = request.args.get('city', 'Delhi')

    city_stations = {
        "Delhi": [
            {"id": 1, "name": "CP Fast Charger", "lat": 28.6139, "lon": 77.2090,
             "available_slots": 4, "total_slots": 10, "type": "Fast", "address": "Connaught Place",
             "cost_per_hour": 150, "supports_swapping": True},
            {"id": 2, "name": "Lajpat EV Hub", "lat": 28.5678, "lon": 77.2345,
             "available_slots": 2, "total_slots": 6, "type": "Normal", "address": "Lajpat Nagar",
             "cost_per_hour": 100, "supports_swapping": False}
        ],
        "Mumbai": [
            {"id": 3, "name": "Bandra EV Point", "lat": 19.0590, "lon": 72.8295,
             "available_slots": 5, "total_slots": 12, "type": "Fast", "address": "Bandra West",
             "cost_per_hour": 180, "supports_swapping": True},
            {"id": 4, "name": "Dadar EcoCharge", "lat": 19.0180, "lon": 72.8436,
             "available_slots": 1, "total_slots": 8, "type": "Normal", "address": "Dadar East",
             "cost_per_hour": 90, "supports_swapping": False}
        ],
        "Bangalore": [
            {"id": 5, "name": "Koramangala PlugIn", "lat": 12.9352, "lon": 77.6141,
             "available_slots": 3, "total_slots": 9, "type": "Fast", "address": "Koramangala",
             "cost_per_hour": 120, "supports_swapping": True},
            {"id": 6, "name": "Indiranagar EV Zone", "lat": 12.9718, "lon": 77.6408,
             "available_slots": 0, "total_slots": 7, "type": "Normal", "address": "Indiranagar",
             "cost_per_hour": 85, "supports_swapping": False}
        ],
        "Chennai": [
            {"id": 7, "name": "T-Nagar ChargeBay", "lat": 13.0423, "lon": 80.2337,
             "available_slots": 6, "total_slots": 10, "type": "Fast", "address": "T Nagar",
             "cost_per_hour": 130, "supports_swapping": True},
            {"id": 8, "name": "Velachery EcoStation", "lat": 12.9792, "lon": 80.2200,
             "available_slots": 3, "total_slots": 5, "type": "Normal", "address": "Velachery",
             "cost_per_hour": 95, "supports_swapping": False}
        ],
        "Hyderabad": [
            {"id": 9, "name": "Gachibowli EV Hub", "lat": 17.4435, "lon": 78.3772,
             "available_slots": 7, "total_slots": 10, "type": "Fast", "address": "Gachibowli",
             "cost_per_hour": 140, "supports_swapping": True},
            {"id": 10, "name": "Madhapur ChargePoint", "lat": 17.4483, "lon": 78.3915,
             "available_slots": 2, "total_slots": 6, "type": "Normal", "address": "Madhapur",
             "cost_per_hour": 110, "supports_swapping": False}
        ],
        "Pune": [
            {"id": 11, "name": "Kothrud SparkPoint", "lat": 18.5074, "lon": 73.8077,
             "available_slots": 3, "total_slots": 8, "type": "Fast", "address": "Kothrud",
             "cost_per_hour": 125, "supports_swapping": True},
            {"id": 12, "name": "Viman Nagar EcoCharge", "lat": 18.5679, "lon": 73.9143,
             "available_slots": 1, "total_slots": 5, "type": "Normal", "address": "Viman Nagar",
             "cost_per_hour": 100, "supports_swapping": False}
        ],
        "Kolkata": [
            {"id": 13, "name": "Salt Lake EV Bay", "lat": 22.5769, "lon": 88.4339,
             "available_slots": 4, "total_slots": 9, "type": "Fast", "address": "Salt Lake",
             "cost_per_hour": 115, "supports_swapping": True},
            {"id": 14, "name": "Howrah EV Stop", "lat": 22.5892, "lon": 88.3100,
             "available_slots": 2, "total_slots": 6, "type": "Normal", "address": "Howrah",
             "cost_per_hour": 90, "supports_swapping": False}
        ]
    }

    return jsonify(city_stations.get(city, []))'''


@app.route('/api/route', methods=['POST'])
def get_route():
    data = request.json
    return jsonify({
        "distance": 10.5,
        "time": 20.2,
        "energy_cost": 2.3
    })


@app.route('/api/predict/<int:station_id>', methods=['GET'])
def predict_utilization(station_id):
    return jsonify({
        "timestamps": ["10:00", "11:00", "12:00", "13:00", "14:00"],
        "utilization": [20, 35, 60, 50, 40]
    })
from math import radians, cos, sin, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    city = request.args.get('city')
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))

    stations = get_stations().get_json()

    # Filter for selected city only
    stations = [s for s in stations if s.get("city", city) == city]

    def score(station):
        distance = haversine(lat, lon, station["lat"], station["lon"])
        cost = station["cost_per_hour"]
        availability = station["available_slots"]
        type_weight = 0 if station["type"] == "Normal" else -1
        return distance * 1.5 + cost * 0.3 - availability * 2 + type_weight

    best_by_distance = min(stations, key=lambda s: haversine(lat, lon, s["lat"], s["lon"]))
    best_by_cost = min(stations, key=lambda s: s["cost_per_hour"])
    best_by_availability = max(stations, key=lambda s: s["available_slots"])
    best_fast = next((s for s in sorted(stations, key=lambda s: score(s)) if s["type"] == "Fast"), best_by_distance)

    return jsonify({
        "nearest": best_by_distance,
        "cheapest": best_by_cost,
        "fastest": best_fast,
        "least_queue": best_by_availability
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
