# -*- coding: utf-8 -*-
import os

from pathlib import Path
from DockWidget import *
from PySide2.QtWidgets import QFileDialog, QMessageBox
from opendrive2tess.main import main as TessNetwork
from PySide2.QtWidgets import *
from Tessng import *
from threading import Thread
from shutil import copyfile


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
        # self.ui.btnStartSimu.clicked.connect(self.startSimu)
        # self.ui.btnPauseSimu.clicked.connect(self.pauseSimu)
        # self.ui.btnStopSimu.clicked.connect(self.stopSimu)
        self.ui.btnShowXodr.clicked.connect(self.showXodr)

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

            step = float(self.ui.xodrStep.currentText().split(" ")[0])
            self.network = TessNetwork(netFilePath)

            # 主线程连接信号
            my_signal.text_print.connect(self.ui.change_progress)
            # 启动子线程
            context = {
                "signal": my_signal.text_print,
                "pb": pb
            }
            thread = Thread(target=self.network.convert_network, args=(step, None, context))
            thread.start()


    def showXodr(self, info):
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

        # 打开新底图
        iface = tngIFace()
        netiface = iface.netInterface()

        netiface.setNetAttrs("my_", "OpenDrive", otherAttrsJson=self.network.network_info["header_info"])
        error_junction = self.network.create_network(tess_lane_types, netiface)
        message = "\n".join([str(i) for i in error_junction])

        self.ui.txtMessage2.setText(f"{message}")
        is_show = bool(error_junction)
        self.ui.text_label_2.setVisible(is_show)
        self.ui.txtMessage2.setVisible(is_show)

        QMessageBox.warning(None, "仿真提醒", "如需仿真, 请保存为tess文件后重新打开")


if __name__ == '__main__':
    app = QApplication()
    win = TESS_API_EXAMPLE()
    win.show()
    app.exec_()