import collections
import copy
import json
import os


# TODO 对于biking driving 不在同一路段的问题，我们可以生成两个json，分别过滤不同的值，多次执行生成路段
width_limit = {
    'driving': {
        'split': 2,  # 作为正常的最窄距离
        'join': 0.1, # 被忽略时的最宽距离
    },
    # 'biking': 1,
}
point_require = 2  # 连续次数后可视为正常车道，或者连续次数后可视为连接段,最小值为2
if point_require < 2:
    raise 1


def get_section_childs(lane_ids, section_info, lengths):
    # TODO 路段遍历，获取link段，处理异常点
    point_infos = []
    # 查找连接段
    for index in range(len(lengths)):
        point_info = {
            'lanes': {},
            'is_link': True,
        }
        for lane_id in lane_ids:
            lane_info = section_info['lanes'][lane_id]
            if lane_info['type'] not in width_limit.keys() or lane_info['widths'][index] > width_limit[lane_info['type']]['split']:
                point_info['lanes'][lane_id] = lane_info['type']  # 无宽度限制或者宽度足够，正常车道
            elif lane_info['widths'][index] > width_limit[lane_info['type']]['join']:
                point_info['lanes'][lane_id] = lane_info['type']  # 宽度介于中间，作为连接段
                point_info['is_link'] = False
            # 否则，不加入车道列表
        point_infos.append(point_info)

    # 连续多个点的信息完全一致，可作为 TODO 对lane_type 做映射，不同车道类型可以汇合成同一类型，
    childs = []
    child_point = []
    start_index = None
    for index in range(len(lengths)):
        if len(child_point) == 1:
            start_index = index - 1
        point_info = point_infos[index]
        if index < point_require: #首尾必须为link
            child_point.append(point_infos[0])
        elif len(lengths) - index - 1 < point_require:
            child_point.append(point_infos[-1])
        elif not child_point:  # 原列表为空
            if point_info['is_link']:
                child_point.append(point_info)
            else:
                continue
        else:  # 原列表不为空
            if point_info == child_point[0]:
                child_point.append(point_info)
            elif len(child_point) >= point_require:
                childs.append(
                    {
                        'start': start_index,
                        'end': index,
                        'point': copy.copy(child_point)
                    }
                )
                child_point = []
            else:
                continue

    childs.append(
        {
            'start': start_index,
            'end': len(lengths) - 1,
            'point': copy.copy(child_point)
        }
    )  # 把最后一个存在的点序列导入

    # 得到link的列表
    return childs


work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')  # 下属必有files文件夹，用来存放xodr和生成的json/csv文件
file_name = 'map_hz_kaifangroad'

with open(os.path.join(work_dir, f"{file_name}.json"), 'r') as f:
    data = json.load(f)
header_info = data['header']
roads_info = data['road']
lanes_info = data['lane']
roads_info = {
    int(k): v for k, v in roads_info.items()
}
for road_id, road_info in roads_info.items():
    if road_info['junction_id'] == None:
        road_info['junction_id'] = -1


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

for road_id, road_info in roads_info.items():
    for section_id, section_info in road_info['sections'].items():
        lengths = road_info['road_points'][str(section_id)]['lengths']
        section_length = len(road_info['road_points'][str(section_id)]['lengths'])
        section_left_points = get_section_childs(road_info['lane_sections'][str(section_id)]['left'], section_info, lengths)
        section_right_points = get_section_childs(road_info['lane_sections'][str(section_id)]['right'], section_info, lengths)
        # section_left_points = get_section_breakpoints(road_info['lane_sections'][str(section_id)]['left'], section_info, lengths)
        # section_right_points = get_section_breakpoints(road_info['lane_sections'][str(section_id)]['right'], section_info, lengths)
        section_info['left_points'] = section_left_points
        section_info['right_points'] = section_right_points
