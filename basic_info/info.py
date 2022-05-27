import json
import os

work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')  # 下属必有files文件夹，用来存放xodr和生成的json/csv文件
file_name = 'test3'

with open(os.path.join(work_dir, f"{file_name}-路段.json"), 'r') as f:
    roads_info = json.load(f)
    roads_info = {
        int(k): v for k, v in roads_info.items()
    }

with open(os.path.join(work_dir, f"{file_name}-车道.json"), 'r') as f:
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

print(roads_info)
