from flask import Flask, request, jsonify, send_from_directory
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.route_planner import RoutePlanner
from tools.config import config

app = Flask(__name__, static_folder='static')

AMAP_KEY = os.environ.get('AMAP_WEBSERVICE_KEY', '9a108c93d1590cf87f1a289648f30db3')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/geocode', methods=['POST'])
def geocode():
    data = request.get_json()
    address = data.get('address')
    city = data.get('city')

    if not address:
        return jsonify({'error': '地址不能为空'}), 400

    planner = RoutePlanner(AMAP_KEY)
    result = planner.geocode_address(address, city)

    if result:
        return jsonify(result)
    return jsonify({'error': '无法解析该地址'}), 404

@app.route('/api/route/plan', methods=['POST'])
def plan_route():
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')
    waypoints = data.get('waypoints', [])

    if not origin or not destination:
        return jsonify({'error': '起点和终点不能为空'}), 400

    planner = RoutePlanner(AMAP_KEY)

    origin_data = planner.geocode_address(origin)
    dest_data = planner.geocode_address(destination)

    if not origin_data:
        return jsonify({'error': f'无法解析起点地址: {origin}'}), 404
    if not dest_data:
        return jsonify({'error': f'无法解析终点地址: {destination}'}), 404

    waypoint_data = []
    for wp in waypoints:
        wp_data = planner.geocode_address(wp)
        if wp_data:
            waypoint_data.append(wp_data)

    route_data = planner.plan_route(origin_data, dest_data, waypoint_data)

    return jsonify(route_data)

@app.route('/api/route/book', methods=['POST'])
def generate_route_book():
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')
    waypoints = data.get('waypoints', [])
    return_via = data.get('return_via', [])
    vehicle_type = data.get('vehicle_type', 'motorcycle')

    if not origin or not destination:
        return jsonify({'error': '起点和终点不能为空'}), 400

    planner = RoutePlanner(AMAP_KEY)
    route_data = planner.generate_route_book_data(origin, destination, return_via, vehicle_type)

    if 'error' in route_data:
        return jsonify(route_data), 400

    output_dir = planner.save_route_book(route_data)

    return jsonify({
        'success': True,
        'output_dir': output_dir,
        'data': route_data
    })

@app.route('/api/route/book/preview', methods=['POST'])
def preview_route_book():
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')
    waypoints = data.get('waypoints', [])
    return_via = data.get('return_via', [])
    vehicle_type = data.get('vehicle_type', 'motorcycle')

    if not origin or not destination:
        return jsonify({'error': '起点和终点不能为空'}), 400

    planner = RoutePlanner(AMAP_KEY)
    route_data = planner.generate_route_book_data(origin, destination, return_via, vehicle_type)

    if 'error' in route_data:
        return jsonify(route_data), 400

    html = planner.generate_html(route_data)
    return jsonify({
        'html': html,
        'data': route_data
    })

@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory(config.OUTPUT_DIR, filename)

@app.route('/api/output/list')
def list_outputs():
    if not os.path.exists(config.OUTPUT_DIR):
        return jsonify([])

    outputs = []
    for item in os.listdir(config.OUTPUT_DIR):
        item_path = os.path.join(config.OUTPUT_DIR, item)
        if os.path.isdir(item_path):
            outputs.append({
                'name': item,
                'path': item
            })
    return jsonify(outputs)

if __name__ == '__main__':
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs('static', exist_ok=True)
    print(f"Server starting...")
    print(f"API Key: {AMAP_KEY[:10]}...")
    print(f"Output directory: {config.OUTPUT_DIR}")
    app.run(host='127.0.0.1', port=5000, debug=True)