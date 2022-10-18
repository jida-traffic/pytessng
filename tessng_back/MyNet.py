import math
import numpy
import collections
from utils import line2surface
from PySide2.QtGui import QVector3D
from numpy import sqrt
from Tessng import PyCustomerNet, tngIFace, m2p
from functools import reduce


# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 创建路网
    def createNet(self):
        import shapefile
        import dbfread
        from pyproj import Proj
        p = Proj('+proj=tmerc +lon_0=120.3348024 +lat_0=33.2927492 +ellps=WGS84')

        iface = tngIFace()
        netiface = iface.netInterface()

        def get_coo_list(vertices):
            list1 = []
            x_move, y_move = 0, 0
            for index in range(0, len(vertices), 1):
                vertice = vertices[index]
                list1.append(QVector3D(m2p((vertice[0] - x_move)), m2p(-(vertice[1] - y_move)), m2p(vertice[2])))
            if len(list1) < 2:
                raise 3
            return list1


        # import osm2gmns as og
        # net = og.getNetFromOSMFile(file_path)
        # og.outputNetToCSV(net, output_folder='osm_file')
        # 通过经纬度定义原点
        # TODO 高程测试
        link_point = [(i, 0, i // 5000 * 1000) for i in range(10000)]
        lane_points = {
            'right': [(i, 0, i // 5000 * 1000) for i in range(10000)],
            'center': [(i, 100, i // 5000 * 1000) for i in range(10000)],
            'left': [(i, 200, i // 5000 * 1000) for i in range(10000)],
        }
        print(lane_points)
        lCenterLinePoint = get_coo_list(link_point)
        lanesWithPoints = [
            {
                'left': get_coo_list(lane['left']),
                'center': get_coo_list(lane['center']),
                'right': get_coo_list(lane['right']),
            } for lane in [lane_points]
        ]

        # 创建路段
        netiface.createLinkWithLaneWidth(lCenterLinePoint, [m2p(2), m2p(5)], 'test')
        # link_obj = netiface.createLink3DWithLanePoints(lCenterLinePoint, lanesWithPoints)
        # print(link_obj.leftBreakPoint3Ds())
        return

        # 创建感动科技高速路网
        filename = 'read_info/感动科技/步凤枢纽区域高速路网/bufeng_intchg_jshw.dbf'
        dbf_rows = dbfread.DBF(filename, encoding='utf-8')
        dbf_rows = list(dbf_rows)

        filename = 'read_info/感动科技/步凤枢纽区域高速路网/bufeng_intchg_jshw.shp'
        file = shapefile.Reader(filename)
        border = file.shapes()

        # 记录连接关系
        def default_dict_1():
            return {
                'start': [],
                'end': []
            }
        def default_dict_2():
            return {
                'successor_ids': set(),
                'predecessor_ids': set(),
            }
        connect_points = collections.defaultdict(default_dict_1)
        for index, road in enumerate(border):
            dbf_info = dbf_rows[index]
            if len(road.points) >= 2:
                connect_points[road.points[0]]['start'].append(road.oid)
                connect_points[road.points[-1]]['end'].append(road.oid)
        connect_info = collections.defaultdict(default_dict_2)
        for point in connect_points.values():
            for start in point['start']:
                for end in point['end']:
                    connect_info[end]['successor_ids'].add(start)  # 点为路段的起始点，则为下一路段
                    connect_info[start]['predecessor_ids'].add(end)  # 点为路段的终点，则为上一路段

        roads_info = {}
        for index, road in enumerate(border):
            dbf_info = dbf_rows[index]
            # 定义 干线/支线 的 精度 以及在连接时的 过渡长度
            if dbf_info['fclass'] == 'motorway':
                step_length = 30
                remove_count = 1
            else:
                step_length = 10
                remove_count = 5

            lane_count = reduce(lambda x, y: int(x) + int(y), dbf_info["lane"].split('|'))
            link_points = [(*p(*point), 0) for point in road.points]

            # 将点序列重新增加断点，以便创建连接段
            new_link_points = []
            for index in range(1, len(link_points)):
                # 至少要三步四个断点，保证至少前后一步，中间一步 ，不需要这个
                steps = max(math.ceil(sqrt((link_points[index][0] - link_points[index-1][0]) ** 2 + (link_points[index][1] - link_points[index-1][1]) ** 2) // step_length), 3)
                new_link_points.extend(numpy.linspace(start=link_points[index-1], stop=link_points[index], num=steps, endpoint=False))
            new_link_points.append(link_points[-1]) #加上最后一个点

            # 重置中心线断点序列，移除前后几个点用来创建连接段
            remove_count = min(remove_count, len(new_link_points) // 2 - 1)
            link_points = new_link_points[remove_count:-remove_count]

            # 计算车道点位
            lanes_points = []
            lane_width = 4  # 定义车道宽度
            for i in range(lane_count):
                lane_point = line2surface(link_points, {
                    "right": ['right', lane_width * i],
                    "center": ['right', lane_width * i - lane_width/2],
                    "left": ['right', lane_width * (i - 1)],
                })
                lanes_points.insert(0, lane_point)

            lCenterLinePoint = get_coo_list(link_points)
            lanesWithPoints = [
                {
                    'left': get_coo_list(lane['left']),
                    'center': get_coo_list(lane['center']),
                    'right': get_coo_list(lane['right']),
                } for lane in lanes_points
            ]
            # 创建 路段
            link_obj = netiface.createLink3DWithLanePoints(lCenterLinePoint, lanesWithPoints,
                                                           f"{dbf_info['osm_id']}-{dbf_info['fclass']}")
            roads_info[road.oid] = link_obj

        # 创建连接段
        for road_id, value in connect_info.items():
            # 只向后续路段获取连接关系
            from_link = roads_info[road_id]
            for successor_id in value['successor_ids']:
                to_link = roads_info[successor_id]
                from_lane_numbers = [lane.number() + 1 for lane in from_link.lanes()]
                to_lane_numbers = [lane.number() + 1 for lane in to_link.lanes()]

                # 匹配最多连接
                # max_lane_count = max(len(to_lane_numbers), len(from_lane_numbers))
                # from_lane_numbers = from_lane_numbers + [from_lane_numbers[-1]] * (max_lane_count - len(from_lane_numbers))
                # to_lane_numbers = to_lane_numbers + [to_lane_numbers[-1]] * (max_lane_count - len(to_lane_numbers))
                # 匹配最少连接
                min_lane_count = min(len(to_lane_numbers), len(from_lane_numbers))
                from_lane_numbers = from_lane_numbers[:min_lane_count]
                to_lane_numbers = to_lane_numbers[:min_lane_count]
                netiface.createConnector(from_link.id(), to_link.id(), from_lane_numbers, to_lane_numbers)

    def afterLoadNet(self):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # 设置场景大小
        # netiface.setSceneSize(10000, 10000)
        # netiface.setNetAttrs("S32路网", "OPENDRIVE")  #setNetAttrs
        # self.createNet()
