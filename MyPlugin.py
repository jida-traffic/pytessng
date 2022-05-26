# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QDockWidget
from Tessng import *
from MyNet import *
from MySimulator import *
from TESS_API_EXAMPLE import *

# 用户插件，继承自TessPlugin
class MyPlugin(TessPlugin):
    def __init__(self):
        super(MyPlugin, self).__init__()
        self.mNetInf = None
        self.mSimuInf = None
        # 过载父类方法，在 TESS NG工厂类创建TESS NG对象时调用

    def init(self):
        self.mNetInf = MyNet()
        # self.mSimuInf = MySimulator()
        # self.mSimuInf.signalRunInfo.connect(self.examleWindow.showRunInfo)

    def customerNet(self):
        return self.mNetInf
