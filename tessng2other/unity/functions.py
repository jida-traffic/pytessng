from PySide2.QtGui import QVector3D
from pytessng.Tessng import p2m
from math import ceil, sqrt
from numpy import sqrt, square


def deviation_point(coo1, coo2, width, right=False, is_last=False):
    signl = 1 if right else -1  # 记录向左向右左右偏移
    x1, y1, z1, x2, y2, z2 = coo1 + coo2  # 如果是最后一个点，取第二个 点做偏移
    x_base, y_base, z_base = coo1 if not is_last else coo2
    if not ((x2 - x1) or (y2 - y1)):  # 分母为0
        return [x_base, y_base, z_base]
    X = x_base + signl * width * (y2 - y1) / sqrt(square(x2 - x1) + square((y2 - y1)))
    Y = y_base + signl * width * (x1 - x2) / sqrt(square(x2 - x1) + square((y2 - y1)))
    return [X, Y, z_base]

def xyz2xzy(array):
    return [array[0], array[2], array[1]]

# 根据左右点序列创建三角形
def create_curve(left_points, right_points, split=False):
    curves = []
    for index, distance in enumerate(left_points[:-1]):  # 两两组合，最后一个不可作为首位

        # TODO 断线时，需要细分路段，做到步长均匀
        # if split and index % 10 in [0, 1, 2, 3]:
            # 断线 3:2 虚线长度由步长和比例共同控制
            # continue

        left_0, left_1, right_0, right_1 = left_points[index], left_points[index + 1], right_points[index], \
                                           right_points[index + 1]
        coo_0 = [xyz2xzy(left_0), xyz2xzy(left_1), xyz2xzy(right_0)]
        coo_1 = [xyz2xzy(left_1), xyz2xzy(right_1), xyz2xzy(right_0)]
        curves += coo_0 + coo_1
    return curves

def chunk(lst, size):
    return list(
        map(lambda x: lst[x * size:x * size + size],
            list(range(0, ceil(len(lst) / size)))))

def qtpoint2point(qtpoints):
    points = []
    for qtpoint in qtpoints:
        points.append(
            [p2m(qtpoint.x()), - p2m(qtpoint.y()), p2m(qtpoint.z())] if isinstance(qtpoint, QVector3D) else qtpoint
        )
    return points

