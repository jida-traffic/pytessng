import json


num = 4
with open(f'basic_info/files/路段{num}.json', 'r') as f:
    roads_info = json.load(f)
    roads_info = {
        int(k): v for k, v in roads_info.items()
    }

with open(f'basic_info/files/车道{num}.json', 'r') as f:
    lanes_info = json.load(f)


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
