import collections
import copy
import json
import os


def get_section_points(section_breakpoints, lengths, lane_ids):
    if section_breakpoints is None:
        section_points = []
        point_lanes = set(lane_ids)
        for i in range(0, len(lengths)):
            data = {
                "type": 'link',
                'lane_ids': copy.copy(point_lanes),
            }
            section_points.append(data)
        return section_points

    split_index = section_breakpoints['split']['index'] and [i for i in
                                                             range(min(section_breakpoints['split']['index']),
                                                                   max(section_breakpoints['split']['index']) + 1)]
    join_index = section_breakpoints['join']['index'] and [i for i in range(min(section_breakpoints['join']['index']),
                                                                            max(section_breakpoints['join'][
                                                                                    'index']) + 1)]
    section_points = []
    point_lanes = set(lane_ids)
    # 每个section的起止必须为正常link
    for i in range(0, len(lengths)):
        # 初始及尾部的车道需要特殊处理成link(根据width处理)
        if i in [0, 1, len(lengths) - 1, len(lengths) - 2]:
            point_type = 'link'
            point_lanes = set(lane_ids)
            for lane_id in lane_ids:
                if section_info['lanes'][lane_id]['type'] in width_limit.keys() and \
                        section_info['lanes'][lane_id]['widths'][i] < \
                        width_limit[section_info['lanes'][lane_id]['type']]['split']:
                    point_lanes = set(lane_ids)
                    point_lanes.remove(lane_id)
        elif i in split_index:
            point_type = 'split'
            for lane in section_breakpoints['split']['lanes']:
                point_lanes.add(lane)

        elif i in join_index:
            point_type = 'join'
            for lane in section_breakpoints['join']['lanes']:
                if lane in point_lanes:
                    point_lanes.remove(lane)
        else:
            point_type = 'link'
        data = {
            "type": point_type,
            'lane_ids': copy.copy(point_lanes),
        }
        section_points.append(data)
    return section_points

def get_section_breakpoints(lane_ids, section_info, lengths):
    # TODO 路段遍历，获取link段，处理异常点
    section_breakpoints = {
        'split': {
            'lanes': [],
            'index': [],
        },
        'join': {
            'lanes': [],
            'index': [],
        },
    }
    # 查找连接段
    for lane_id in lane_ids:
        lane_info = section_info['lanes'][lane_id]
        # 确保车道点序列和参考线序列保持一致
        if lane_info['type'] in width_limit.keys():
            lanelet_split, lanelet_split_index = False, None
            lanelet_join, lanelet_join_index = False, None
            limit_width = width_limit[lane_info['type']]
            limit_split = limit_width['split']
            limit_join = limit_width['join']
            widths = lane_info['widths']

            # 查找车道的断点
            connect_index = []
            for index in range(len(widths)):
                width = widths[index]
                if width > limit_join and width < limit_split:
                    connect_index.append(index)

            if connect_index:
                if abs(widths[connect_index[0]] - widths[connect_index[-1]]) < 1:
                    pass  # 无法处理一条车道变宽然后变窄的情况
                elif widths[connect_index[0]] > widths[connect_index[-1]]:
                    connect_type = 'join'
                    section_breakpoints['join']['lanes'].append(lane_id)
                    section_breakpoints['join']['index'] += connect_index

                else:
                    connect_type = 'split'
                    section_breakpoints['split']['lanes'].append(lane_id)
                    section_breakpoints['split']['index'] += connect_index


    if section_breakpoints['split']['lanes'] and section_breakpoints['join']['lanes'] and \
            not (max(section_breakpoints['split']['index']) <= min(section_breakpoints['join']['index']) or min(section_breakpoints['split']['index']) >= max(section_breakpoints['join']['index'])):
        # 异常的特殊情况（重叠），不处理
        section_breakpoints = None


    if section_breakpoints and not (section_breakpoints['split']['lanes'] + section_breakpoints['join']['lanes']):
        section_breakpoints = None
    section_points = get_section_points(section_breakpoints, lengths, lane_ids)
    return section_points


# TODO 对于biking driving 不在同一路段的问题，我们可以生成两个json，分别过滤不同的值，多次执行生成路段
width_limit = {
    'driving': {
        'split': 3,  # 作为正常的最窄距离
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
file_name = 'hdmap1.4_foshan_20220111'

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
