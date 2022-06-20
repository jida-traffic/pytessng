# -*- coding: utf-8 -*-

import os
from pathlib import Path
import sys

from DockWidget import *
from Tessng import *
from utils import Network


class TESS_API_EXAMPLE(QMainWindow):
    def __init__(self, parent = None):
        super(TESS_API_EXAMPLE, self).__init__(parent)
        self.ui = Ui_TESS_API_EXAMPLEClass()
        self.ui.setupUi(self)
        self.createConnect()
        self.xodr = None
        self.network = None

    def createConnect(self):
        self.ui.btnOpenNet.clicked.connect(self.openNet)
        self.ui.btnStartSimu.clicked.connect(self.startSimu)
        self.ui.btnPauseSimu.clicked.connect(self.pauseSimu)
        self.ui.btnStopSimu.clicked.connect(self.stopSimu)
        self.ui.btnShowXodr.clicked.connect(self.showXodr)

    def openNet(self):
        iface = tngIFace()
        if not iface:
            return
        if iface.simuInterface().isRunning():
            QMessageBox.warning(None, "提示信息", "请先停止仿真，再打开路网")
            return
        custSuffix = "TESSNG Files (*.tess);;TESSNG Files (*.backup);;OpenDrive Files (*.xodr)"
        dbDir = os.fspath(Path(__file__).resolve().parent / "Data")
        selectedFilter = "TESSNG Files (*.xodr)"
        options = QFileDialog.Options(0)
        netFilePath, filtr = QFileDialog.getOpenFileName(self, "打开文件", dbDir, custSuffix, selectedFilter, options)
        print(netFilePath)
        if netFilePath:
            if netFilePath.endswith('xodr'):
                self.xodr = netFilePath
                self.network = Network(netFilePath)
                # 代表TESS NG的接口
                # iface = tngIFace()
                # 代表TESS NG的路网子接口
                # netiface = iface.netInterface()
                # from utils import get_coo_list
            else:
                iface.netInterface().openNetFle(netFilePath)


    def startSimu(self):
        iface = tngIFace()
        if not iface:
            return
        if not iface.simuInterface().isRunning() or iface.simuInterface().isPausing():
            iface.simuInterface().startSimu()

    def pauseSimu(self):
        iface = tngIFace()
        if not iface:
            return
        if iface.simuInterface().isRunning():
            iface.simuInterface().pauseSimu()

    def stopSimu(self):
        iface = tngIFace()
        if not iface:
            return
        if iface.simuInterface().isRunning():
            iface.simuInterface().stopSimu()

    def showRunInfo(self, runInfo):
        self.ui.txtMessage.clear()
        self.ui.txtMessage.setText(runInfo)

    def showXodr(self, ewwe):
        if not self.xodr:
            return
        # 代表TESS NG的接口
        self.network.create_network()
        # 代表TESS NG的路网子接口
        # netiface = iface.netInterface()
        # from utils import get_coo_list
        # link_point = [(i, 0) for i in range(100)]
        # lane_points = {
        #     'right': [(i, 0) for i in range(100)],
        #     'center': [(i, 1) for i in range(100)],
        #     'left': [(i, 2) for i in range(100)],
        # }
        # lCenterLinePoint = get_coo_list(link_point)
        # lanesWithPoints = [
        #     {
        #         'left': get_coo_list(lane['left']),
        #         'center': get_coo_list(lane['center']),
        #         'right': get_coo_list(lane['right']),
        #     } for lane in [lane_points]
        # ]
        # netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints, f"_right")


if __name__ == '__main__':
    app = QApplication()
    win = TESS_API_EXAMPLE()
    win.show()
    app.exec_()
