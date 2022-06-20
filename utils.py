import collections
import copy

from PySide2.QtCore import QPointF
from Tessng import m2p, tngIFace
from config import *


def get_section_points(section_breakpoints, section_info, lengths, lane_ids):
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
    section_points = get_section_points(section_breakpoints, section_info, lengths, lane_ids)
    return section_points


def get_section_childs(section_info, lengths, direction):
    # 分为左右车道，同时过滤tess规则下不同的车道类型
    if direction == 'left':
        lane_ids = [lane_id for lane_id in section_info['lanes'].keys() if lane_id > 0 and lane_id in section_info["tess_lane_ids"]]
    else:
        lane_ids = [lane_id for lane_id in section_info['lanes'].keys() if lane_id < 0 and lane_id in section_info["tess_lane_ids"]]
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


class Section:
    def __init__(self, road_id, section_id, lane_ids: list):
        self.road_id = road_id
        self.id = section_id
        # if road_id == 2 and section_id == 2:
        #     lane_ids.remove(-5)

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
        # for link_info in obj:
        #     link = link_info['link']
        #     lane_ids = link_info['lane_ids']
        #     index = 0
        #     for lane in link.lanes():  # tess 的车道列表是有序的
        #         self.lane_mapping[self.left_lane_ids[index]] = lane
        #         index += 1
        for link_info in obj:
            link = link_info['link']
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
        # is_t = False
        for link_info in obj:
            link = link_info['link']
            lane_ids = link_info['lane_ids']
            index = 0
            for lane in link.lanes():
                link_info[lane_ids[index]] = lane
                index += 1

        self._right_link = obj

    # def set_lanes(self, lane_ids):

    def tess_lane(self, lane_id, type):
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

    def tess_link(self, lane_id, type):
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


def get_inter(string):
    inter_list = []
    is_true = True
    for i in string.split('.'):
        try:
            inter_list.append(int(i))
        except:
            inter_list.append(None)
            is_true = False
    return [is_true, *inter_list]


# 为 child 间创建链接
def connect_childs(links, connector_mapping):
    for index in range(len(links) - 1):
        from_link_info = links[index]
        to_link_info = links[index+1]
        from_link = from_link_info['link']
        to_link = to_link_info['link']

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


