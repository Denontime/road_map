# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from tools.route_planner import RoutePlanner

AMAP_KEY = '9a108c93d1590cf87f1a289648f30db3'
planner = RoutePlanner(AMAP_KEY)

print("Generating motorcycle route book...")
route_data = planner.generate_route_book_data(
    '银川市吾悦广场',
    '灵武市园疙瘩湖',
    ['宁东镇鸭子荡水库'],
    vehicle_type='motorcycle'
)

if 'error' not in route_data:
    output_dir = planner.save_route_book(route_data)
    print(f"Route book saved to: {output_dir}")
    print(f"Vehicle: {route_data['vehicle_info']['name']}")
    print(f"Distance: {route_data['go_route']['total_distance']/1000:.1f} km")
    print(f"Duration: {route_data['go_route']['total_duration']/60:.0f} min")
else:
    print(f"Error: {route_data['error']}")