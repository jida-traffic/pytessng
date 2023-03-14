import collections
import math

from tessng2other.opendrive.functions import qtpoint2point
from tessng2other.unity.config import border_line_width

# 为了节省空间，仅对路段级的做黑色三角形，同时取车道左侧做白色线，一般为白色虚线，如果车道类型不一致，做白色实线，如果是最左侧车道，做黄色实线
from tessng2other.unity.functions import create_curve, deviation_point, chunk


def calc_boundary(base_points, border_line_width):
    left_points, right_points = [], []
    point_count = len(base_points)
    for index, _ in enumerate(base_points):
        if index + 1 == point_count:
            is_last = True
            num = index - 1
        else:
            is_last = False
            num = index
        left_point = deviation_point(base_points[num], base_points[num + 1], border_line_width / 2, right=False,
                                     is_last=is_last)
        right_point = deviation_point(base_points[num], base_points[num + 1], border_line_width / 2, right=True,
                                      is_last=is_last)
        left_points.append(left_point)
        right_points.append(right_point)
    return left_points, right_points


def convert_unity(netiface):
    unity_info = collections.defaultdict(list)

    # 绘制路面
    for link in netiface.links():
        left_points = qtpoint2point(link.leftBreakPoint3Ds())
        right_points = qtpoint2point(link.rightBreakPoint3Ds())
        unity_info["Driving"] += create_curve(left_points, right_points)
    for connector in netiface.connectors():
        for laneConnector in connector.laneConnectors():
            left_points = qtpoint2point(laneConnector.leftBreakPoint3Ds())
            # 防止 nan 情况发生(长度为0的情况)
            left_points = [_ for _ in left_points if not math.isnan(_[2])]
            right_points = qtpoint2point(laneConnector.rightBreakPoint3Ds())
            unity_info["Driving"] += create_curve(left_points, right_points)

    # 绘制左右边界线
    for link in netiface.links():
        lanes = list(link.lanes())
        for index, lane in enumerate(lanes):
            if index == 0:
                # 最右侧车道绘制右侧边界(白色实线)
                base_points = qtpoint2point(link.rightBreakPoint3Ds())
                left_points, right_points = calc_boundary(base_points, border_line_width)
                unity_info['WhiteLine'] += create_curve(left_points, right_points)
            # 所有车道绘制左侧边界
            if lane == lanes[-1]:
                # 最左侧车道绘制黄色实线
                base_points = qtpoint2point(link.leftBreakPoint3Ds())
                left_points, right_points = calc_boundary(base_points, border_line_width)
                unity_info['YellowLine'] += create_curve(left_points, right_points)
            elif lane.actionType() != lanes[index+1].actionType():
                # 左侧相邻车道类型不一致，绘制白色实线
                base_points = qtpoint2point(link.leftBreakPoint3Ds())
                left_points, right_points = calc_boundary(base_points, border_line_width)
                unity_info['WhiteLine'] += create_curve(left_points, right_points)
            else:
                # TODO 绘制白色虚线
                base_points = qtpoint2point(link.leftBreakPoint3Ds())
                left_points, right_points = calc_boundary(base_points, border_line_width)
                unity_info['WhiteLine'] += create_curve(left_points, right_points, split=True)

    unity_count = {}
    for key, value in unity_info.items():
        unity_info[key] = [{'pointsArray': info, 'drawOrder': [i for i in range(len(info))], 'count': int(len(info))}
                           for info in chunk(value, 60000)]
        unity_count[key] = len(unity_info[key])
    return unity_info
