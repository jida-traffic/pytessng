import math
import numpy as np
from PySide2.QtGui import QVector3D
from Tessng import PyCustomerNet, tngIFace, m2p
from Tessng import p2m
import numpy as np


Road_id = 1
def qtpoint2point(qtpoints):
    points = []
    for qtpoint in qtpoints:
        points.append(
            [p2m(qtpoint.x()), - p2m(qtpoint.y()), p2m(qtpoint.z())] if isinstance(qtpoint, QVector3D) else qtpoint
        )
    return points


def get_coo_list(vertices):
    list1 = []
    x_move, y_move = 0, 0
    for index in range(0, len(vertices), 1):
        vertice = vertices[index]
        list1.append(QVector3D(m2p((vertice[0] - x_move)), m2p(-(vertice[1] - y_move)), m2p(vertice[2])))
    if len(list1) < 2:
        raise 3
    return list1


# 计算向量2相对向量1的旋转角度（-pi~pi）
def clockwise_angle(v1, v2):
    x1, y1 = v1.x, v1.y
    x2, y2 = v2.x, v2.y
    dot = x1 * x2 + y1 * y2
    det = x1 * y2 - y1 * x2
    theta = np.arctan2(det, dot)
    return theta


def calc_deviation_curves(qt_left_points, qt_right_points, calc_singal=False):
    left_points = qtpoint2point(qt_left_points)
    right_points = qtpoint2point(qt_right_points)

    deviation_curves = []
    # 车道宽度计算，以左侧车道为基础，向右偏移（向tessng看齐）
    s = 0
    for index in range(len(left_points) - 1):
        left_start_point, left_end_point = left_points[index], left_points[index + 1]
        right_start_point, right_end_point = right_points[index], right_points[index + 1]

        # 向左偏移为正，向右偏移为负
        geometry_vector = Vector(start_point=left_start_point, end_point=left_end_point)
        start_deviation_vector = Vector(start_point=left_start_point, end_point=right_start_point)
        end_deviation_vector = Vector(start_point=left_end_point, end_point=right_end_point)

        # 计算向量夹角 角度在 -pi ~ 0 以内
        start_signal = np.sign(clockwise_angle(geometry_vector, start_deviation_vector))
        end_signal = np.sign(clockwise_angle(geometry_vector, end_deviation_vector))


        start_deviation_distance = (np.linalg.norm(np.array(right_start_point[:2]) - np.array(left_start_point[:2]))) * start_signal * -1
        end_deviation_distance = (np.linalg.norm(np.array(right_end_point[:2]) - np.array(left_end_point[:2]))) * end_signal * -1
        forward_distance = np.linalg.norm(np.array(left_end_point[:2]) - np.array(left_start_point[:2]))

        a = start_deviation_distance
        b = (end_deviation_distance - start_deviation_distance) / forward_distance

        if calc_singal and (start_signal != -1 or end_signal != -1):
            print('error')  # 在非中心车道计算过程中，理论上右侧车道的相对角度永远为负

        deviation_curves.append(
            Curve(s=s, a=a, b=b, c=0, d=0)  # 直线段 c=0, d=0
        )
        s += forward_distance

    return deviation_curves


