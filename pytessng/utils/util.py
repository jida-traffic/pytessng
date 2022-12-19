from Tessng import *
from PySide2.QtGui import *

def qtpoint2point(qtpoints):
    points = []
    for qtpoint in qtpoints:
        points.append(
            [m2p(qtpoint.x()), - m2p(qtpoint.y()), m2p(qtpoint.z())] if isinstance(qtpoint, QVector3D) else qtpoint
        )
    return points

def point2qtpoint(points):
    qtpoints = []
    for point in points:
        qtpoints.append(
            QVector3D(p2m(point[0]), - p2m(point[1]), p2m(point[2])) if not isinstance(point, QVector3D) else point
        )
    return qtpoints