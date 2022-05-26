road_lane_info = [{'lane_id': 1}, {'lane_id': 3}]
road_lane_info = sorted(road_lane_info, key=lambda i: i['lane_id'])
print(road_lane_info)