class Road:
    def __init__(self, link):
        global Road_id
        self.id = Road_id
        Road_id += 1

        self.tess_id = link.id()
        self.link = link
        # 默认 车道方向只有参考线方向
        self.geometrys, self.length = self.add_geometry()
        self.elevationProfile = []  # 高程
        self.lanes = self.add_lane()
        self.lane_offsets = calc_deviation_curves(link.leftBreakPoint3Ds(), link.centerBreakPoint3Ds(), calc_singal=False)

    # 参考线计算
    def add_geometry(self):
        qt_points = self.link.centerBreakPoint3Ds()
        points = qtpoint2point(qt_points)
        # 为简化计算，每路段只有一 section/dirction/
        geometrys = []
        s = 0
        for index in range(len(points) - 1):
            # 计算参考线段落
            start_point, end_point = points[index], points[index + 1]
            x, y = start_point[0], start_point[1]
            hdg = math.atan2(end_point[1] - start_point[1], end_point[0] - start_point[0])
            length = np.linalg.norm(np.array(start_point[:2]) - np.array(end_point[:2]))
            geometrys.append(
                Curve(s=s, x=x, y=y, hdg=hdg, length=length)
            )
            s += length
        return geometrys, s


    def add_lane(self):
        # 中心车道偏移计算 laneoffset
        lanes = []

        lanes.append(
            {
                'width': [],
                'type': 'none',
                'id': 0,
                'direction': 'center',
                'lane': None,
            }
        )  # 中心车道

        lane_objs = self.link.lanes()[::-1]

        lane_id = -1
        direction = 'right'
        for index in range(0, len(lane_objs)):  # 从中心车道向右侧展开
            lane = lane_objs[index]
            widths = calc_deviation_curves(lane.leftBreakPoint3Ds(), lane.rightBreakPoint3Ds(), calc_singal=True)
            lanes.append(
                {
                    'width': widths,
                    'type': 'driving',  # TODO lane.actionType(),
                    'id': lane_id,
                    'direction': direction,
                    'lane': lane,
                }
            )
            lane_id -= 1
            # 每两个车道间，添加一个特殊车道，用来填充无法通行的部分
            # 如果不是最右侧车道，向右填充
            if lane_objs[-1] != lane:
                widths = calc_deviation_curves(lane.rightBreakPoint3Ds(), lane_objs[index + 1].leftBreakPoint3Ds(), calc_singal=False)
                lanes.append(
                    {
                        'width': widths,
                        'type': 'restricted',
                        'id': lane_id,
                        'direction': direction,
                        "lane": None,
                    }
                )
                lane_id -= 1
        return lanes

    def add_junction(self):
        pass

    def add_link(self):
        pass


class Junction:
    def __init__(self, ConnectorArea):
        self.tess_id = ConnectorArea.id()
        self.ConnectorArea = ConnectorArea

        self.connection_count = 0
    pass


