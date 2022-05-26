from PySide2.QtCore import *

from PySide2.QtWidgets import *
from Tessng import PyCustomerNet, TessInterface, TessPlugin, NetInterface, tngPlugin, tngIFace, m2p
from Tessng import NetItemType, GraphicsItemPropName

class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    def createNet(self):
        # 第一条路段
        iface = tngIFace()
        netiface = iface.netInterface()

        startPoint = QPointF(m2p(-300), 0)
        endPoint = QPointF(m2p(300), 0)
        lPoint = [startPoint, endPoint]
        link1 = netiface.createLink(lPoint, 7, "曹安公路")
        if link1 is not None:
            dp = netiface.createDispatchPoint(link1)
            if dp != None :
                dp.addDispatchInterval(1, 2, 28)

        #第二条路段
        startPoint = QPointF(m2p(-300), m2p(-25))
        endPoint = QPointF(m2p(300), m2p(-25))
        lPoint = [startPoint, endPoint]
        link2 = netiface.createLink(lPoint, 7, "次干道")
        if link2 is not None:
            dp = netiface.createDispatchPoint(link2)
            if  dp is not None:
                dp.addDispatchInterval(1, 3600, 3600)

        #第三条路段
        startPoint = QPointF(m2p(-300), m2p(25))
        endPoint = QPointF(m2p(-150), m2p(25))
        lPoint = [startPoint, endPoint]
        link3 = netiface.createLink(lPoint, 3)
        if link3 is not None:
            dp = netiface.createDispatchPoint(link3)
            if dp is not None:
                dp.addDispatchInterval(1, 3600, 3600)

        #创建第四条路段
        startPoint = QPointF(m2p(-50), m2p(25))
        endPoint = QPointF(m2p(50), m2p(25))
        lPoint = [startPoint, endPoint]
        link4 = netiface.createLink(lPoint, 3)

        #创建第五条路段
        startPoint = QPointF(m2p(150), m2p(25))
        endPoint = QPointF(m2p(300), m2p(25))
        lPoint = [startPoint, endPoint]
        link5 = netiface.createLink(lPoint, 3, "自定义限速路段")
        if link5 is not None:
            link5.setLimitSpeed(30)

        #创建第六条路段
        startPoint = QPointF(m2p(-300), m2p(50))
        endPoint = QPointF(m2p(300), m2p(50))
        lPoint = [startPoint, endPoint]
        link6 = netiface.createLink(lPoint, 3, "动态发车路段")
        if link6 is not None:
            link6.setLimitSpeed(80)

        #创建第七条路段
        startPoint = QPointF(m2p(-300), m2p(75))
        endPoint = QPointF(m2p(-250), m2p(75))
        lPoint = [startPoint, endPoint]
        link7 = netiface.createLink(lPoint, 3)
        if link7 is not None:
            link7.setLimitSpeed(80)

        #创建第八条路段
        startPoint = QPointF(m2p(-50), m2p(75))
        endPoint = QPointF(m2p(300), m2p(75))
        lPoint = [startPoint, endPoint]
        link8 = netiface.createLink(lPoint, 3)
        if link8 is not None:
            link8.setLimitSpeed(80)

        #创建第一条连接段
        if link3 is not None and link4 is not None:
            lFromLaneNumber = [1, 2, 3]
            lToLaneNumber = [1, 2, 3]
            conn1 = netiface.createConnector(link3.id(), link4.id(), lFromLaneNumber, lToLaneNumber, "连接段1", True)

        #创建第二条连接段
        if link4 is not None and link5 is not None:
            lFromLaneNumber = [1, 2, 3]
            lToLaneNumber = [1, 2, 3]
            conn1 = netiface.createConnector(link4.id(), link5.id(), lFromLaneNumber, lToLaneNumber, "连接段2", True)

        #创建第三条连接段
        if link7 is not None and link8 is not None:
            lFromLaneNumber = [1, 2, 3]
            lToLaneNumber = [1, 2, 3]
            conn1 = netiface.createConnector(link7.id(), link8.id(), lFromLaneNumber, lToLaneNumber, "动态发车连接段", True)

    def afterLoadNet(self):
        iface = tngIFace()
        netiface = iface.netInterface()
        count = netiface.linkCount()
        if(count == 0):
            self.createNet()
        if(netiface.linkCount() > 0):
            iface.simuInterface().startSimu()
        # plugin = tngPlugin()
        # config = plugin.tessngConfig()
        # if config['__simuafterload'] is True:
        #     iface.simuInterface().startSimu()

    def ref_labelNameAndFont(self, itemType, itemId, ref_outPropName, ref_outFontSize):
        iface = tngIFace()
        simuiface = iface.simuInterface()
        if simuiface.isRunning():
            ref_outPropName.value = GraphicsItemPropName.None_
            return
        ref_outPropName.value = GraphicsItemPropName.Id
        ref_outFontSize.value = 6
        if itemType == NetItemType.GConnectorType:
            ref_outPropName.value = GraphicsItemPropName.Name
        elif itemType == NetItemType.GLinkType:
            if itemId == 1 or itemId == 5 or itemId == 6:
                ref_outPropName.value = GraphicsItemPropName.Name















