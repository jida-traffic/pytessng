# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TESS_API_EXAMPLE.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide2 import QtCore
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_TESS_API_EXAMPLEClass(object):
    def setupUi(self, TESS_API_EXAMPLEClass):
        if not TESS_API_EXAMPLEClass.objectName():
            TESS_API_EXAMPLEClass.setObjectName(u"TESS_API_EXAMPLEClass")
        TESS_API_EXAMPLEClass.resize(262, 735)

        self.centralWidget = QWidget(TESS_API_EXAMPLEClass)
        self.centralWidget.setObjectName(u"centralWidget")
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")


        # 文件选择框
        self.groupBox_1 = QGroupBox(self.centralWidget)
        self.groupBox_1.setObjectName(u"groupBox_1")
        self.verticalLayout_0 = QVBoxLayout(self.groupBox_1)

        xodr_label1 = QLabel()
        xodr_label1.setText("步长选择(请在文件导入前选择)")
        self.xodrStep = QComboBox(self.centralWidget)
        self.xodrStep.addItems(("0.5", "0.1", "1"))
        #     # 导入进度条
        # self.pd = QProgressBar(self.centralWidget)
        # # pd.setLabelText('导入进度')
        # self.pd.setRange(0, 100)  # 进度对话框的范围设定
        # self.pd.setValue(0)
        # # pd.move(pd.x(), pd.y() + 200)
        # # self.pd.show()
        # self.pd_progress = 0
        #
        # def progress_chg():
        #     self.pd.setValue(self.pd_progress)
        #     # self.pd.show()
        #
        # timer = QTimer(self.pd)
        # timer.timeout.connect(progress_chg)
        # timer.start(100)

        self.btnOpenNet = QPushButton(self.centralWidget)
        self.btnOpenNet.setObjectName(u"btnOpenNet")

        # self.verticalLayout_0.addWidget(self.pd)
        self.verticalLayout_0.addWidget(xodr_label1)
        self.verticalLayout_0.addWidget(self.xodrStep)
        self.verticalLayout_0.addWidget(self.btnOpenNet)

        # 信息窗
        self.groupBox_3 = QGroupBox(self.centralWidget)
        self.groupBox_3.setObjectName(u"groupBox_3")

        self.verticalLayout_2 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(1, -1, 1, -1)

        self.txtMessage1 = QTextBrowser(self.groupBox_3)
        self.txtMessage1.setObjectName(u"txtMessage")

        self.txtMessage2 = QTextBrowser(self.groupBox_3)
        self.txtMessage2.setObjectName(u"txtMessage")

        self.verticalLayout_2.addWidget(self.txtMessage1)
        self.verticalLayout_2.addWidget(self.txtMessage2)

        # xodr 创建选择页
        self.groupBox_2 = QGroupBox(self.centralWidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_2)

        xodr_label2 = QLabel()
        xodr_label2.setText("车道类型")
        self.xodrCk1, self.xodrCk2 = QCheckBox('机动车道'), QCheckBox('非机动车道')
        self.xodrCks = [self.xodrCk1, self.xodrCk2]
        for i in self.xodrCks:
            i.setCheckState(QtCore.Qt.Checked)

        self.btnShowXodr = QPushButton(self.centralWidget)
        self.btnShowXodr.setObjectName(u"btnShowXodr")

        self.verticalLayout_4.addWidget(xodr_label2)
        self.verticalLayout_4.addWidget(self.xodrCk1)
        self.verticalLayout_4.addWidget(self.xodrCk2)
        self.verticalLayout_4.addWidget(self.btnShowXodr)

        # 添加控件到布局
        self.verticalLayout.addWidget(self.groupBox_1)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.verticalLayout.addWidget(self.groupBox_3)

        self.groupBox_3.setVisible(True)  # 信息窗
        self.groupBox_2.setVisible(False)  # 创建选择框
        self.txtMessage2.setVisible(False) # error 信息栏
        # xodr 控件结束


        TESS_API_EXAMPLEClass.setCentralWidget(self.centralWidget)
        self.menuBar = QMenuBar(TESS_API_EXAMPLEClass)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 262, 26))
        TESS_API_EXAMPLEClass.setMenuBar(self.menuBar)
        self.mainToolBar = QToolBar(TESS_API_EXAMPLEClass)
        self.mainToolBar.setObjectName(u"mainToolBar")
        TESS_API_EXAMPLEClass.addToolBar(Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QStatusBar(TESS_API_EXAMPLEClass)
        self.statusBar.setObjectName(u"statusBar")
        TESS_API_EXAMPLEClass.setStatusBar(self.statusBar)

        self.retranslateUi(TESS_API_EXAMPLEClass)

        QMetaObject.connectSlotsByName(TESS_API_EXAMPLEClass)
    # setupUi

    def retranslateUi(self, TESS_API_EXAMPLEClass):
        TESS_API_EXAMPLEClass.setWindowTitle(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"TESS_API_EXAMPLE", None))
        self.btnOpenNet.setText(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u9009\u62e9\u6587\u4ef6", None))
        # self.btnStartSimu.setText(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u542f\u52a8\u4eff\u771f", None))
        # self.btnPauseSimu.setText(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u6682\u505c\u4eff\u771f", None))
        # self.btnStopSimu.setText(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u505c\u6b62\u4eff\u771f", None))
        self.groupBox_1.setTitle(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u5bfc\u5165opendrive\u6587\u4ef6", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u4fe1\u606f\u7a97", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u521b\u5efaTESS NG", None))
        self.btnShowXodr.setText(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u786e\u8ba4", None))
        # self.xodr_step.setText(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u786e", None))
    # retranslateUi