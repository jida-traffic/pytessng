# -*- coding: utf-8 -*-
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
        self.ui.btnAdjustNetwork.clicked.connect(self.adjustNetwork)
        self.ui.btnShowXodr.clicked.connect(self.showXodr)

    def adjustNetwork(self, info):
        iface = tngIFace()
        netiface = iface.netInterface()

        if not netiface.linkCount():
            return

        # TODO 合并路段
        roads = {}
        class Road:
            def __init__(self):
                self.id = None
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
            last_road.next_links.append(next_link)
            last_road.connectors.append(connector)

            next_road.link = next_link
            next_road.last_links.append(last_link)
            next_road.connectors.append(connector)

            roads[next_link.id()] = next_road
            roads[last_link.id()] = last_road


        def get_chain_by_next(road, link_group: list):
            if len(road.next_links) != 1:
                # 有且仅有一个下游，才可以继续延伸
                return
            next_link = road.next_links[0]
            next_link_id = next_link.id()
            next_road = roads[next_link.id()]
            # 判断下游 link 是否有且仅有 1 个上游，且车道数与当前link一致，若一致，加入链路并继续向下游寻找
            if len(next_road.last_links) == 1 and road.link.laneCount() == next_road.link.laneCount():
                link_group.append(next_link_id)
                # if len(road.next_links) == 1:
                #     # 如果下游路段也只有一个下游，可以继续向下寻找
                get_chain_by_next(next_road, link_group)
            return

        def get_chain_by_last(road, link_group: list):
            if len(road.last_links) != 1:
                # 有且仅有一个上游，才可以继续延伸
                return
            last_link = road.last_links[0]
            last_link_id = last_link.id()
            last_road = roads[last_link.id()]
            # 判断上游 link 是否有且仅有 1 个下游，且车道数与当前link一致，若一致，加入链路并继续向上游寻找
            if len(last_road.next_links) == 1 and road.link.laneCount() == last_road.link.laneCount():
                link_group.insert(0, last_link_id)
                get_chain_by_last(last_road, link_group)
            return

        link_groups = []
        exist_links = []
        for link_id, road in roads.items():
            # 已经进行过查找的 link 不需要再次遍历
            if link_id in exist_links:
                continue
            link_group = [link_id]
            get_chain_by_next(road, link_group)
            get_chain_by_last(road, link_group)

            link_groups.append(link_group)
            exist_links += link_group
            print(link_group)
        # 判断是否有路段进行过重复查询，如果有，说明逻辑存在漏洞
        print(len(exist_links), len(set(exist_links)))
        print(exist_links)

        # TODO 根据信息做路网调整


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
                # # 为所有的连接面域创建road，关联至 junction
                connecors.append(Connector(connector, junction))
                # 为所有的 车道连接创建独立的road，关联至 junction
                # for laneConnector in connector.laneConnectors():
                #     connecors.append(Connector(connector, junction))

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
        if netFilePath:
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
        点击按钮，绘制路网
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


        # 简单绘制路网走向
        from matplotlib import pyplot as plt
        for value in self.network.network_info['roads_info'].values():
            for points in value['road_points'].values():
                x = [i['position'][0] for i in points['right_points']]
                # x = [point['right_points'][['position']][0] for point in points]
                y = [i['position'][1] for i in points['right_points']]
                plt.plot(x, y)
        plt.show()

        # 打开新底图
        iface = tngIFace()
        netiface = iface.netInterface()
        attrs = netiface.netAttrs()
        if attrs is None or attrs.netName() != "PYTHON 路网":
            netiface.setNetAttrs("PYTHON 路网", "OPENDRIVE", otherAttrsJson=self.network.network_info["header_info"])

        error_junction = self.network.create_network(tess_lane_types, netiface)
        message = "\n".join([str(i) for i in error_junction])

        # 打印这一段
        # from matplotlib import pyplot as plt
        # all_points = [netiface.findLink(1).centerBreakPoint3Ds(),
        #                netiface.findLink(1).leftBreakPoint3Ds(),
        #                netiface.findLink(1).rightBreakPoint3Ds(),
        #                netiface.links()[0].lanes()[0].leftBreakPoint3Ds(),
        #                netiface.links()[0].lanes()[0].rightBreakPoint3Ds(),
        #                netiface.links()[0].lanes()[0].centerBreakPoint3Ds()]
        # for index in range(len(all_points)):
        #     points = all_points[index]
        #     plt.plot([_.x() for _ in points], [-_.y() for _ in points], color='g')
        #     plt.show()

        self.ui.txtMessage2.setText(f"{message}")
        is_show = bool(error_junction)
        self.ui.text_label_2.setVisible(is_show)
        self.ui.txtMessage2.setVisible(is_show)
        # QMessageBox.warning(None, "仿真提醒", "如需仿真, 请保存为tess文件后重新打开")

        # return
        # # 路网绘制成功后，写入xodr文件
        # links = netiface.links()
        # print(len(links))
        # roads = []
        # from tess2xodr import Road
        # for link in links:
        #     roads.append(Road(link))
        #
        # from create_node import create_doc
        # doc = create_doc(roads)
        # # 开始写xml文档
        # fp = open('Data/test.xodr', 'w')
        # doc.writexml(fp, indent='\t', addindent='\t', newl='\n', encoding="utf-8")


if __name__ == '__main__':
    app = QApplication()
    win = TESS_API_EXAMPLE()
    win.show()
    app.exec_()
