import math
from PySide2.QtGui import QVector3D
from Tessng import m2p
from Tessng import p2m
import numpy as np


class BaseRoad:
    Road_id = 1
    def __init__(self):
        self.id = BaseRoad.Road_id
        BaseRoad.Road_id += 1

        # 中心车道
        self.lanes = [
            {
                'width': [],
                'type': 'none',
                'id': 0,
                'direction': 'center',
                'lane': None,
            }
        ]

    # 参考线计算
    @staticmethod
    def calc_geometry(points):
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

    @staticmethod
    def qtpoint2point(qtpoints):
        points = []
        for qtpoint in qtpoints:
            points.append(
                [p2m(qtpoint.x()), - p2m(qtpoint.y()), p2m(qtpoint.z())] if isinstance(qtpoint, QVector3D) else qtpoint
            )
        return points

    @staticmethod
    def get_coo_list(vertices):
        list1 = []
        x_move, y_move = 0, 0
        for index in range(0, len(vertices), 1):
            vertice = vertices[index]
            list1.append(QVector3D(m2p((vertice[0] - x_move)), m2p(-(vertice[1] - y_move)), m2p(vertice[2])))
        if len(list1) < 2:
            raise 3
        return list1

    @staticmethod
    # 计算向量2相对向量1的旋转角度（-pi~pi）
    def clockwise_angle(v1, v2):
        x1, y1 = v1.x, v1.y
        x2, y2 = v2.x, v2.y
        dot = x1 * x2 + y1 * y2
        det = x1 * y2 - y1 * x2
        theta = np.arctan2(det, dot)
        return theta

    @staticmethod
    def calc_elevation(points):
        """
        计算 高程曲线列表
        """
        elevations = []
        s = 0
        for index in range(len(points) - 1):
            start_point, end_point = points[index], points[index + 1]
            start_height, end_height = start_point[2], end_point[2]

            distance = np.linalg.norm(np.array(start_point[:2]) - np.array(end_point[:2]))

            a = start_height
            b = (end_height - start_height) / distance
            elevations.append(
                Curve(s=s, a=a, b=b, c=0, d=0)  # 直线段 c=0, d=0
            )
            s += distance
        return elevations

    @staticmethod
    def calc_deviation_curves(qt_left_points, qt_right_points, calc_singal=False):
        left_points = BaseRoad.qtpoint2point(qt_left_points)
        right_points = BaseRoad.qtpoint2point(qt_right_points)

        deviation_curves = []
        # 车道宽度计算，以左侧车道为基础，向右偏移（向tessng看齐）,假设所有车道宽度线性变化
        s = 0
        for index in range(len(left_points) - 1):
            left_start_point, left_end_point = left_points[index], left_points[index + 1]
            right_start_point, right_end_point = right_points[index], right_points[index + 1]

            # 向左偏移为正，向右偏移为负
            geometry_vector = Vector(start_point=left_start_point, end_point=left_end_point)
            start_deviation_vector = Vector(start_point=left_start_point, end_point=right_start_point)
            end_deviation_vector = Vector(start_point=left_end_point, end_point=right_end_point)

            # 计算向量夹角 角度在 -pi ~ 0 以内
            start_signal = np.sign(BaseRoad.clockwise_angle(geometry_vector, start_deviation_vector))
            end_signal = np.sign(BaseRoad.clockwise_angle(geometry_vector, end_deviation_vector))

            # 起终点宽度及行进距离, TODO 此处宽度算有问题，不应该用相应成对点的距离作为宽度，有可能发生两点不垂直于中心线，这样算出的宽度偏大
            start_deviation_distance = (np.linalg.norm(
                np.array(right_start_point[:2]) - np.array(left_start_point[:2]))) * start_signal * -1
            end_deviation_distance = (np.linalg.norm(
                np.array(right_end_point[:2]) - np.array(left_end_point[:2]))) * end_signal * -1
            forward_distance = np.linalg.norm(np.array(left_end_point[:2]) - np.array(left_start_point[:2]))

            a = start_deviation_distance
            b = (end_deviation_distance - start_deviation_distance) / forward_distance

            # if calc_singal and (start_signal != -1 or end_signal != -1):
            #     print('error')  # TODO 在非中心车道计算过程中，理论上右侧车道的相对角度永远为负

            deviation_curves.append(
                Curve(s=s, a=a, b=b, c=0, d=0)  # 直线段 c=0, d=0
            )
            s += forward_distance

        return deviation_curves


