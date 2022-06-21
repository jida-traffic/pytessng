# -*- coding: utf-8 -*-
import os
from pathlib import Path

from DockWidget import *
from Tessng import *
from utils.util import Network


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
                step = float(self.ui.xodrStep.currentText())
                self.network = Network(netFilePath, step_length=step)
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

    def showXodr(self, info):
        if not self.network:
            QMessageBox.warning(None, "提示信息", "请先导入xodr路网文件")
            return
        # 代表TESS NG的接口
        step = float(self.ui.xodrStep.currentText())
        tess_lane_types = []
        for xodrCk in self.ui.xodrCks:
            if xodrCk.checkState() == QtCore.Qt.CheckState.Checked:
                tess_lane_types.append(xodrCk.text())
        if not tess_lane_types:
            QMessageBox.warning(None, "提示信息", "请至少选择一种车道类型")
            return
        error_junction = self.network.create_network(tess_lane_types)
        message = "\n".join([str(i) for i in error_junction])
        self.ui.txtMessage.setText(message)


if __name__ == '__main__':
    app = QApplication()
    win = TESS_API_EXAMPLE()
    win.show()
    app.exec_()
