from Tessng import PyCustomerNet, tngIFace


# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 创建路网
    def createNet(self, roads_info, lanes_info):
        pass

    def afterLoadNet(self):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # 设置场景大小
        netiface.setSceneSize(1000, 1000)  # 测试数据
        # netiface.setSceneSize(4000, 1000)  # 华为路网
        # netiface.setSceneSize(10000, 3000)  # 深圳路网
        # 获取路段数
        count = netiface.linkCount()
        # if (count == 0):
        #     self.createNet(roads_info, lanes_info)
