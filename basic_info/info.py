import json


num = 4
with open(f'basic_info/files/路段{num}.json', 'r') as f:
    roads_info = json.load(f)
    roads_info = {
        int(k): v for k, v in roads_info.items()
    }

with open(f'basic_info/files/车道{num}.json', 'r') as f:
    lanes_info = json.load(f)

#
# for _, road_info in roads_info.items():
#     # road
#     road_info["sections"] = {}
    # road_info["max_lane"] = 0
    # road_info["min_lane"] = 0

for lane_name, lane_info in lanes_info.items():
    if not lane_info:  # 此车道只是文件中某车道的前置或者后置车道，仅仅被提及，是空信息，跳过
        continue
    road_id = lane_info['road_id']
    section_id = lane_info['section_id']
    lane_id = lane_info['lane_id']

    # 添加默认属性
    roads_info[road_id].setdefault('sections', {})
    roads_info[road_id]['sections'].setdefault(section_id, {})
    roads_info[road_id]['sections'][section_id].setdefault('lanes', {})
    roads_info[road_id]['sections'][section_id]["lanes"][lane_id] = lane_info

# for _, road_info in roads_info.items():
#     print(_)
#     road_info["max_lane"] = max(road_info['lanes'].keys())
#     road_info["min_lane"] = min(road_info['lanes'].keys())



# link_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] == -1]
# junction_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] != -1]
# # 创建所有的Link
# for road_id in link_road_ids:
#     for lane_id, lane_info in roads_info[road_id]['lanes'].items():
#         vertices = roads_info[road_id]['road_center_vertices']
#         temp_vertice = vertices[0]
#         for vertice in vertices:
#             disc = (vertice[0] - temp_vertice[0]) ** 2 + (vertice[1] - temp_vertice[1]) ** 2
#             if disc > 1:
#                 print(1)
#             temp_vertice = vertice

