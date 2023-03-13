import collections
import csv
import numpy as np

from PySide2.QtGui import *
from Tessng import *


def qtpoint2point(qtpoints):
    points = []
    for qtpoint in qtpoints:
        points.append(
            [m2p(qtpoint.x()), - m2p(qtpoint.y()), m2p(qtpoint.z())] if isinstance(qtpoint, QVector3D) else qtpoint
        )
    return points


def point2qtpoint(points):
    qtpoints = []
    for point in points:
        qtpoints.append(
            QVector3D(p2m(point[0]), - p2m(point[1]), p2m(point[2])) if not isinstance(point, QVector3D) else point
        )
    return qtpoints


class Road:
    def __init__(self):
        self.link = None
        self.last_links = []
        self.next_links = []
        self.connectors = []


class AdjustNetwork:
    def __init__(self, netiface):
        self.netiface = netiface
        self.roads = self.calc_connector()

        # 在调整的过程中，旧的link在不断删除，同时新的link被创建，所以需要建立映射关系表
        # connector也有可能在消失，所以不再被记录，通过上下游link获取connector
        self.old_new_link_mapping = {}
        # 初始化映射表,link在调整前后可能存在一对多/多对一关系，所以用 dict&list 记录
        for link in netiface.links():
            self.old_new_link_mapping[link.id()] = [link.id()]

    # 记录全局的连接关系
    def calc_connector(self):
        roads = {}
        for connector in self.netiface.connectors():
            # 上下游不可能为空
            last_link = connector.fromLink()
            next_link = connector.toLink()

            last_road = roads.get(last_link.id(), Road())
            next_road = roads.get(next_link.id(), Road())

            last_road.link = last_link
            last_road.next_links.append(next_link.id())
            last_road.connectors.append(connector)

            next_road.link = next_link
            next_road.last_links.append(last_link.id())
            next_road.connectors.append(connector)

            roads[next_link.id()] = next_road
            roads[last_link.id()] = last_road

        # 记录无连接段的路段
        for link in self.netiface.links():
            if link.id() not in roads:
                road = Road()
                road.link = link
                roads[link.id()] = road
        return roads

    # 计算路段上所有的路段点，车道点
    # 根据已知的信息计算新的断点序列列表
    @staticmethod
    def calc_points(points, indexs_list, ratios):
        last_index = 0
        points = qtpoint2point(points)

        new_points_list = []  # [[] for _ in indexs_list]

        first_point = None
        # 先把初识点全部分配下去
        for _, indexs in enumerate(indexs_list):
            if indexs:
                last_index = indexs[-1]  # 更新计算点
            new_points = [points[index] for index in indexs]
            # 添加首尾点
            if first_point is not None:
                new_points.insert(0, first_point)

            ratio = ratios[_]
            final_point = np.array(points[last_index]) * (1 - ratio) + np.array(points[last_index + 1]) * ratio
            new_points.append(final_point)
            first_point = final_point

            new_points_list.append(new_points)
            # if indexs:
            #     last_index = indexs[-1]  # 更新计算点

        # 添加最后一个路段，第一个点为上一路段计算的终点，第二个点为上一路段所在点序列的下一个点，最后一个点为路段终点
        new_points_list.append([first_point] + points[last_index + 1:])
        new_points_list = [point2qtpoint(i) for i in new_points_list]
        return new_points_list

    def calc_split_parameter(self, link, split_link_info):
        center_points = link.centerBreakPoint3Ds()
        center_points = qtpoint2point(center_points)

        sum_length = 0
        last_x, last_y, last_z = center_points[0]
        lengths = [0] + split_link_info["lengths"]
        for point_index, point in enumerate(center_points):
            x, y, z = point
            distance = np.sqrt((x - last_x) ** 2 + (y - last_y) ** 2)
            last_x, last_y, last_z = x, y, x

            new_sum_length = sum_length + distance
            for split_index, split_length in enumerate(lengths):
                if split_index == 0:
                    continue
                if new_sum_length < lengths[split_index - 1]:
                    continue
                elif new_sum_length >= lengths[split_index - 1] and new_sum_length < lengths[split_index]:
                    # 区间命中
                    split_link_info['index'][split_index - 1].append(point_index)
                    # TODO 区间已经命中，可以 break 了
                # elif sum_length >= lengths[split_index - 1] and new_sum_length > split_length:
                #     # 新点超出范围,计算比例
                #     ratio = (split_length - sum_length) / distance
                #     split_link_info['ratio'][split_index - 1] = ratio  # 此处不需要记录 首点的比例，因为当需要用到首点时，采用上一点的断点计算
                else:  # new_sum_length >= lengths[split_index]
                    # 如果此处并没有 ratio，说明这是第一次被匹配上，需要进行ratio 计算
                    if split_link_info['ratio'][split_index - 1] is None:
                        ratio = (split_length - sum_length) / distance
                        split_link_info['ratio'][split_index - 1] = ratio  # 此处不需要记录 首点的比例，因为当需要用到首点时，采用上一点的断点计算
            sum_length = new_sum_length

        # 计算完成，可以进行分割
        if len(split_link_info['lengths']) != len(split_link_info['index']) or len(split_link_info['lengths']) != len(
                split_link_info['index']):
            raise 1  # 初步判断

    def calc_split_links_info(self, link, split_link_info):
        # 计算新的 link 信息
        indexs_list = split_link_info['index']
        ratios = split_link_info['ratio']
        link_center_points = self.calc_points(link.centerBreakPoint3Ds(), indexs_list, ratios)

        new_links_info = [
            {
                'center': link_center_points[index],
                'name': f"{link.name()}/{index}",
                'lanes': collections.defaultdict(lambda: {
                    'center': [],
                    'left': [],
                    'right': [],
                    'type': '',
                    'attr': {},
                }),
                'old_link_id': link.id(),
            } for index in range(len(indexs_list) + 1)
        ]

        for lane in link.lanes():
            center_points = self.calc_points(lane.centerBreakPoint3Ds(), indexs_list, ratios)
            left_points = self.calc_points(lane.leftBreakPoint3Ds(), indexs_list, ratios)
            right_points = self.calc_points(lane.rightBreakPoint3Ds(), indexs_list, ratios)
            for index in range(len(indexs_list) + 1):  # 被分割后的 link 数量,比分割点数大 1
                new_links_info[index]['lanes'][lane.number()] = {
                    'center': center_points[index],
                    'left': left_points[index],
                    'right': right_points[index],
                    'type': lane.actionType(),
                    'attr': {},
                }
        return new_links_info

    def split_link(self, file_path):
        reader = csv.reader(open(file_path, 'r', encoding='utf-8'))
        next(reader)

        split_links_info = collections.defaultdict(lambda: {'lengths': [], 'index': [], 'ratio': []})
        for row in reader:
            try:
                row = [float(i) for index, i in enumerate(row)]
            except:
                return f"输入数据错误:{row}"

            link_id = int(row[0])
            points_length = sorted(row[1:])
            link = self.netiface.findLink(link_id)
            if not link:
                return f"link: {link_id} 不存在"
            if min(points_length) <= 0 or max(points_length) >= link.length() or len(points_length) != len(
                    set(points_length)):
                return f"link: {row[0]} 长 {link.length()}, 断点长度输入不准确"

            split_links_info[link_id]['lengths'] = points_length
            split_links_info[link_id]['index'] = [[] for _ in points_length]
            split_links_info[link_id]['ratio'] = [None for _ in points_length]

        # 路段有可能发生 合并，切分，所以使用 list 存储最为合理
        old_new_link_mapping = collections.defaultdict(list)
        for link in self.netiface.links():
            old_new_link_mapping[link.id()].append(link.id())

        old_connectors = []
        # 记录原始连接信息
        for link_id in split_links_info.keys():
            # last_link, next_link 都不属于 link_group,所以在过程中可能已经被删除，只能通过id映射获取新的link
            # 可能存在多个上游路段和多个下游路段，需要逐个获取连接段，从而记录连接关系
            old_connectors += self.calc_upstream_connection(link_id)
            old_connectors += self.calc_downstream_connection(link_id)

        all_new_link_info = []
        # 计算新的路段信息
        for link_id, split_link_info in split_links_info.items():
            link = self.netiface.findLink(link_id)
            # 根据 link 实际信息 丰富 切割参数 > split_link_info
            self.calc_split_parameter(link, split_link_info)
            # 获取切割详情，含点序列等基本信息
            new_links_info = self.calc_split_links_info(link, split_link_info)
            all_new_link_info += new_links_info
            # 记录 link 基本信息后移除
            old_link_id = link.id()
            old_new_link_mapping[old_link_id].remove(old_link_id)  # 删除路段前，移除相关的映射关系
            self.netiface.removeLink(link)

        # 根据记录的信息, 集中创建新的路段并更新映射表
        for new_link_info in all_new_link_info:
            # 做路段分割时，原始路段有且仅有一个
            old_link_id = new_link_info['old_link_id']
            new_link_obj = self.create_new_link(new_link_info)
            # 记录进映射表
            old_new_link_mapping[old_link_id].append(new_link_obj.id())

        # 集中创建内部的连接段
        for old_link_id, new_link_ids in old_new_link_mapping.items():
            for index in range(len(new_link_ids) - 1):
                from_link_id = old_new_link_mapping[old_link_id][index]
                to_link_id = old_new_link_mapping[old_link_id][index + 1]
                link_obj = self.netiface.findLink(from_link_id)
                # 被分割的小路段的车道数/车道类型均完全一致，所以随便取一个路段即可
                lanes = [lane.number() + 1 for lane in link_obj.lanes()]
                self.netiface.createConnector(from_link_id, to_link_id, lanes, lanes, f"{from_link_id}-{to_link_id}")

        # 根据记录的信息 批量创建新的连接段
        self.create_all_new_connector(old_connectors, old_new_link_mapping)
        return True

    def join_link(self):
        # TODO 合并路段, 需要添加车道类型判断，后续增加点位自合并的方法
        link_groups = []
        exist_links = []
        for link_id, road in self.roads.items():
            if link_id in exist_links:
                # 已经进行过查找的 link 不需要再次遍历
                continue

            link_group = [road.link]
            self.get_chain_by_next(road, link_group)
            self.get_chain_by_last(road, link_group)

            link_groups.append(link_group)
            exist_links += [i.id() for i in link_group]

        # 判断是否有路段进行过重复查询，如果有，说明逻辑存在漏洞
        if len(exist_links) != len(set(exist_links)):
            return "出现唯一性错误，请联系开发者"

        # 在调整的过程中，旧的link在不断删除，同时新的link被创建，所以需要建立映射关系表，connector也有可能在消失，所以不再被记录，通过上下游link获取connector
        # 初始化映射表
        old_new_link_mapping = collections.defaultdict(list)
        for link in self.netiface.links():
            old_new_link_mapping[link.id()].append(link.id())

        # TODO 根据信息做路网调整, 在调整过程中，未遍历到的 link_group 不会被调整，即不会丢失对象
        # 分步做，先统计原始的连接段信息，方便后续迭代
        old_connectors = []
        for link_group in filter(lambda x: len(x) > 1, link_groups):
            # 记录原始信息，方便后续重新创建路段及连接段
            first_link = link_group[0]
            final_link = link_group[-1]

            # last_link, next_link 都不属于 link_group,所以在过程中可能已经被删除，只能通过id映射获取新的link
            # 可能存在多个上游路段和多个下游路段，需要逐个获取连接段，从而记录连接关系
            old_connectors += self.calc_upstream_connection(first_link.id())
            old_connectors += self.calc_downstream_connection(final_link.id())

        all_new_link_info = []
        # 记录路段合并信息
        for link_group in filter(lambda x: len(x) > 1, link_groups):
            new_link_info = {
                'center': [],
                'name': '',
                'lanes': collections.defaultdict(lambda: {
                    'center': [],
                    'left': [],
                    'right': [],
                    'type': '',
                    'attr': {},
                }),
                'old_link_ids': [i.id() for i in link_group],
            }

            # 先记录id
            for link in link_group:  # 有序的进行点位合并
                # TODO 暂时不记录中间连接段的点序列
                new_link_info['center'] += link.centerBreakPoint3Ds()
                new_link_info['name'] += link.name()
                for lane in link.lanes():
                    lane_number = lane.number()
                    new_link_info['lanes'][lane_number]['center'] += lane.centerBreakPoint3Ds()
                    new_link_info['lanes'][lane_number]['left'] += lane.leftBreakPoint3Ds()
                    new_link_info['lanes'][lane_number]['right'] += lane.rightBreakPoint3Ds()
                    new_link_info['lanes'][lane_number]['type'] = lane.actionType()

                # 记录 link 基本信息后移除
                old_new_link_mapping[link.id()].remove(link.id())
                self.netiface.removeLink(link)
            all_new_link_info.append(new_link_info)

        # 集中创建新的路段并更新映射表
        for new_link_info in all_new_link_info:
            new_link_obj = self.create_new_link(new_link_info)
            # 更新映射表，原本多个旧路段都指向了同一个新路段
            for old_link_id in new_link_info['old_link_ids']:
                old_new_link_mapping[old_link_id].append(new_link_obj.id())

        # 创建新的连接段,
        # 如果某连接段上下游均进行了路段合并，则连接段会被重新重复创建，已被过滤
        self.create_all_new_connector(old_connectors, old_new_link_mapping)

    # 计算路段的上游连接关系
    def calc_upstream_connection(self, link_id):
        road = self.roads[link_id]
        connectors = []
        for last_link_id in road.last_links:
            connector_info = self.get_connector_info(last_link_id, link_id)
            connectors.append(connector_info)
        return connectors

    # 计算路段的下游连接关系
    def calc_downstream_connection(self, link_id):
        road = self.roads[link_id]
        connectors = []
        for next_link_id in road.next_links:
            connector_info = self.get_connector_info(link_id, next_link_id)
            connectors.append(connector_info)
        return connectors

    def get_connector_info(self, from_link_id, to_link_id):
        connector = self.netiface.findConnectorByLinkIds(from_link_id, to_link_id)
        return {
            'from_link_id': from_link_id,
            'to_link_id': to_link_id,
            'connector': [
                (i.fromLane().number(), i.toLane().number())
                for i in connector.laneConnectors()
            ],
            'lanesWithPoints3': [
                {
                    "center": i.centerBreakPoint3Ds(),
                    "left": i.leftBreakPoint3Ds(),
                    "right": i.rightBreakPoint3Ds(),
                }
                for i in connector.laneConnectors()
            ],
        }

    def get_chain_by_next(self, road, link_group: list):
        if len(road.next_links) != 1:
            # 有且仅有一个下游，才可以继续延伸
            return
        next_link_id = road.next_links[0]
        next_link = self.netiface.findLink(next_link_id)
        next_road = self.roads[next_link.id()]
        # 判断下游 link 是否有且仅有 1 个上游，且车道数/车道类型与当前link一致，若一致，加入链路并继续向下游寻找
        if len(next_road.last_links) == 1 and [lane.actionType() for lane in road.link.lanes()] == [
            lane.actionType() for lane in next_road.link.lanes()]:
            link_group.append(next_link)
            self.get_chain_by_next(next_road, link_group)
        return

    # 通过指定路段信息寻找匹配的上下游
    def get_chain_by_last(self, road, link_group: list):
        if len(road.last_links) != 1:
            # 有且仅有一个上游，才可以继续延伸
            return
        last_link_id = road.last_links[0]
        last_link = self.netiface.findLink(last_link_id)
        last_road = self.roads[last_link.id()]
        # 判断上游 link 是否有且仅有 1 个下游，且车道数与当前link一致，若一致，加入链路并继续向上游寻找
        if len(last_road.next_links) == 1 and [lane.actionType() for lane in road.link.lanes()] == [
            lane.actionType() for lane in last_road.link.lanes()]:
            link_group.insert(0, last_link)
            self.get_chain_by_last(last_road, link_group)
        return

    def create_new_link(self, new_link_info):
        new_link_obj = self.netiface.createLink3DWithLanePointsAndAttrs(
            new_link_info['center'],
            [
                {
                    'center': new_link_info['lanes'][k]['center'],
                    'right': new_link_info['lanes'][k]['right'],
                    'left': new_link_info['lanes'][k]['left'],
                } for k in sorted(new_link_info['lanes'])
            ],  # 必须排序
            [new_link_info['lanes'][k]['type'] for k in sorted(new_link_info['lanes'])],
            [new_link_info['lanes'][k]['attr'] for k in sorted(new_link_info['lanes'])],
            new_link_info['name']
        )
        return new_link_obj

    # 根据记录的信息 批量创建新的连接段
    def create_all_new_connector(self, old_connectors, old_new_link_mapping):
        # 如果某连接段上下游均进行了路段合并，则连接段会被重新重复创建，此处进行过滤
        exist_connector = []
        for connector in old_connectors:
            old_from_link_id = connector['from_link_id']
            old_to_link_id = connector['to_link_id']
            new_from_link_id = old_new_link_mapping[old_from_link_id][-1]  # 上游路段取新的link列表的最后一个
            new_to_link_id = old_new_link_mapping[old_to_link_id][0]  # 下游路段取新的link列表的第一个

            connector_name = f'{new_from_link_id}_{new_to_link_id}'
            if connector_name in exist_connector:
                continue
            self.netiface.createConnector3DWithPoints(new_from_link_id,
                                                      new_to_link_id,
                                                      [i[0] + 1 for i in connector['connector']],
                                                      [i[1] + 1 for i in connector['connector']],
                                                      connector['lanesWithPoints3'],
                                                      f"{new_from_link_id}-{new_to_link_id}"
                                                      )
            # 采用默认连接，防止出现连接段不平滑问题
            # netiface.createConnector(new_from_link_id, new_to_link_id, [i[0] + 1 for i in connector['connector']], [i[1] + 1 for i in connector['connector']], f"{new_from_link_id}-{new_to_link_id}")
            exist_connector.append(connector_name)
