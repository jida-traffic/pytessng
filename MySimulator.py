import random

from PySide2.QtCore import *
from Tessng import TessInterface, SimuInterface, PyCustomerSimulator, IVehicle, m2p, tngIFace, tngPlugin
from Tessng import TESSNG
from opendrive2tess.utils.external_utils import get_vehi_info


class MySimulator(QObject, PyCustomerSimulator):
    forRunInfo = Signal(str)
    def __init__(self):
        QObject.__init__(self)
        PyCustomerSimulator.__init__(self)
        self.mrSquareVehiCount = 28
        self.mrSpeedOfPlane = 0

    def initVehicle(self, vehi):
        tmpId = vehi.id() % 100000
        roadName = vehi.roadName()
        roadId = vehi.roadId()
        if roadName == '曹安公路':
            #飞机
            if tmpId == 1:
                vehi.setVehiType(12)
                vehi.initLane(3, m2p(105), 0)
            #工程车
            elif tmpId >=2 and tmpId <=8:
                vehi.setVehiType(8)
                vehi.initLane((tmpId - 2) % 7, m2p(80), 0)
            #消防车
            elif tmpId >=9 and tmpId <=15:
                vehi.setVehiType(9)
                vehi.initLane((tmpId - 2) % 7, m2p(65), 0)
            #消防车
            elif tmpId >=16 and tmpId <=22:
                vehi.setVehiType(10)
                vehi.initLane((tmpId - 2) % 7, m2p(50), 0)
            #最后两队列小车
            elif tmpId == 23:
                vehi.setVehiType(1)
                vehi.initLane(1, m2p(35), 0)
            elif tmpId == 24:
                vehi.setVehiType(1)
                vehi.initLane(5, m2p(35), 0)
            elif tmpId == 25:
                vehi.setVehiType(1)
                vehi.initLane(1, m2p(20), 0)
            elif tmpId == 26:
                vehi.setVehiType(1)
                vehi.initLane(5, m2p(20), 0)
            elif tmpId == 27:
                vehi.setVehiType(1)
                vehi.initLane(1, m2p(5), 0)
            elif tmpId == 28:
                vehi.setVehiType(1)
                vehi.initLane(5, m2p(5), 0)
            if tmpId >= 23 and tmpId <= 28:
                vehi.setLength(m2p(4.5), True)
        return True

    def ref_calcAcce(self, vehi, acce):
        return False
        # if vehi.vehiDistFront() < m2p(5):
        #     #前车距小于5米，让TESSNG计算加速度
        #     return False
        # elif vehi.currSpeed() > m2p(10):
        #     acce.value = m2p(-2)
        # elif vehi.currSpeed() < m2p(1):
        #     acce.value = m2p(2)
        # return False

    def ref_reCalcdesirSpeed(self, vehi, ref_esirSpeed):
        tmpId = vehi.id() % 100000
        roadName = vehi.roadName()
        if roadName == '曹安公路':
            if tmpId <= self.mrSquareVehiCount:
                iface = tngIFace()
                simuIFace = iface.simuInterface()
                simuTime = simuIFace.simuTimeIntervalWithAcceMutiples()
                if simuTime < 5 * 1000:
                    ref_esirSpeed.value = 0
                elif simuTime < 10 * 1000:
                    ref_esirSpeed.value = m2p(20 / 3.6)
                else:
                    ref_esirSpeed.value = m2p(40 / 3.6)
            return True
        return False

    def ref_reSetFollowingParam(self, vehi, ref_inOutSi, ref_inOutSd):
        roadName = vehi.roadName()
        if roadName == "连接段2":
            ref_inOutSd.value = m2p(30);
            return True
        return False

    def ref_reSetAcce(self, vehi, inOutAcce):
        roadName = vehi.roadName()
        if roadName == "连接段1":
            if vehi.currSpeed() > m2p(20 / 3.6):
                inOutAcce = m2p(-5)
                return True
            elif vehi.currSpeed() > m2p(20 / 3.6):
                inOutAcce = m2p(-1)
                return True
        return False

    def ref_reSetSpeed(self, vehi, ref_inOutSpeed):
        tmpId = vehi.id() % 100000
        roadName = vehi.roadName()
        if roadName == "曹安公路":
            if tmpId == 1:
                self.mrSpeedOfPlane = vehi.currSpeed()
            elif tmpId >= 2 and tmpId <= self.mrSquareVehiCount: #and self.mrSpeedOfPlane >= 0:
                ref_inOutSpeed.value = self.mrSpeedOfPlane
                return True
        return False

    #计算是否要左自由变道
    def reCalcToLeftFreely(self, vehi):
        #车辆到路段或连接终点距离小于20米不变道
        if vehi.vehicleDriving().distToEndpoint() - vehi.length() / 2 < m2p(20):
            return False
        tmpId = vehi.id() % 100000
        roadName = vehi.roadName()
        if roadName == "曹安公路":
            if tmpId >= 23 and tmpId <= 28:
                laneNumber = vehi.vehicleDriving().laneNumber()
                if laneNumber == 1 or laneNumber == 4:
                    return True
        return False

    #计算是否要右自由变道
    def reCalcToRightFreely(self, vehi):
        tmpId = vehi.id() % 100000;
        #车辆到路段或连接终点距离小于20米不变道
        if vehi.vehicleDriving().distToEndpoint() - vehi.length() / 2 < m2p(20):
            return False

        roadName = vehi.roadName();
        if roadName == "曹安公路":
            if tmpId >= 23 and tmpId <= 28:
                laneNumber = vehi.vehicleDriving().laneNumber()
                if laneNumber == 2 or laneNumber == 5:
                    return True
        return False

    def afterOneStep(self):
        #= == == == == == =以下是获取一些仿真过程数据的方法 == == == == == ==
        # TESSNG 顶层接口
        iface = tngIFace()
        # TESSNG 仿真接口
        simuiface = iface.simuInterface()
        netiface = iface.netInterface()
        # 当前仿真计算批次
        batchNum = simuiface.batchNumber()
        # 当前已仿真时间，单位：毫秒
        simuTime = simuiface.simuTimeIntervalWithAcceMutiples()
        # 开始仿真的现实时间
        startRealtime = simuiface.startMSecsSinceEpoch()
        # 当前正在运行车辆列表
        lAllVehi = simuiface.allVehiStarted()


        # TODO 发送所有的消息至后台处理接口(queue or redis or http)
        data = get_vehi_info(simuiface)
        import sys
        my_process = sys.modules["__main__"].__dict__['myprocess']
        # 如果队列满了，取出第一个数据，为了防止数据在期间被另一进程消费完，导致等待(死锁)，采用nowait并捕获
        if my_process.my_queue.full():
            try:
                my_process.my_queue.get_nowait()
            except:
                pass
        try:
            my_process.my_queue.put_nowait(data)
        except:
            pass
        # print(my_process.my_queue.qsize())

        # 当前在ID为1的路段上车辆
        lVehis = simuiface.vehisInLink(1)

        if batchNum % 20 == 0:
            strLinkCount = str(netiface.linkCount())
            strVehiCount = str(len(lAllVehi))
            strSimuTime = str(simuTime)
            runInfo = f"路段数：{strLinkCount}\n运行车辆数：{strVehiCount}\n仿真时间：{strSimuTime}(毫秒)"
            self.forRunInfo.emit(runInfo)


        # 动态发车，不通过发车点
        if batchNum % 50 == 1:
            r = hex(256 + random.randint(0,256))[3:].upper()
            g = hex(256 + random.randint(0,256))[3:].upper()
            b = hex(256 + random.randint(0,256))[3:].upper()
            color = f"#{r}{g}{b}"
            # 路段上发车
            dvp = TESSNG.DynaVehiParam()
            dvp.vehiTypeCode = random.randint(0, 4) + 1
            dvp.roadId = 6
            dvp.laneNumber = random.randint(0, 3)
            dvp.dist = 50
            dvp.speed = 20
            dvp.color = color

            pIVehicle1 = simuiface.createGVehicle(dvp)
            if pIVehicle1 != None:
                pass

            # 连接段上发车
            dvp2 = TESSNG.DynaVehiParam()
            dvp2.vehiTypeCode = random.randint(0, 4) + 1
            dvp2.roadId = 3
            dvp2.laneNumber = random.randint(0, 3)
            dvp2.toLaneNumber = dvp2.laneNumber # 默认为 - 1，如果大于等于0, 在连接段上发车
            dvp2.dist = 50
            dvp2.speed = 20
            dvp2.color = color
            pIVehicle2 = simuiface.createGVehicle(dvp2)
            if pIVehicle2 != None:
                pass