class Network:
    def __init__(self, filepath, filter_types=None, step_length=None):
        self.filepath = filepath
        self.step_length = step_length or 0.5
        # 定义静态文件及所处位置文件夹
        # file_name = '第I类路网'
        # filter_types = ["driving", "onRamp", "offRamp", "exit", "entry"]  # 一般用于机动车行驶的车道
        self.filter_types = filter_types or ["driving", "biking", "parking", "onRamp", "offRamp", "exit", "entry", "connectingRamp"]
        self.xy_limit = None  # x1,x2,y1,y2
        self.convert_network()


    def convert_network(self):
        from opendrive_info.main import main
        header_info, roads_info, lanes_info = main(self.filepath, self.filter_types, step_length=self.step_length)
        # print(self.header_info, self.roads_info, self.lanes_info)
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] == None:
                road_info['junction_id'] = -1
            # 记录 坐标点的极值
            for section_id, points in road_info['road_points'].items():
                for point in points['points']:
                    position = point['position']
                    if self.xy_limit is None:
                        self.xy_limit = [position[0], position[0], position[1], position[1]]
                    else:
                        self.xy_limit[0] = min(self.xy_limit[0], position[0])
                        self.xy_limit[1] = max(self.xy_limit[1], position[0])
                        self.xy_limit[2] = min(self.xy_limit[2], position[1])
                        self.xy_limit[3] = max(self.xy_limit[3], position[1])


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
        self.header_info, self.roads_info, self.lanes_info = header_info, roads_info, lanes_info
        print("convert done")


    def create_network(self, tess_lane_types=['机动车道', '非机动车道']):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # TODO 无法实时设置场景大小
        if self.xy_limit:
            netiface.setSceneSize(abs(self.xy_limit[0] - self.xy_limit[1]), abs(self.xy_limit[2] - self.xy_limit[3]))  # 华为路网

        # 如果后续tess在同一路段中存在不同类型的车道，tess_lane_types需要做成列表嵌套
        error_junction = []

        # 不同类型的车道建立不同的路段
        for tess_lane_type in tess_lane_types:
            # 会改变数据结构，所以创建新的数据备份
            roads_info = copy.deepcopy(self.roads_info)
            lanes_info = copy.deepcopy(self.lanes_info)

            def default_dict():
                return {
                    'lFromLaneNumber': [],
                    'lToLaneNumber': [],
                    'lanesWithPoints3': [],
                    'infos': [],
                }
            connector_mapping = collections.defaultdict(default_dict)
            for road_id, road_info in roads_info.items():
                for section_id, section_info in road_info['sections'].items():
                    section_info['tess_lane_ids'] = []
                    for lane_id, lane_info in section_info['lanes'].items():
                        if lane_type_mapping[lane_info['type']] == tess_lane_type:
                            section_info['tess_lane_ids'].append(lane_id)

                    lengths = road_info['road_points'][section_id]['lengths']
                    section_info['left_points'] = get_section_childs(section_info, lengths, 'left')
                    section_info['right_points'] = get_section_childs(section_info, lengths, 'right')
            road_mapping = self.create_links(netiface, roads_info, connector_mapping)
            self.convert_link_connect(roads_info, lanes_info, connector_mapping, road_mapping, tess_lane_type, error_junction)
            self.convert_junction(roads_info, lanes_info, connector_mapping, road_mapping, tess_lane_type, error_junction)
            self.create_connects(netiface, connector_mapping)
        print(error_junction)


    def create_links(self, netiface, roads_info, connector_mapping):
        # 创建基础路段,数据原因，不考虑交叉口
        road_mapping = dict()
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] != -1:
                continue  # 先行创建所有的基本路段
            tess_road = Road(road_id)
            for section_id, section_info in road_info['sections'].items():

                points = road_info['road_points'][section_id]['points']

                left_childs = section_info['left_points']
                right_childs = section_info['right_points']

                tess_section = Section(road_id, section_id, section_info['tess_lane_ids'])
                tess_road.sections.append(tess_section)

                # 存在左车道
                if max(section_info['tess_lane_ids']) > 0:
                    # 对section分段
                    left_links = []
                    childs = left_childs #记录了所有的路段(断点)
                    for index in range(len(childs)):
                        child = childs[index]
                        start_index, end_index = child['start'], child['end'] + 1
                        land_ids = sorted(child["point"][0]['lanes'].keys(), reverse=True)
                        lCenterLinePoint = self.get_coo_list([point["position"] for point in points][::-1][start_index:end_index])
                        lanesWithPoints = [
                            {
                                'left': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['left_vertices'][start_index:end_index]),
                                'center': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['center_vertices'][start_index:end_index]),
                                'right': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['right_vertices'][start_index:end_index]),
                            }
                            for lane_id in land_ids  # if roads_info[road_id]['lanes'][lane_id]['type']=='driving'
                        ]
                        link_obj = netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints,
                                                                               f"{road_id}_{section_id}_{index}_left")
                        left_links.append(
                            {
                                'link': link_obj,
                                'lane_ids': land_ids,
                            }
                        )

                    tess_section.left_link = left_links
                    connect_childs(tess_section.left_link, connector_mapping)
                    # return
                # 存在右车道
                if min(section_info['tess_lane_ids']) < 0:
                    # sectionChild = Child(right_childs)
                    # sectionChild.covert_network()
                    # childs = sectionChild.childs
                    right_links = []
                    childs = right_childs
                    # 车道id为负，越小的越先在tess中创建
                    # land_ids = sorted(lane_section_info['right'], reverse=False)
                    for index in range(len(childs)):
                        child = childs[index]
                        start_index, end_index = child['start'], child['end'] + 1
                        land_ids = sorted(child["point"][0]['lanes'].keys(), reverse=False)
                        lCenterLinePoint = self.get_coo_list(
                            [point["position"] for point in points][start_index:end_index])

                        lanesWithPoints = [
                            {
                                'left': self.get_coo_list(road_info['sections'][section_id]["lanes"][lane_id]['left_vertices'][start_index:end_index]),
                                'center': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['center_vertices'][start_index:end_index]),
                                'right': self.get_coo_list(
                                    road_info['sections'][section_id]["lanes"][lane_id]['right_vertices'][start_index:end_index]),
                            }
                            for lane_id in land_ids  # if roads_info[road_id]['lanes'][lane_id]['type']=='driving'
                        ]

                        link_obj = netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints,
                                                                     f"{road_id}_{section_id}_{index}_right")
                        right_links.append(
                            {
                                'link': link_obj,
                                'lane_ids': land_ids,
                            }
                        )
                        # right_links.append(netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints,
                        #                                                             f"{road_id}_{section_id}_{index}_right"))
                    tess_section.right_link = right_links
                    connect_childs(tess_section.right_link, connector_mapping)
                road_mapping[road_id] = tess_road
        return road_mapping


    def convert_link_connect(self, roads_info, lanes_info, connector_mapping, road_mapping, tess_lane_type, error_junction):
        # 创建所有的连接段,交叉口本身不作为车道，直接生成连接段
        # 多条车道属于一个road
        link_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] == -1]
        junction_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] != -1]
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] != -1:
                continue

            # lane_sections 保存基本信息，sections 保存详情
            for section_id, section_info in road_info['sections'].items():
                # 路段间的连接段只向后连接,本身作为前路段(向前也一样，会重复一次)
                for lane_id in section_info["tess_lane_ids"]:
                    lane_info = section_info['lanes'][lane_id]
                    # 路段类型匹配失败，跳过 TODO 需确保不同类型的车道不会连接
                    if lane_type_mapping[lane_info['type']] != tess_lane_type:
                        continue
                    # 633 路段，L18（-） 只有两个后续车道连接？？？ 已确认，yes
                    predecessor_id = lane_info['name']

                    # 为了和交叉口保持一致，重新获取一次相关信息
                    is_true, from_road_id, from_section_id, from_lane_id, _ = get_inter(predecessor_id)

                    if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1', 需要清除（上一车道宽度归零，不会连接到下一车道）
                        continue

                    from_section = road_mapping[from_road_id].section(from_section_id)
                    from_link = from_section.tess_link(from_lane_id, 'from')
                    from_lane = from_section.tess_lane(from_lane_id, 'from')
                    if not (from_link and from_lane):
                        # 如果车道在此处宽度归零，是不会连接到下一车道的
                        continue

                    for successor_id in lane_info["successor_ids"]:
                        is_true, to_road_id, to_section_id, to_lane_id, _ = get_inter(successor_id)
                        if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                            continue
                        if to_road_id not in link_road_ids:  # 只针对性的创建路段间的连接
                            continue

                        to_section = road_mapping[to_road_id].section(to_section_id)
                        to_link = to_section.tess_link(to_lane_id, 'to')
                        to_lane = to_section.tess_lane(to_lane_id, 'to')

                        if from_lane.actionType() != to_lane.actionType():
                            error_junction.append(
                                {
                                    "link": f"{from_link.id()}-{to_link.id()}",
                                    "from": from_lane.number() + 1,
                                    "to": to_lane.number() + 1,
                                    "info": f"{from_lane.actionType()}-{to_lane.actionType()}"

                                }
                            )
                            continue

                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'].append(
                            from_lane.number() + 1)
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'].append(
                            to_lane.number() + 1)
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'].append(
                            self.get_coo_list([lane_info['center_vertices'][-1],
                                          lanes_info[successor_id]['center_vertices'][0]]))  # 注意连接线方向
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
            for section_id, section_info in road_info['sections'].items():
                # 获取路口的所有连接关系
                for lane_id, lane_info in section_info["lanes"].items():
                    if lane_type_mapping[lane_info['type']] != tess_lane_type:
                        continue  # 路段类型匹配失败，跳过
                    for predecessor_id in lane_info['predecessor_ids']:
                        is_true, from_road_id, from_section_id, from_lane_id, _ = get_inter(predecessor_id)
                        if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                            continue

                        from_section = road_mapping[from_road_id].section(from_section_id)
                        from_link = from_section.tess_link(from_lane_id, 'from')
                        from_lane = from_section.tess_lane(from_lane_id, 'from')

                        for successor_id in lane_info["successor_ids"]:
                            is_true, to_road_id, to_section_id, to_lane_id, _ = get_inter(successor_id)
                            if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                                continue

                            to_section = road_mapping[to_road_id].section(to_section_id)
                            to_link = to_section.tess_link(to_lane_id, 'to')
                            to_lane = to_section.tess_lane(to_lane_id, 'to')
                            # 检查车道类型是否异常
                            if from_lane.actionType() != to_lane.actionType():
                                error_junction.append(
                                    {
                                        "link": f"{from_link.id()}-{to_link.id()}",
                                        "from": from_lane.number() + 1,
                                        "to": to_lane.number() + 1,
                                        "info": f"{from_lane.actionType()}-{to_lane.actionType()}"
                                    }
                                )
                                continue

                            # TODO 交叉口可能产生自连接，记录并跳过
                            if from_road_id == to_road_id and from_section_id != to_section_id:
                                error_junction.append(
                                    {
                                        "lane": lane_info['name'],
                                        "predecessor": predecessor_id,
                                        "successor": successor_id,
                                        'tess_lane_type': tess_lane_type,
                                    }
                                )
                                continue

                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'].append(
                                from_lane.number() + 1)
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'].append(
                                to_lane.number() + 1)

                            # 用前后车道的首尾坐标替换原有首尾坐标
                            connector_vertices = lanes_info[predecessor_id]['center_vertices'][-1:] + \
                                                 lane_info['center_vertices'][1:-1] + \
                                                 lanes_info[successor_id]['center_vertices'][:1]
                            # connector_vertices = lane_info['center_vertices']
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'].append(
                                self.get_coo_list(connector_vertices))  # 注意连接线方向
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

            types = set(i['junction'] for i in link_info['infos'])
            if True in types and False in types:
                link_type = 'all'
            elif True in types:
                link_type = 'junction'
            else:
                link_type = 'link'

            # 源数据建立连接
            if lanesWithPoints3:
                netiface.createConnectorWithPoints(from_link_id, to_link_id,
                                               lFromLaneNumber, lToLaneNumber,
                                               lanesWithPoints3, f"{from_link_id}-{to_link_id}-{link_type}")
            # TESS 自动计算，建立连接
            else:
                netiface.createConnector(from_link_id, to_link_id, lFromLaneNumber, lToLaneNumber)

    def get_coo_list(self, vertices):
        # TODO 路段线与车道线的密度保持一致
        list1 = []
        for index in range(0, len(vertices), 1):
            vertice = vertices[index]
            x_move, y_move = sum(self.xy_limit[:2]) / 2, sum(self.xy_limit[2:]) / 2 if self.xy_limit else (0, 0)
            list1.append(QPointF(m2p(vertice[0] - x_move), m2p(-(vertice[1] - y_move))))
        return list1
