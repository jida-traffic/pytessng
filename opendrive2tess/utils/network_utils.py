import collections
import copy
import json

from opendrive2tess.utils.config import *
# 使用此功能必须依赖 TESS 安装包
from PySide2.QtGui import *
from Tessng import *
from lxml import etree
from opendrive2tess.opendrive2lanelet.opendriveparser.elements.roadLanes import Lane
from opendrive2tess.utils.convert_utils import convert_opendrive, convert_roads_info, convert_lanes_info
from opendrive2tess import send_signal


def get_section_childs(section_info, lengths, direction):
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
    for index in range(len(lengths)):
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
    start_index = None #分片时，start_index 为None 会视为0
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

        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'] = [i[0] for i in connect_lanes]
        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'] = [i[1] for i in connect_lanes]
        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['infos'] = []


class Section:
    def __init__(self, road_id, section_id, lane_ids: list):
        self.road_id = road_id
        self.id = section_id

        self._left_link = None
        self._right_link = None
        self.lane_ids = list(lane_ids or [])
        # 左右来向的车道id分别为正负， 需要根据tess的规则进行排序
        self.left_lane_ids = sorted(filter(lambda i: i > 0, self.lane_ids, ), reverse=True)
        self.right_lane_ids = sorted(filter(lambda i: i < 0, self.lane_ids, ), reverse=False)
        self.lane_mapping = {}

    @property
    def left_link(self):
        return self._left_link

    @left_link.setter
    def left_link(self, obj):
        for link_info in obj:
            link = link_info['link']
            if not link:
                continue
            lane_ids = link_info['lane_ids']
            index = 0
            for lane in link.lanes():
                link_info[lane_ids[index]] = lane
                index += 1
        self._left_link = obj

    @property
    def right_link(self):
        return self._right_link

    @right_link.setter
    def right_link(self, obj):
        for link_info in obj:
            link = link_info['link']
            # 路段创建失败时，link 为 None
            if not link:
                continue
            lane_ids = link_info['lane_ids']
            index = 0
            for lane in link.lanes():
                link_info[lane_ids[index]] = lane
                index += 1
        self._right_link = obj

    def tess_lane(self, lane_id, type):
        try:
            if lane_id > 0:
                if type == 'from':
                    link_info = self.left_link[-1]
                else:
                    link_info = self.left_link[0]
            else:
                if type == 'from':
                    link_info = self.right_link[-1]
                else:
                    link_info = self.right_link[0]
            return link_info.get(lane_id)
        except:
            return None

    def tess_link(self, lane_id, type):
        try:
            if lane_id > 0:
                if type == 'from':
                    return self.left_link[-1]['link']
                else:
                    return self.left_link[-0]['link']
            else:
                if type == 'from':
                    return self.right_link[-1]['link']
                else:
                    return self.right_link[0]['link']
        except:
            return None


class Road:
    def __init__(self, road_id):
        self.id = road_id
        self.sections = []

    def section(self, section_id: int = None):
        if section_id is None:
            return self.sections
        else:
            for section in self.sections:
                if section.id == section_id:
                    return section
            # return self.sections[section_id]

    def section_append(self, section: Section):
        self.sections.append(section)
        self.sections.sort(key=lambda i: i.id)


