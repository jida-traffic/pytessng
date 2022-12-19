# -*- coding: utf-8 -*-
import collections
import copy
import os

from pathlib import Path
from DockWidget import *
from opendrive2tessng.main import main as TessNetwork
from PySide2.QtWidgets import *
from Tessng import *
from threading import Thread
from xml.dom import minidom
from tessng2opendrive.create_node import Doc
from tessng2opendrive.tess2xodr import Junction, Connector, Road
from utils.util import qtpoint2point, point2qtpoint


class MySignals(QObject):
    # 定义一种信号，因为有文本框和进度条两个类，此处要四个参数，类型分别是： QPlainTextEdit 、 QProgressBar、字符串和整形数字
    # 调用 emit方法发信号时，传入参数必须是这里指定的参数类型
    # 此处也可分开写两个函数，一个是文本框输出的，一个是给进度条赋值的
    text_print = Signal(QProgressBar, int, dict, bool)


class TESS_API_EXAMPLE(QMainWindow):
    def __init__(self, parent=None):
        super(TESS_API_EXAMPLE, self).__init__(parent)
        self.ui = Ui_TESS_API_EXAMPLEClass()
        self.ui.setupUi(self)
        self.createConnect()
        self.xodr = None
        self.network = None

    def createConnect(self):
        self.ui.btnOpenNet.clicked.connect(self.openNet)
        self.ui.btnCreateXodr.clicked.connect(self.createXodr)
        self.ui.btnShowXodr.clicked.connect(self.showXodr)
        self.ui.btnAdjustNetwork.clicked.connect(self.adjustNetwork)
        self.ui.btnSplitLink.clicked.connect(self.btnSplitLink)

    def btnSplitLink(self, info):
        iface = tngIFace()
        netiface = iface.netInterface()

        if not netiface.linkCount():
            return

        # xodrSuffix = "OpenDrive Files (*.csv)"
        # dbDir = os.fspath(Path(__file__).resolve().parent / "Data")
        # file_path, filtr = QFileDialog.getOpenFileName(self, "打开文件", dbDir, xodrSuffix)
        # if not file_path:
        #     return
        file_path = r'C:/Users/yang/Desktop/OD测试/split - 副本.csv'
        # file_path = r'C:/Users/yang/Desktop/OD测试/split.csv'

        import csv
        reader = csv.reader(open(file_path, 'r', encoding='utf-8'))
        next(reader)

        split_links_info = collections.defaultdict(lambda : {'lengths': [], 'index': [], 'ratio': []})
        for row in reader:
            try:
                row = [int(i) for index, i in enumerate(row)]
            except:
                QMessageBox.warning(None, "提示信息", f"输入数据错误:{row}")
                return

            link_id = row[0]
            points_length = sorted(row[1:])
            link = netiface.findLink(link_id)
            if not link:
                QMessageBox.warning(None, "提示信息", f"link: {link_id} 不存在")
                return
            if min(points_length) <= 0 or max(points_length) >= link.length() or len(points_length) != len(set(points_length)):
                QMessageBox.warning(None, "提示信息", f"link: {row[0]} 长 {link.length()}, 断点长度输入不准确")
                return
            split_links_info[link_id]['lengths'] = points_length
            split_links_info[link_id]['index'] = [[] for _ in points_length]
            split_links_info[link_id]['ratio'] = [None for _ in points_length]

        # 路段有可能发生 合并，切分，所以使用 list 存储最为合理
        old_new_link_mapping = collections.defaultdict(list)
        for link in netiface.links():
            old_new_link_mapping[link.id()].append(link.id())


        class Road:
            def __init__(self):
                self.link = None
                self.last_links = []
                self.next_links = []
                self.connectors = []

        roads = {}
        # 记录全局的连接关系
        for connector in netiface.connectors():
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

        new_connectors = []
        # 记录原始连接信息
        for link_id in split_links_info.keys():
            road = roads[link_id]

            connector_info = []
            for last_link_id in road.last_links:
                connector = netiface.findConnectorByLinkIds(last_link_id, link_id)
                connector_info.append(
                    {
                        'from_link_id': last_link_id,
                        'to_link_id': link_id,
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
                )
            for next_link_id in road.next_links:
                connector = netiface.findConnectorByLinkIds(link_id, next_link_id)
                connector_info.append(
                    {
                        'from_link_id': link_id,
                        'to_link_id': next_link_id,
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
                )
            new_connectors.append(connector_info)

        # 在调整的过程中，旧的link在不断删除，同时新的link被创建，所以需要建立映射关系表，connector也有可能在消失，所以不再被记录，通过上下游link获取connector
        old_new_link_mapping = {}
        for link in netiface.links():
            old_new_link_mapping[link.id()] = [link.id()]

        # 计算新的路段信息
        import numpy as np
        for link_id, split_link_info in split_links_info.items():
            link = netiface.findLink(link_id)
            center_points = link.centerBreakPoint3Ds()
            center_points = qtpoint2point(center_points)


            sum_length = 0
            last_x, last_y, last_z = center_points[0]
            lengths = [0] + split_link_info["lengths"]
            for point_index, point in enumerate(center_points):
                x, y, z = point
                distance = np.sqrt((x - last_x) ** 2 + (y - last_y) ** 2)

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

            # 计算路段上所有的路段点，车道点
            # 根据已知的信息计算新的断点序列列表
            def calc_points(points, indexs_list, ratios):
                last_index = 0
                points = qtpoint2point(points)

                new_points_list = []  # [[] for _ in indexs_list]

                first_point = None
                # 先把初识点全部分配下去
                for _, indexs in enumerate(indexs_list):
                    new_points = [points[index] for index in indexs]
                    # 添加首尾点
                    if first_point is not None:
                        new_points.insert(0, first_point)

                    ratio = ratios[_]
                    final_point = np.array(points[last_index]) * (1 - ratio) + np.array(points[last_index + 1]) * ratio
                    new_points.append(final_point)
                    first_point = final_point

                    new_points_list.append(new_points)
                    if indexs:
                        last_index = indexs[-1]  # 更新计算点

                # 添加最后一个路段，第一个点为上一路段计算的终点，第二个点为上一路段所在点序列的下一个点，最后一个点为路段终点
                new_points_list.append([first_point] + points[last_index + 1:])
                new_points_list = [point2qtpoint(i) for i in new_points_list]

                return new_points_list

            # 计算新的 link 信息
            indexs_list = split_link_info['index']
            ratios = split_link_info['ratio']
            link_center_points = calc_points(link.centerBreakPoint3Ds(), indexs_list, ratios)

            new_links_info = [
                {
                    'center': link_center_points[index],
                    'name': '',
                    'lanes': collections.defaultdict(lambda: {
                        'center': [],
                        'left': [],
                        'right': [],
                        'type': '',
                        'attr': {},
                    }),
                } for index in range(len(indexs_list) + 1)
            ]

            for lane in link.lanes():
                center_points = calc_points(lane.centerBreakPoint3Ds(), indexs_list, ratios)
                left_points = calc_points(lane.leftBreakPoint3Ds(), indexs_list, ratios)
                right_points = calc_points(lane.rightBreakPoint3Ds(), indexs_list, ratios)
                # type = lane.actionType()
                # attr = {}
                for index in range(len(indexs_list) + 1):  # 被分割后的 link 数量,比分割点数大 1
                    new_links_info[index]['lanes'][lane.number()] = {
                        'center': center_points[index],
                        'left': left_points[index],
                        'right': right_points[index],
                        'type': lane.actionType(),
                        'attr': {},
                    }

            # 记录 link 基本信息后移除
            old_link_id = link.id()
            old_new_link_mapping[old_link_id].remove(old_link_id)  # 删除路段前，移除相关的映射关系
            netiface.removeLink(link)

            # 删除后立即创建新的路段并更新映射表，集中更新会导致id错乱
            for new_link_info in new_links_info:
                new_link_obj = netiface.createLink3DWithLanePointsAndAttrs(
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

                # 记录进映射表
                old_new_link_mapping[old_link_id].append(new_link_obj.id())

        # for connector in new_connectors:
        #     from_link_id = connector['from_link_id']
        #     to_link_id = connector['to_link_id']
        #     new_from_link_id = old_new_link_mapping[from_link_id][-1]  # 上游路段取新的link列表的最后一个
        #     new_to_link_id = old_new_link_mapping[to_link_id][0]  # 下游路段取新的link列表的第一个

        # 根据记录的信息 批量创建新的连阶段
        exist_connector = []
        for connectors in new_connectors:
            # 一路段可能存在多个上+下游
            for connector in connectors:
                from_link_id = connector['from_link_id']
                to_link_id = connector['to_link_id']
                new_from_link_id = old_new_link_mapping[from_link_id][-1]  # 上游路段取新的link列表的最后一个
                new_to_link_id = old_new_link_mapping[to_link_id][0]  # 下游路段取新的link列表的第一个

                connector_name = f'{new_from_link_id}_{new_to_link_id}'
                if connector_name in exist_connector:
                    continue
                netiface.createConnector3DWithPoints(new_from_link_id,
                                                     new_to_link_id,
                                                     [i[0] + 1 for i in connector['connector']],
                                                     [i[1] + 1 for i in connector['connector']],
                                                     connector['lanesWithPoints3'],
                                                     ""
                                                     )
                exist_connector.append(connector_name)


    def adjustNetwork(self, info):
        iface = tngIFace()
        netiface = iface.netInterface()

        if not netiface.linkCount():
            return

        # TODO 合并路段, 需要添加车道类型判断，后续增加点位自合并的方法
        roads = {}

        class Road:
            def __init__(self):
                self.link = None
                self.last_links = []
                self.next_links = []
                self.connectors = []

        for connector in netiface.connectors():
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

        def get_chain_by_next(road, link_group: list):
            if len(road.next_links) != 1:
                # 有且仅有一个下游，才可以继续延伸
                return
            next_link_id = road.next_links[0]
            next_link = netiface.findLink(next_link_id)
            next_road = roads[next_link.id()]
            # 判断下游 link 是否有且仅有 1 个上游，且车道数/车道类型与当前link一致，若一致，加入链路并继续向下游寻找
            if len(next_road.last_links) == 1 and [lane.actionType() for lane in road.link.lanes()] == [
                lane.actionType() for lane in next_road.link.lanes()]:
                link_group.append(next_link)
                get_chain_by_next(next_road, link_group)
            return

        def get_chain_by_last(road, link_group: list):
            if len(road.last_links) != 1:
                # 有且仅有一个上游，才可以继续延伸
                return
            last_link_id = road.last_links[0]
            last_link = netiface.findLink(last_link_id)
            last_road = roads[last_link.id()]
            # 判断上游 link 是否有且仅有 1 个下游，且车道数与当前link一致，若一致，加入链路并继续向上游寻找
            if len(last_road.next_links) == 1 and [lane.actionType() for lane in road.link.lanes()] == [
                lane.actionType() for lane in last_road.link.lanes()]:
                link_group.insert(0, last_link)
                get_chain_by_last(last_road, link_group)
            return

        link_groups = []
        exist_links = []
        for link_id, road in roads.items():
            if link_id in exist_links:
                # 已经进行过查找的 link 不需要再次遍历
                continue

            link_group = [road.link]
            get_chain_by_next(road, link_group)
            get_chain_by_last(road, link_group)

            link_groups.append(link_group)
            exist_links += [i.id() for i in link_group]

        # 判断是否有路段进行过重复查询，如果有，说明逻辑存在漏洞
        if len(exist_links) != len(set(exist_links)):
            QMessageBox.warning(None, "提示信息", "出现唯一性错误，请联系开发者")
            return

        # 在调整的过程中，旧的link在不断删除，同时新的link被创建，所以需要建立映射关系表，connector也有可能在消失，所以不再被记录，通过上下游link获取connector
        old_new_link_mapping = {}
        for link in netiface.links():
            old_new_link_mapping[link.id()] = link.id()

        # TODO 根据信息做路网调整, 在调整过程中，未遍历到的 link_group 不会被调整，即不会丢失对象
        # 分步做，先统计原始的连接段信息，方便后续迭代
        new_connectors = []
        for link_group in link_groups:
            if len(link_group) == 1:
                continue
            connector_info = []

            # 记录原始信息，方便后续重新创建路段及连接段
            first_link = link_group[0]
            first_road = roads[first_link.id()]
            final_link = link_group[-1]
            final_road = roads[final_link.id()]

            # last_link, next_link 都不属于 link_group,所以在过程中可能已经被删除，只能通过id映射获取新的link
            # 可能存在多个上游路段和多个下游路段，需要逐个获取连接段，从而记录连接关系
            # 计算上游连接信息
            for last_link_id in first_road.last_links:
                connector = netiface.findConnectorByLinkIds(last_link_id, first_link.id())
                connector_info.append(
                    {
                        'from_link_id': last_link_id,
                        'to_link_id': first_link.id(),
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
                )

            # 计算下游连接信息
            for next_link_id in final_road.next_links:
                connector = netiface.findConnectorByLinkIds(final_link.id(), next_link_id)
                connector_info.append(
                    {
                        'from_link_id': final_link.id(),
                        'to_link_id': next_link_id,
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
                )
            new_connectors.append(connector_info)

        # 进行路段合并
        for link_group in link_groups:
            if len(link_group) == 1:
                continue
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
            }

            # 先记录id
            link_group_ids = [i.id() for i in link_group]
            for link in link_group:  # 有序的
                # TODO 暂时不记录中间连接段的点序列
                new_link_info['center'] += link.centerBreakPoint3Ds()
                for lane in link.lanes():
                    lane_number = lane.number()
                    new_link_info['lanes'][lane_number]['center'] += lane.centerBreakPoint3Ds()
                    new_link_info['lanes'][lane_number]['left'] += lane.leftBreakPoint3Ds()
                    new_link_info['lanes'][lane_number]['right'] += lane.rightBreakPoint3Ds()
                    new_link_info['lanes'][lane_number]['type'] = lane.actionType()

                # 记录 link 基本信息后移除
                netiface.removeLink(link)
            # 删除后立即创建新的路段并更新映射表，集中更新会导致id错乱
            new_link_obj = netiface.createLink3DWithLanePointsAndAttrs(
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

            # 更新映射表
            print(new_link_obj.id(), link_group_ids)
            for old_link_id in link_group_ids:
                old_new_link_mapping[old_link_id] = new_link_obj.id()

        # 创建新的连接段,
        # 如果某连接段上下游均进行了路段合并，则连接段会被重新重复创建，已被过滤
        exist_connector = []
        for connectors in new_connectors:
            # 一路段可能存在多个上+下游
            for connector in connectors:
                new_from_id = old_new_link_mapping[connector['from_link_id']]
                new_to_id = old_new_link_mapping[connector['to_link_id']]

                connector_name = f'{new_from_id}_{new_to_id}'
                if connector_name in exist_connector:
                    continue
                netiface.createConnector3DWithPoints(new_from_id,
                                                     new_to_id,
                                                     [i[0] + 1 for i in connector['connector']],
                                                     [i[1] + 1 for i in connector['connector']],
                                                     connector['lanesWithPoints3'],
                                                     ""
                                                     )
                exist_connector.append(connector_name)
        print('OK')

    def createXodr(self, info):
        iface = tngIFace()
        netiface = iface.netInterface()

        if not netiface.linkCount():
            return

        xodrSuffix = "OpenDrive Files (*.xodr)"
        dbDir = os.fspath(Path(__file__).resolve().parent / "Data")
        file_path, filtr = QFileDialog.getSaveFileName(None, "文件保存", dbDir, xodrSuffix)
        if not file_path:
            return

        # 因为1.4 不支持多个前继/后续路段/车道，所以全部使用 junction 建立连接关系
        # 每个连接段视为一个 road，多个 road 组合成一个 junction
        connecors = []
        junctions = []
        for ConnectorArea in netiface.allConnectorArea():
            junction = Junction(ConnectorArea)
            junctions.append(junction)
            for connector in ConnectorArea.allConnector():
                # 为所有的 车道连接创建独立的road，关联至 junction
                for laneConnector in connector.laneConnectors():
                    connecors.append(Connector(laneConnector, junction))

        roads = []
        for link in netiface.links():
            roads.append(Road(link))

        # 路网绘制成功后，写入xodr文件
        doc = Doc()
        doc.init_doc()
        doc.add_junction(junctions)
        doc.add_road(roads + connecors)

        uglyxml = doc.doc.toxml()
        xml = minidom.parseString(uglyxml)
        xml_pretty_str = xml.toprettyxml()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_pretty_str)

    def openNet(self):
        xodrSuffix = "OpenDrive Files (*.xodr)"
        dbDir = os.fspath(Path(__file__).resolve().parent / "Data")

        iface = tngIFace()
        netiface = iface.netInterface()
        if not iface:
            return
        if iface.simuInterface().isRunning():
            QMessageBox.warning(None, "提示信息", "请先停止仿真，再打开路网")
            return

        count = netiface.linkCount()
        if count:
            # 关闭窗口时弹出确认消息
            reply = QMessageBox.question(self, '提示信息', '是否保存数据', QMessageBox.Yes, QMessageBox.No)
            # TODO 保存数据--> 清除数据 --> 打开新文件
            if reply == QMessageBox.Yes:
                netiface.saveRoadNet()

        # custSuffix = "TESSNG Files (*.tess);;TESSNG Files (*.backup);;OpenDrive Files (*.xodr)"
        netFilePath, filtr = QFileDialog.getOpenFileName(self, "打开文件", dbDir, xodrSuffix)
        print(netFilePath)
        if not netFilePath:
            return
        self.xodr = netFilePath
        # 限制文件的再次选择
        self.ui.btnOpenNet.setEnabled(False)
        # 声明线程间的共享变量
        global pb
        global my_signal
        my_signal = MySignals()
        pb = self.ui.pb

        step_length = float(self.ui.xodrStep.currentText().split(" ")[0])
        self.network = TessNetwork(netFilePath)

        # 主线程连接信号
        my_signal.text_print.connect(self.ui.change_progress)
        # 启动子线程
        context = {
            "signal": my_signal.text_print,
            "pb": pb
        }
        filters = None  # list(LANE_TYPE_MAPPING.keys())
        thread = Thread(target=self.network.convert_network, args=(step_length, filters, context))
        thread.start()

    def showXodr(self, info):
        """
        点击按钮，绘制 opendrive 路网
        Args:
            info: None
        Returns:
        """
        if not (self.network and self.network.network_info):
            QMessageBox.warning(None, "提示信息", "请先导入xodr路网文件或等待文件转换完成")
            return

        # 代表TESS NG的接口
        tess_lane_types = []
        for xodrCk in self.ui.xodrCks:
            if xodrCk.checkState() == QtCore.Qt.CheckState.Checked:
                tess_lane_types.append(xodrCk.text())
        if not tess_lane_types:
            QMessageBox.warning(None, "提示信息", "请至少选择一种车道类型")
            return

        # # 简单绘制路网走向
        # from matplotlib import pyplot as plt
        # for value in self.network.network_info['roads_info'].values():
        #     for points in value['road_points'].values():
        #         x = [i['position'][0] for i in points['right_points']]
        #         # x = [point['right_points'][['position']][0] for point in points]
        #         y = [i['position'][1] for i in points['right_points']]
        #         plt.plot(x, y)
        # plt.show()

        # 打开新底图
        iface = tngIFace()
        netiface = iface.netInterface()
        attrs = netiface.netAttrs()
        if attrs is None or attrs.netName() != "PYTHON 路网":
            netiface.setNetAttrs("PYTHON 路网", "OPENDRIVE", otherAttrsJson=self.network.network_info["header_info"])

        error_junction = self.network.create_network(tess_lane_types, netiface)
        message = "\n".join([str(i) for i in error_junction])

        self.ui.txtMessage2.setText(f"{message}")
        is_show = bool(error_junction)
        self.ui.text_label_2.setVisible(is_show)
        self.ui.txtMessage2.setVisible(is_show)


if __name__ == '__main__':
    app = QApplication()
    win = TESS_API_EXAMPLE()
    win.show()
    app.exec_()
