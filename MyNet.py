from PySide2.QtGui import QVector3D
from Tessng import PyCustomerNet, tngIFace, m2p


def get_coo_list(vertices):
    list1 = []
    x_move, y_move = 0, 0
    for index in range(0, len(vertices), 1):
        vertice = vertices[index]
        list1.append(QVector3D(m2p((vertice[0] - x_move)), m2p(-(vertice[1] - y_move)), m2p(vertice[2])))
    if len(list1) < 2:
        raise 3
    return list1


# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 创建路网
    def createNet(self):
        # 中铁路网绘制
        pass

    def afterLoadNet(self):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # 设置场景大小
        netiface.setSceneSize(300, 300)
        count = netiface.linkCount()
        if (count == 0):
            self.createNet()