class Connector:
    def __init__(self, connector, junction):
        global Road_id
        self.id = Road_id
        Road_id += 1

        self.junction = junction

        self.tess_id = connector.id()
        self.connector = connector
        self.fromLink = connector.fromLink()
        self.toLink = connector.toLink()

        self.lane_offsets = []  # 连接段选取最左侧边界作为参考线，不会有offset
        # # 默认 车道方向只有参考线方向
        # self.elevationProfile = []  # 高程
        self.lanes, self.geometrys, self.length = self.add_lanes()


    def add_lanes(self):
        connector_start_left_point, connector_start_right_point, connector_end_left_point, connector_end_right_point = [
            np.array(_) for _ in qtpoint2point([
                self.fromLink.leftBreakPoint3Ds()[-1], self.fromLink.rightBreakPoint3Ds()[-1],
                self.toLink.leftBreakPoint3Ds()[0], self.toLink.rightBreakPoint3Ds()[0],
            ])]

        # 取两点
        # connector_left_points = [np.array(_) for _ in qtpoint2point([self.fromLink.leftBreakPoint3Ds()[-1], self.toLink.leftBreakPoint3Ds()[0]])]
        # connector_right_points = [np.array(_) for _ in qtpoint2point([self.fromLink.rightBreakPoint3Ds()[-1], self.toLink.rightBreakPoint3Ds()[0]])]

        # 暂时取第一个连接与第二个连接
        connector_left_points = [np.array(_) for _ in qtpoint2point(self.connector.laneConnectors()[0].leftBreakPoint3Ds())]
        connector_right_points = [np.array(_) for _ in qtpoint2point(self.connector.laneConnectors()[-1].rightBreakPoint3Ds())]

        from_lanes, to_lanes = set(), set()
        for laneConnector in self.connector.laneConnectors():
            from_lanes.add(laneConnector.fromLane())
            to_lanes.add(laneConnector.toLane())
        lane_count = max(len(from_lanes), len(to_lanes))

        # TODO 保证左右点数量相同
        for _ in self.connector.laneConnectors():
            print(list([len(_.leftBreakPoint3Ds()) for _ in self.connector.laneConnectors()]))

        all_lane_points = []
        point_count = min(len(connector_left_points), len(connector_right_points))  # 点位过少，会导致车道沿参考线垂直向左右延申，容易错误
        for lane_num in range(lane_count):  # 此处采用的是平均分配，每条车道宽度变化一致，也可使用少数车道宽度稳定，其他车道渐变的方式
            all_lane_points.append(
                    {
                        'left_points': [connector_left_points[index] + (connector_right_points[index] - connector_left_points[index]) / lane_count * lane_num for index in range(point_count)],
                        'right_points': [connector_left_points[index] + (connector_right_points[index] - connector_left_points[index]) / lane_count * (lane_num + 1) for index in range(point_count)],
                    }
            )


        # junction点位打印
        import matplotlib.pyplot as plt
        for lane_points in all_lane_points:
            for k, points in lane_points.items():
                plt.plot([_[0] for _ in points], [_[1] for _ in points], color='g', linestyle="", marker=".", linewidth=1)
        plt.show()

        # 计算所有的车道
        lanes = []
        # 中心车道偏移计算 laneoffset
        lanes.append(
            {
                'width': [],
                'type': 'none',
                'id': 0,
                'direction': 'center',
                'lane': None,
            }
        )  # 中心车道

        lane_id = -1
        direction = 'right'
        for lane_points in all_lane_points:  # 从中心车道向右侧展开
            widths = calc_deviation_curves(lane_points["left_points"], lane_points["right_points"], calc_singal=True)
            lanes.append(
                {
                    'width': widths,
                    'type': 'driving',  # TODO lane.actionType(),
                    'id': lane_id,
                    'direction': direction,
                    'lane': None,
                }
            )
            lane_id -= 1

        geometrys, s = self.add_geometry(all_lane_points[0]['left_points'])
        return lanes, geometrys, s

    # 参考线计算
    def add_geometry(self, points):
        # 为简化计算，每路段只有一 section/dirction/
        geometrys = []
        s = 0
        for index in range(len(points) - 1):
            # 计算参考线段落
            start_point, end_point = points[index], points[index + 1]
            x, y = start_point[0], start_point[1]
            hdg = math.atan2(end_point[1] - start_point[1], end_point[0] - start_point[0])
            length = np.linalg.norm(np.array(start_point[:2]) - np.array(end_point[:2]))
            geometrys.append(
                Curve(s=s, x=x, y=y, hdg=hdg, length=length)
            )
            s += length
        return geometrys, s

    def add_junction(self):
        pass

    def add_link(self):
        pass



# opendrive 中的所有曲线对象
class Curve:
    def __init__(self, **kwargs):
        # self.road = None
        # self.section = None
        # self.lane = None
        # self.s = None
        # self.x = None
        # self.y = None
        # self.hdg = None
        # self.a, self.b, self.c, self.d = None, None, None, None
        # self.offset = None
        parameters = ["road", "section", "lane", "s", "x", "y", "hdg", "a", "b", "c", "d", "offset", 'direction', 'level', 'length']
        for key in parameters:
            if key in kwargs:
                self.__setattr__(key, kwargs[key])
            else:
                self.__setattr__(key, None)

class Vector:
    def __init__(self, start_point, end_point):
        start_point, end_point = list(start_point), list(end_point)
        self.x = end_point[0] - start_point[0]
        self.y = end_point[1] - start_point[1]
        self.z = end_point[2] - start_point[2]
