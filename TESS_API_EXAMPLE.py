# -*- coding: utf-8 -*-
import os

from pathlib import Path
from DockWidget import *
from PySide2.QtWidgets import QFileDialog, QMessageBox
from utils.network_utils import Network
from PySide2.QtWidgets import *
from Tessng import *


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
        # self.ui.btnStartSimu.clicked.connect(self.startSimu)
        # self.ui.btnPauseSimu.clicked.connect(self.pauseSimu)
        # self.ui.btnStopSimu.clicked.connect(self.stopSimu)
        self.ui.btnShowXodr.clicked.connect(self.showXodr)

    def openNet(self):
        # custSuffix = "TESSNG Files (*.tess);;TESSNG Files (*.backup);;OpenDrive Files (*.xodr)"
        # dbDir = os.fspath(Path(__file__).resolve().parent / "Data")
        # selectedFilter = "TESSNG Files (*.xodr)"
        # options = QFileDialog.Options(0)
        # netFilePath, filtr = QFileDialog.getOpenFileName(self, "打开文件", dbDir, custSuffix, selectedFilter, options)
        xodrSuffix = "OpenDrive Files (*.xodr)"
        tessSuffix = "Tess Files (*.tess)"
        dbDir = os.fspath(Path(__file__).resolve().parent / "Data")
        temp_file = os.path.join(QApplication.instance().applicationDirPath(), 'Temp', 'Net001.tmp')
        temp_back_file = os.path.join(QApplication.instance().applicationDirPath(), 'Temp', 'Net001_back.tmp')

        iface = tngIFace()
        if not iface:
            return
        if iface.simuInterface().isRunning():
            QMessageBox.warning(None, "提示信息", "请先停止仿真，再打开路网")
            return

        count = iface.netInterface().linkCount()
        if count:
            # 关闭窗口时弹出确认消息
            reply = QMessageBox.question(self, '提示信息', '是否保存数据', QMessageBox.Yes, QMessageBox.No)
            # TODO 保存数据--> 清除数据 --> 打开新文件
            if reply == QMessageBox.Yes:
                # <tess 会更新temp文件，所以选择保存时需要额外处理>，先把tmp文件复制，然后替换,嘴还不要采取这种方式
                from shutil import copyfile
                copyfile(temp_file, temp_back_file)
                iface.netInterface().saveRoadNet()
                copyfile(temp_back_file, temp_file)
            iface.netInterface().openNetFle(temp_file)

        # custSuffix = "TESSNG Files (*.tess);;TESSNG Files (*.backup);;OpenDrive Files (*.xodr)"
        netFilePath, filtr = QFileDialog.getOpenFileName(self, "打开文件", dbDir, xodrSuffix)
        print(netFilePath)
        if netFilePath:
            # if netFilePath.endswith('xodr'):
            self.xodr = netFilePath
            step = float(self.ui.xodrStep.currentText())

            # TODO 添加进度条--主窗口
            self.network = Network(netFilePath, step_length=step, window=self.ui)
            # 导入完成后，部分窗体展示
            self.ui.txtMessage1.setText(f"路网详情\n{str(self.network.network_info)}")
            self.ui.groupBox_2.setVisible(True)
            # else:
            #     iface.netInterface().openNetFle(netFilePath)
        # TODO 插件的展示与隐藏
        # tngPlugin().dockWidget.setVisible(False)


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
        self.ui.txtMessage2.setText(f"异常路段\n{message}")
        if error_junction:
            self.ui.txtMessage2.setVisible(True)
        QMessageBox.warning(None, "仿真提醒", "如需仿真, 请保存为tess文件后重新打开")


if __name__ == '__main__':
    app = QApplication()
    win = TESS_API_EXAMPLE()
    win.show()
    app.exec_()