class Network:
    def __init__(self, opendrive):
        self.opendrive = opendrive
        self.network_info = None
        self.xy_move = (0, 0)
        self.size = (300, 600)

    def extract_network_info(self, step=None, filters=None, context=None):
        step = step or 1
        filters = filters or Lane.laneTypes
        opendrive = self.opendrive
        # 头信息
        header_info = {
            "date": opendrive.header.date,
            "geo_reference": opendrive.header.geo_reference,
        }

        # 参考线信息解析
        roads_info = convert_roads_info(opendrive, step, filters)

        # 车道点位序列不再独立计算，采用 road info 中参考线的点位
        # 车道信息解析，这一步最消耗时间，允许传入进度条
        scenario = convert_opendrive(opendrive, filters, roads_info, context)
        lanes_info = convert_lanes_info(opendrive, scenario, roads_info)

        network_info = {
            "header_info": header_info,
            "roads_info": roads_info,
            "lanes_info": lanes_info,
        }
        return network_info


    def convert_network(self, step=None, filters=None, context=None):
        try:
            self.network_info = self.extract_network_info(step, filters, context)
            roads_info = self.network_info["roads_info"]
            lanes_info = self.network_info["lanes_info"]

            xy_limit = None
            for road_id, road_info in roads_info.items():
                if road_info['junction_id'] == None:
                    road_info['junction_id'] = -1
                # 记录 坐标点的极值 (取左右point列表无区别，只是计算方向不同)
                for section_id, points in road_info['road_points'].items():
                    for point in points['right_points']:
                        position = point['position']
                        if xy_limit is None:  # x1,x2,y1,y2
                            xy_limit = [position[0], position[0], position[1], position[1]]
                        else:
                            xy_limit[0] = min(xy_limit[0], position[0])
                            xy_limit[1] = max(xy_limit[1], position[0])
                            xy_limit[2] = min(xy_limit[2], position[1])
                            xy_limit[3] = max(xy_limit[3], position[1])
            self.xy_move = (sum(xy_limit[:2]) / 2, sum(xy_limit[2:]) / 2) if xy_limit else (0, 0)
            self.size = (abs(xy_limit[0] - xy_limit[1]), abs(xy_limit[2] - xy_limit[3]))
            print(f"路网移动参数: {self.xy_move}")

            for lane_name, lane_info in lanes_info.items():
                if not lane_info:  # 此车道只是文件中某车道的前置或者后置车道，仅仅被提及，是空信息，跳过
                    continue
                road_id = lane_info['road_id']
                section_id = lane_info['section_id']
                lane_id = lane_info['lane_id']
                if road_id not in roads_info.keys():
                    continue

                # 添加默认属性
                roads_info[road_id].setdefault('sections', {})
                roads_info[road_id]['sections'].setdefault(section_id, {})
                roads_info[road_id]['sections'][section_id].setdefault('lanes', {})
                roads_info[road_id]['sections'][section_id]["lanes"][lane_id] = lane_info

            send_signal(context, 100, network_info=self.network_info)
            # json.dump(self.network_info, open("my.json", 'w'))

        except Exception as e:
            send_signal(context, 0, error=True)
            print(f"convert_network error: {e}")


    def create_network(self, tess_lane_types, netiface=None):
        if not netiface:
            netiface = tngIFace().netInterface()
        # 设置场景显示区域
        netiface.setSceneSize(*self.size)

        # 如果后续tess在同一路段中存在不同类型的车道，tess_lane_types需要做成列表嵌套
        error_junction = []

        # 从文件中取数据
        # self.network_info = json.load(open("my.json", "r"))
        # def update_dict(root):
        #     # 判断是否为空树
        #     if root == {}:
        #         return
        #     # 递归遍历嵌套字典
        #     list_key = list(root.keys())
        #     for root_key in list_key:
        #         # 递归非叶子节点
        #         try:
        #             temp = int(root_key)
        #         except:
        #             temp = root_key
        #         # print(root_key, temp)
        #         root[temp] = root.pop(root_key)
        #         if isinstance(root[temp], dict):
        #             update_dict(root[temp])
        # update_dict(self.network_info)

        for tess_lane_type in tess_lane_types:
            # 会改变数据结构，可能在重复创建时有影响，所以创建新的数据备份
            roads_info = copy.deepcopy(self.network_info["roads_info"])
            lanes_info = copy.deepcopy(self.network_info["lanes_info"])

            def default_dict():
                return {
                    'lFromLaneNumber': [],
                    'lToLaneNumber': [],
                    'lanesWithPoints3': [],
                    'infos': [],
                }

            connector_mapping = collections.defaultdict(default_dict)
            for road_id, road_info in roads_info.items():
                for section_id, section_info in road_info.get('sections', {}).items():
                    section_info['tess_lane_ids'] = []
                    for lane_id, lane_info in section_info['lanes'].items():
                        if LANE_TYPE_MAPPING.get(lane_info['type']) == tess_lane_type:
                            section_info['tess_lane_ids'].append(lane_id)

                    lengths = road_info['road_points'][section_id]['lengths']
                    section_info['left_childs'] = get_section_childs(section_info, lengths, 'left')
                    section_info['right_childs'] = get_section_childs(section_info, lengths, 'right')

            # 创建路段并记录路段内section连接
            road_mapping = self.create_links(netiface, roads_info, connector_mapping, error_junction)
            # 记录路段间的连接
            self.convert_link_connect(roads_info, lanes_info, connector_mapping, road_mapping, tess_lane_type,
                                      error_junction)
            # 记录交叉口
            self.convert_junction(roads_info, lanes_info, connector_mapping, road_mapping, tess_lane_type,
                                  error_junction)
            # 实现所有的连接关系
            self.create_connects(netiface, connector_mapping)
        return error_junction

    def create_links(self, netiface, roads_info, connector_mapping, error_junction):
        # 创建基础路段,和其section间的连接段
        road_mapping = dict()
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] != -1:
                continue  # 先行创建所有的基本路段
            tess_road = Road(road_id)
            for section_id, section_info in road_info.get('sections', {}).items():
                # section里的多段link已经根据方向重新排序
                tess_section = Section(road_id, section_id, section_info['tess_lane_ids'])
                tess_road.sections.append(tess_section)

                if not section_info['tess_lane_ids']:
                    continue
                for direction in ['left', 'right']:
                    # 判断此方向的路段中是否存在车道
                    is_exist = max(section_info['tess_lane_ids']) > 0 if direction == 'left' else min(section_info['tess_lane_ids']) < 0
                    if not is_exist:
                        continue

                    points = road_info['road_points'][section_id][f'{direction}_points']
                    # 对section分段
                    section_links = []
                    # 记录了所有的路段(断点)
                    childs = section_info[f'{direction}_childs']
                    # 右车道id为负，越小的越先在tess中创建，左车道id为正，越大的越先创建
                    reverse = True if direction == 'left' else False
                    for index in range(len(childs)):
                        child = childs[index]
                        # 步长过大，可能会导致在分段时 child 只包含了一个点
                        start_index, end_index = child['start'], child['end'] + 1
                        land_ids = sorted(child['lanes'], reverse=reverse) #列表内多点的的数据是一样的，取第一个即可
                        lCenterLinePoint = self.get_coo_list([point["position"] for point in points][start_index:end_index])
                        lanesWithPoints = [
                            {
                                'left': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['left_vertices'][
                                    start_index:end_index]),
                                'center': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['center_vertices'][
                                    start_index:end_index]),
                                'right': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['right_vertices'][
                                    start_index:end_index]),
                            }
                            for lane_id in land_ids
                        ]
                        link_obj = netiface.createLink3DWithLanePoints(lCenterLinePoint, lanesWithPoints,
                                                                     f"{road_id}_{section_id}_{index}_{direction}")
                        # link_obj 可能为None, 为什么
                        if not link_obj:
                            error_junction.append(
                                {
                                    "roadName": f"{road_id}_{section_id}_{index}_{direction}",
                                    "centerLine": [point["position"] for point in points][start_index:end_index],
                                    "landIds": land_ids,
                                    "message": "路段创建失败",
                                }
                            )
                        link_info = {
                            'link': link_obj,
                            'lane_ids': land_ids
                        }
                        section_links.append(link_info)

                    tess_section.__setattr__(f"{direction}_link", section_links)
                    connect_childs(getattr(tess_section, f"{direction}_link"), connector_mapping)
            road_mapping[road_id] = tess_road
        return road_mapping

    def convert_link_connect(self, roads_info, lanes_info, connector_mapping, road_mapping, tess_lane_type,
                             error_junction):
        # 累计所有的路段间的连接段
        link_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] == -1]
        junction_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] != -1]
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] != -1:
                continue

            # lane_sections 保存基本信息，sections 保存详情
            for section_id, section_info in road_info.get('sections', {}).items():
                # 路段间的连接段只向后连接,本身作为前路段(向前也一样，会重复一次)
                for lane_id in section_info["tess_lane_ids"]:
                    lane_info = section_info['lanes'][lane_id]
                    # 路段类型匹配失败，跳过
                    if LANE_TYPE_MAPPING.get(lane_info['type']) != tess_lane_type:
                        continue
                    predecessor_id = lane_info['name']

                    # 为了和交叉口保持一致，重新获取一次相关信息
                    is_true, from_road_id, from_section_id, from_lane_id, _ = get_inter(predecessor_id, roads_info)
                    # 部分车道的连接关系可能是'2.3.None.-1', 需要清除（上一车道宽度归零，不会连接到下一车道）
                    # 同时 predecessor_id 的 from_road 可能并不在路网中
                    if not (is_true and from_road_id in road_mapping.keys()):
                        continue

                    from_section = road_mapping[from_road_id].section(from_section_id)
                    from_link = from_section and from_section.tess_link(from_lane_id, 'from')
                    from_lane = from_section and from_section.tess_lane(from_lane_id, 'from')

                    for successor_id in lane_info["successor_ids"]:
                        is_true, to_road_id, to_section_id, to_lane_id, _ = get_inter(successor_id, roads_info)
                        if not (is_true and to_road_id in road_mapping.keys()):
                            continue

                        if to_road_id not in link_road_ids:  # 只针对性的创建路段间的连接
                            continue

                        # 查看 section 为什么为 None
                        to_section = road_mapping[to_road_id].section(to_section_id)
                        to_link = to_section and to_section.tess_link(to_lane_id, 'to')
                        to_lane = to_section and to_section.tess_lane(to_lane_id, 'to')

                        # 多种原因会出现这种情况,1.如果车道在此处宽度归零，是不会连接到下一车道的 2.步长过大导致取点时进行了交集
                        if not (from_link and from_lane and to_link and to_lane):
                            continue

                        if from_lane.actionType() != to_lane.actionType():
                            error_junction.append(
                                {
                                    "from_link_id": from_link.id(),
                                    "from_lane_number": from_lane.number() + 1,
                                    "from_lane_type": from_lane.actionType(),
                                    "to_link_id": to_link.id(),
                                    "to_lane_number": to_lane.number() + 1,
                                    "to_lane_type": from_lane.actionType(),
                                    "message": "连接段前后车道类型不同",
                                }
                            )
                            continue

                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'].append(
                            from_lane.number() + 1)
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'].append(
                            to_lane.number() + 1)
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'].append(
                            {
                                'center': self.get_coo_list([lane_info['center_vertices'][-1], lanes_info[successor_id]['center_vertices'][0]]),
                                'left': self.get_coo_list([lane_info['left_vertices'][-1], lanes_info[successor_id]['left_vertices'][0]]),
                                'right': self.get_coo_list([lane_info['right_vertices'][-1], lanes_info[successor_id]['right_vertices'][0]]),
                            }
                        )  # 注意连接线方向
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['infos'].append(
                            {
                                "predecessor_id": predecessor_id,
                                "successor_id": successor_id,
                                'junction': False,
                            }
                        )

    def convert_junction(self, roads_info, lanes_info, connector_mapping, road_mapping, tess_lane_type, error_junction):
        # 仅交叉口
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] == -1:
                continue
            for section_id, section_info in road_info.get('sections', {}).items():
                # 获取路口的所有连接关系
                for lane_id, lane_info in section_info["lanes"].items():
                    # TODO 如果交叉口前后也连向交叉口，此时交叉口路段并未创建，会导致连接被忽略
                    if LANE_TYPE_MAPPING.get(lane_info['type']) != tess_lane_type:
                        continue  # 路段类型匹配失败，跳过
                    for predecessor_id in lane_info['predecessor_ids']:
                        is_true, from_road_id, from_section_id, from_lane_id, _ = get_inter(predecessor_id, roads_info)
                        if not (is_true and from_road_id in road_mapping.keys()):
                            continue

                        from_section = road_mapping[from_road_id].section(from_section_id)
                        from_link = from_section and from_section.tess_link(from_lane_id, 'from')
                        from_lane = from_section and from_section.tess_lane(from_lane_id, 'from')

                        for successor_id in lane_info["successor_ids"]:
                            is_true, to_road_id, to_section_id, to_lane_id, _ = get_inter(successor_id, roads_info)
                            if not (is_true and to_road_id in road_mapping.keys()):  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                                continue

                            to_section = road_mapping[to_road_id].section(to_section_id)
                            to_link = to_section and to_section.tess_link(to_lane_id, 'to')
                            to_lane = to_section and to_section.tess_lane(to_lane_id, 'to')

                            if not (from_link and from_lane and to_link and to_lane):
                                continue
                            # 检查车道类型是否异常
                            if from_lane.actionType() != to_lane.actionType():
                                error_junction.append(
                                    {
                                        "from_link_id": from_link.id(),
                                        "from_lane_number": from_lane.number() + 1,
                                        "from_lane_type": from_lane.actionType(),
                                        "to_link_id": to_link.id(),
                                        "to_lane_number": to_lane.number() + 1,
                                        "to_lane_type": from_lane.actionType(),
                                        "message": "连接段前后车道类型不同",
                                    }
                                )
                                continue

                            # TODO 交叉口可能产生自连接，记录并跳过（连接发生在同一路段时，必须保证是同一个section）
                            if from_road_id == to_road_id and from_section_id != to_section_id:
                                error_junction.append(
                                    {
                                        "from_link_id": from_link.id(),
                                        "from_lane_number": from_lane.number() + 1,
                                        "from_lane_type": from_lane.actionType(),
                                        "to_link_id": to_link.id(),
                                        "to_lane_number": to_lane.number() + 1,
                                        "to_lane_type": from_lane.actionType(),
                                        "message": "车道连接信息错误",
                                    }
                                )
                                continue

                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'].append(
                                from_lane.number() + 1)
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'].append(
                                to_lane.number() + 1)

                            # 用前后车道的首尾坐标替换原有首尾坐标
                            center_connector_vertices = lanes_info[predecessor_id]['center_vertices'][-1:] + \
                                                 lane_info['center_vertices'][1:-1] + \
                                                 lanes_info[successor_id]['center_vertices'][:1]
                            left_connector_vertices = lanes_info[predecessor_id]['left_vertices'][-1:] + \
                                                      lane_info['left_vertices'][1:-1] + \
                                                      lanes_info[successor_id]['left_vertices'][:1]
                            right_connector_vertices = lanes_info[predecessor_id]['right_vertices'][-1:] + \
                                                      lane_info['right_vertices'][1:-1] + \
                                                      lanes_info[successor_id]['right_vertices'][:1]
                            connector_vertices = {
                                    "center": self.get_coo_list(center_connector_vertices),
                                    "left": self.get_coo_list(left_connector_vertices),
                                    "right": self.get_coo_list(right_connector_vertices),
                                }
                            # connector_vertices = lane_info['center_vertices']
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'].append(
                                connector_vertices
                            )
                                # self.get_coo_list(connector_vertices))  # 注意连接线方向
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['infos'].append(
                                {
                                    "predecessor_id": predecessor_id,
                                    "successor_id": successor_id,
                                    "lane_id": lane_info["name"],
                                    "connector_vertices": connector_vertices,
                                    'junction': True,
                                    "from_link": from_link,
                                    "to_link": to_link,
                                }
                            )

    def create_connects(self, netiface, connector_mapping):
        # 创建所有的连接关系
        for link_id, link_info in connector_mapping.items():
            from_link_id = int(link_id.split('-')[0])
            to_link_id = int(link_id.split('-')[1])
            lFromLaneNumber = link_info['lFromLaneNumber']
            lToLaneNumber = link_info['lToLaneNumber']
            lanesWithPoints3 = link_info['lanesWithPoints3']

            # 源数据建立连接
            if lanesWithPoints3:
                netiface.createConnector3DWithPoints(from_link_id, to_link_id,
                                                   lFromLaneNumber, lToLaneNumber,
                                                   lanesWithPoints3, f"{from_link_id}-{set(lFromLaneNumber)}-{to_link_id}-{set(lToLaneNumber)}")
            # TESS 自动计算，建立连接
            else:
                netiface.createConnector(from_link_id, to_link_id, lFromLaneNumber, lToLaneNumber)

    def get_coo_list(self, vertices):
        x_move, y_move = self.xy_move  #self.xy_move
        temp_list = []
        for index in range(0, len(vertices)):
            vertice = vertices[index]
            temp_list.append(QVector3D(m2p((vertice[0] - x_move)), m2p(-(vertice[1] - y_move)), m2p(vertice[2])))

        return temp_list