class Road(BaseRoad):
    def __init__(self, link):
        super().__init__()

        self.tess_id = link.id()
        self.link = link

        # 计算路段参考线及高程
        geometry_points = self.qtpoint2point(self.link.centerBreakPoint3Ds())
        self.geometrys, self.length = self.calc_geometry(geometry_points)
        self.elevations = self.calc_elevation(geometry_points)  # 用车道中心线计算高程

        # 计算中心车道偏移量
        self.lane_offsets = self.calc_deviation_curves(link.leftBreakPoint3Ds(), link.centerBreakPoint3Ds(), calc_singal=False)

        # 计算车道及相关信息
        self.add_lane()

    # 添加车道
    def add_lane(self):
        lane_objs = self.link.lanes()[::-1]
        lane_id = -1
        direction = 'right'
        for index in range(0, len(lane_objs)):  # 从中心车道向右侧展开
            lane = lane_objs[index]
            widths = self.calc_deviation_curves(lane.leftBreakPoint3Ds(), lane.rightBreakPoint3Ds(), calc_singal=True)
            self.lanes.append(
                {
                    'width': widths,
                    'type': 'driving',  # TODO lane.actionType(),
                    'id': lane_id,
                    'direction': direction,
                    'lane': lane,
                }
            )
            lane_id -= 1
            # TODO 每两个车道间，添加一个特殊车道，用来填充无法通行的部分
            # 如果不是最右侧车道，向右填充
            # if lane_objs[-1] != lane:
            #     widths = self.calc_deviation_curves(lane.rightBreakPoint3Ds(), lane_objs[index + 1].leftBreakPoint3Ds(), calc_singal=False)
            #     self.lanes.append(
            #         {
            #             'width': widths,
            #             'type': 'restricted',
            #             'id': lane_id,
            #             'direction': direction,
            #             "lane": None,
            #         }
            #     )
            #     lane_id -= 1
        return None


class Connector(BaseRoad):
    def __init__(self, connector, junction):
        super().__init__()

        self.junction = junction
        self.tess_id = connector.id()
        self.connector = connector
        self.fromLink = connector.fromLink()
        self.toLink = connector.toLink()

        self.lane_offsets = []  # 连接段选取最左侧边界作为参考线，不会有offset
        # # 默认 车道方向只有参考线方向
        geometry_points = self.add_lanes()
        self.geometrys, self.length = self.calc_geometry(geometry_points)
        self.elevations = self.calc_elevation(geometry_points)   # 用车道中心线计算高程

    # 添加车道
    def add_lanes(self):
        # 获取连接段的左右边界点序列，用来后续分配给各车道的宽度
        connector_left_points = [np.array(_) for _ in self.qtpoint2point(self.connector.laneConnectors()[-1].leftBreakPoint3Ds())]
        connector_right_points = [np.array(_) for _ in self.qtpoint2point(self.connector.laneConnectors()[0].rightBreakPoint3Ds())]

        # 计算需要建立的连接段上的车道数量
        from_lanes, to_lanes = set(), set()
        for laneConnector in self.connector.laneConnectors():
            from_lanes.add(laneConnector.fromLane())
            to_lanes.add(laneConnector.toLane())
        lane_count = max(len(from_lanes), len(to_lanes))

        # 计算连接段上各车道的左右边界
        all_lane_points = []
        # TODO 保证左右点数量相同
        point_count = min(len(connector_left_points), len(connector_right_points))  # 点位过少，会导致车道沿参考线垂直向左右延申，容易错误
        connector_left_points = [i[0] for i in np.array_split(connector_left_points, point_count)]
        connector_right_points = [i[0] for i in np.array_split(connector_right_points, point_count)]

        # from matplotlib import pyplot as plt
        # plt.plot([i[0] for i in connector_right_points], [i[1] for i in connector_right_points])
        # plt.show()

        for lane_num in range(lane_count):  # 此处采用的是平均分配，每条车道宽度变化一致，也可使用少数车道宽度稳定，其他车道渐变的方式
            all_lane_points.append(
                    {
                        'left_points': [connector_left_points[index] + (connector_right_points[index] - connector_left_points[index]) / lane_count * lane_num for index in range(point_count)],
                        'right_points': [connector_left_points[index] + (connector_right_points[index] - connector_left_points[index]) / lane_count * (lane_num + 1) for index in range(point_count)],
                    }
            )

        # 计算所有的车道
        lane_id = -1
        direction = 'right'
        for lane_points in all_lane_points:  # 从中心车道向右侧展开
            widths = self.calc_deviation_curves(lane_points["left_points"], lane_points["right_points"], calc_singal=True)
            self.lanes.append(
                {
                    'width': widths,
                    'type': 'driving',  # TODO lane.actionType(),
                    'id': lane_id,
                    'direction': direction,
                    'lane': None,
                }
            )
            lane_id -= 1

        # 参考线取最左侧车道的左边界
        geometry_points = all_lane_points[0]['left_points']
        return geometry_points  # 返回参考线点序列


class Junction:
    def __init__(self, ConnectorArea):
        self.tess_id = ConnectorArea.id()
        self.ConnectorArea = ConnectorArea
        self.connection_count = 0


# opendrive 中的所有曲线对象
class Curve:
    def __init__(self, **kwargs):
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
