import numpy as np

from pytessng.Tessng import m2p, p2m
from PySide2.QtGui import QVector3D


def get_coo_list(vertices):
    list1 = []
    x_move, y_move = 0, 0
    for index in range(0, len(vertices), 1):
        vertice = vertices[index]
        list1.append(QVector3D(m2p((vertice[0] - x_move)), m2p(-(vertice[1] - y_move)), m2p(vertice[2])))
    if len(list1) < 2:
        raise 3
    return list1


def qtpoint2point(qtpoints):
    points = []
    for qtpoint in qtpoints:
        points.append(
            [p2m(qtpoint.x()), - p2m(qtpoint.y()), p2m(qtpoint.z())] if isinstance(qtpoint, QVector3D) else qtpoint
        )
    return points


# 计算向量2相对向量1的旋转角度（-pi~pi）
def clockwise_angle(v1, v2):
    x1, y1 = v1.x, v1.y
    x2, y2 = v2.x, v2.y
    dot = x1 * x2 + y1 * y2
    det = x1 * y2 - y1 * x2
    theta = np.arctan2(det, dot)
    return theta