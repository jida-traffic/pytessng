from pytessng import Tessng
from Tessng import *


# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 创建路网
    def createNet(self):
        pass

    def ref_curvatureMinDist(self, itemType: int, itemId: int, ref_minDist: Tessng.objreal):
        # if itemType == NetItemType.LaneConnectorType:
        ref_minDist.value = 0.1
        return True
