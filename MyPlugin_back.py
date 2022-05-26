# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QDockWidget
from Tessng import *
from MyNet_back import *
from MySimulator import *
from TESS_API_EXAMPLE import *

class MyPlugin(TessPlugin):
    def __init__(self):
        super(MyPlugin, self).__init__()
        self.mNetInf = None
        self.mSimuInf = None
        self.mPySimuInf = None

    def initGui(self):
        # 在TESS NG主界面上增加 QDockWidget对象
        self.mpExampleWindow = TESS_API_EXAMPLE()

        iface = tngIFace()
        win = iface.guiInterface().mainWindow()

        pDockWidget = QDockWidget("自定义与TESS NG交互界面", win)
        pDockWidget.setObjectName("mainDockWidget")
        pDockWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        pDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea)
        pDockWidget.setWidget(self.mpExampleWindow.centralWidget())
        iface.guiInterface().addDockWidgetToMainWindow(Qt.DockWidgetArea(1), pDockWidget)

    def init(self):
        self.initGui()
        self.mNetInf = MyNet()
        self.mSimuInf = MySimulator()
        self.mSimuInf.forRunInfo.connect(self.mpExampleWindow.showRunInfo)

    def projName(self):
        return "projName__"

    def customerNet(self):
        return self.mNetInf

    def customerSimulator(self):
        return self.mSimuInf
