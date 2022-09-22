from opendrive2tess.utils.config import *


def get_section_childs(section_info, lengths, direction, road_id, section_id):
    # 分为左右车道，同时过滤tess规则下不同的车道类型
    if direction == 'left':
        lane_ids = [lane_id for lane_id in section_info['lanes'].keys() if
                    lane_id > 0 and lane_id in section_info["tess_lane_ids"]]
    else:
        lane_ids = [lane_id for lane_id in section_info['lanes'].keys() if
                    lane_id < 0 and lane_id in section_info["tess_lane_ids"]]
    # 路段遍历，获取link段，处理异常点
    point_infos = []
    # 查找连接段
    for index, length in enumerate(lengths):
        point_info = {
            'lanes': {},
            'is_link': True,
        }
        for lane_id in lane_ids:
            lane_info = section_info['lanes'][lane_id]
            tess_lane_type = LANE_TYPE_MAPPING.get(lane_info['type'])
            if tess_lane_type not in WIDTH_LIMIT.keys() or lane_info['widths'][index] > \
                    WIDTH_LIMIT[tess_lane_type]['split']:
                point_info['lanes'][lane_id] = lane_info['type']  # 无宽度限制或者宽度足够，正常车道
            elif lane_info['widths'][index] > WIDTH_LIMIT[tess_lane_type]['join']:
                point_info['lanes'][lane_id] = lane_info['type']  # 宽度介于中间，作为连接段
                point_info['is_link'] = False
            # 否则，不加入车道列表
        point_infos.append(point_info)

    # 连续多个点的信息完全一致，可作为同一路段
    childs = []
    child_point = []
    start_index = None  # 分片时，start_index 为None 会视为0
    for index in range(len(lengths)):
        if len(child_point) == 1:
            start_index = index - 1
        point_info = point_infos[index]
        if index < POINT_REQUIRE:  # 首尾必须为link
            child_point.append(point_infos[0])
        elif len(lengths) - index - 1 < POINT_REQUIRE:
            child_point.append(point_infos[-1])
        elif not child_point:  # 原列表为空
            if point_info['is_link']:
                child_point.append(point_info)
            else:
                continue
        else:  # 原列表不为空
            if point_info == child_point[0]:
                child_point.append(point_info)
            elif len(child_point) >= POINT_REQUIRE:
                childs.append(
                    {
                        'start': start_index,
                        'end': index,
                        'lanes': set(child_point[0]['lanes'].keys()) & set(child_point[0]['lanes'].keys()),
                    }
                )
                child_point = []
            else:
                continue

    # 把最后一个存在的点序列导入, 最后一个应该以末尾点为准,但是如果此处包含了首&尾，应该取数据量的交集
    # 这样可能会丢失部分路段，所以在建立连接段时，必须确保 from_lane, to_lane 均存在
    childs.append(
        {
            'start': start_index,
            'end': len(lengths) - 1,
            'lanes': set(child_point[0]['lanes'].keys()) & set(child_point[0]['lanes'].keys())
        }
    )
    # lengths 只是断点序列，标记着与起始点的距离,反向用了同样的lengths
    # 得到link的列表,因为lane的点坐标与方向有关，所以此时的child已经根据方向排序
    return childs


# 判断道路id的合法性
def get_inter(string, roads_info):
    inter_list = []
    is_true = True
    for i in string.split('.'):
        try:
            inter_list.append(int(i))
        except:
            inter_list.append(None)
            is_true = False

    # 检查 前后续路段 是否存在,不存在可以忽略
    if inter_list[0] not in roads_info.keys():
        is_true = False
    return [is_true, *inter_list]


# 为 child 间创建连接
def connect_childs(links, connector_mapping):
    for index in range(len(links) - 1):
        from_link_info = links[index]
        to_link_info = links[index + 1]
        from_link = from_link_info['link']
        to_link = to_link_info['link']
        if not (from_link and to_link and from_link_info['lane_ids'] and to_link_info['lane_ids']):
            continue

        connect_lanes = set()
        for lane_id in set(from_link_info['lane_ids'] + to_link_info['lane_ids']):
            # 车道原始编号相等，取原始编号对应的车道，否则，取临近车道(lane_ids 是有序的，所以临近车道永远偏向周边区)
            from_lane_id = min(from_link_info['lane_ids'], key=lambda x: abs(x - lane_id))
            from_lane = from_link_info[from_lane_id]
            to_lane_id = min(to_link_info['lane_ids'], key=lambda x: abs(x - lane_id))
            to_lane = to_link_info[to_lane_id]
            connect_lanes.add((from_lane.number() + 1, to_lane.number() + 1))

        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'] += [i[0] for i in connect_lanes]
        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'] += [i[1] for i in connect_lanes]
        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'] += [None for i in connect_lanes]
        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['infos'] += []
