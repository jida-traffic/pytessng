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
        xodr_label1.setText("路段最小分段长度(请在文件导入前选择)")
        self.xodrStep = QComboBox(self.centralWidget)
        self.xodrStep.addItems(( "20", "0.5", "0.1", "1", "5", "10"))
        # 文件导入进度条
        self.pb = QProgressBar(self.centralWidget)
        self.pb.setRange(0, 100)  # 进度对话框的范围设定
        self.pb.setTextVisible(False)

        self.btnOpenNet = QPushButton(self.centralWidget)
        self.btnOpenNet.setObjectName(u"btnOpenNet")

        # self.verticalLayout_0.addWidget(self.pd)
        self.verticalLayout_0.addWidget(xodr_label1)
        self.verticalLayout_0.addWidget(self.xodrStep)
        self.verticalLayout_0.addWidget(self.pb)
        self.verticalLayout_0.addWidget(self.btnOpenNet)

        # 信息窗
        self.groupBox_3 = QGroupBox(self.centralWidget)
        self.groupBox_3.setObjectName(u"groupBox_3")

        self.verticalLayout_2 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(1, -1, 1, -1)

        self.text_label_1 = QLabel()
        self.text_label_1.setText("路网详情")
        self.txtMessage1 = QTextBrowser(self.groupBox_3)
        self.txtMessage1.setObjectName(u"txtMessage")

        self.text_label_2 = QLabel()
        self.text_label_2.setText("创建异常信息提示窗\n(用户可根据异常信息手动更改)")
        self.txtMessage2 = QTextBrowser(self.groupBox_3)
        self.txtMessage2.setObjectName(u"txtMessage")

        self.verticalLayout_2.addWidget(self.text_label_1)
        self.verticalLayout_2.addWidget(self.txtMessage1)
        self.verticalLayout_2.addWidget(self.text_label_2)
        self.verticalLayout_2.addWidget(self.txtMessage2)

        # xodr 创建选择页
        self.groupBox_2 = QGroupBox(self.centralWidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_2)

        xodr_label2 = QLabel()
        xodr_label2.setText("导入车道类型选择")
        self.xodrCk1, self.xodrCk2 = QCheckBox('机动车道'), QCheckBox('非机动车道')
        self.xodrCks = [self.xodrCk1, self.xodrCk2]
        for i in self.xodrCks:
            i.setCheckState(QtCore.Qt.Checked)

        self.btnShowXodr = QPushButton(self.centralWidget)
        self.btnShowXodr.setObjectName(u"btnShowXodr")

        xodr_label3 = QLabel()
        xodr_label3.setText(f"车道转换说明:\n机动车道:\n{'~0.2m:'.ljust(10)} 不解析\n{'0.2m~3m:'.ljust(10)} 视为连接段\n{'3m~:'.ljust(10)} 正常车道\n")

        self.verticalLayout_4.addWidget(xodr_label2)
        self.verticalLayout_4.addWidget(self.xodrCk1)
        self.verticalLayout_4.addWidget(self.xodrCk2)
        self.verticalLayout_4.addWidget(self.btnShowXodr)
        self.verticalLayout_4.addWidget(xodr_label3)

        # 添加控件到布局
        self.verticalLayout.addWidget(self.groupBox_1)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.verticalLayout.addWidget(self.groupBox_3)

        self.groupBox_3.setVisible(True)  # 信息窗
        self.pb.setVisible(False)  # 信息窗
        self.groupBox_2.setVisible(False)  # 创建选择框
        self.text_label_1.setVisible(False)
        self.text_label_2.setVisible(False)
        self.txtMessage1.setVisible(True) # error 信息栏
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
        self.groupBox_1.setTitle(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"opendrive文件导入", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u4fe1\u606f\u7a97", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"\u521b\u5efaTESS NG", None))
        self.btnShowXodr.setText(QCoreApplication.translate("TESS_API_EXAMPLEClass", u"开始创建TESS NG路网", None))


    def change_progress(self, pb, value, network_info=None, error=False):
        if error:
            # 导入失败，窗体不显示，错误提示
            self.pb.setVisible(False)
            self.text_label_1.setVisible(False)
            self.groupBox_2.setVisible(False)
            self.btnOpenNet.setEnabled(True)
            QMessageBox.warning(None, "提示信息", "路网解析错误，请联系开发者")
            return
        pb.setValue(value)
        if not network_info:
            self.pb.setVisible(True)
        else:
            self.pb.setVisible(False)
            # 导入完成后，部分窗体展示
            self.text_label_1.setVisible(True)
            self.txtMessage1.setText(f"{str(network_info)}")
            self.groupBox_2.setVisible(True)
            self.btnOpenNet.setEnabled(True)
