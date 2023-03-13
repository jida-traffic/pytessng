# -*- coding: utf-8 -*-
import collections
import os
import csv
import numpy as np

from pathlib import Path
from DockWidget import *
from PySide2.QtWidgets import *
from Tessng import *
from threading import Thread
from xml.dom import minidom
from tessng2opendrive.create_node import Doc
from tessng2opendrive.tess2xodr import Junction, Connector, Road
from opendrive2tessng.main import main as TessNetwork
from pytessng.utils.functions import qtpoint2point, point2qtpoint
from pytessng.utils.functions import AdjustNetwork


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
        self.ui.btnJoinLink.clicked.connect(self.joinLink)
        self.ui.btnSplitLink.clicked.connect(self.splitLink)

    def splitLink(self, info):
        iface = tngIFace()
        netiface = iface.netInterface()

        if not netiface.linkCount():
            return

        xodrSuffix = "OpenDrive Files (*.csv)"
        dbDir = os.fspath(Path(__file__).resolve().parent / "Data")
        file_path, filtr = QFileDialog.getOpenFileName(self, "打开文件", dbDir, xodrSuffix)
        if not file_path:
            return
        adjust_obj = AdjustNetwork(netiface)
        message = adjust_obj.split_link(file_path)
        if message and isinstance(message, str):
            QMessageBox.warning(None, "提示信息", message)
        return

    def joinLink(self, info):
        iface = tngIFace()
        netiface = iface.netInterface()

        if not netiface.linkCount():
            return

        adjust_obj = AdjustNetwork(netiface)
        message = adjust_obj.join_link()
        if message and isinstance(message, str):
            QMessageBox.warning(None, "提示信息", message)
        return

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
