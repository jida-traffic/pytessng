import collections
import datetime
import xml.dom.minidom
from tess2xodr import Road, Connector


class Doc:
    def __init__(self):
        # 只会记录路段，不会记录连接段
        self.link_node_mapping = collections.defaultdict(lambda: {'node': None, 'lanes_node': {}, })
        self.connector_node_mapping = collections.defaultdict(lambda: {'node': None, 'lanes_node': {}, })
        self.doc = xml.dom.minidom.Document()
        self.junction_node_mapping = {}

    # TODO 全局不考虑section
    def init_doc(self, header_info=None):
        # 创建一个根节点Managers对象
        root = self.doc.createElement('OpenDRIVE')
        self.doc.appendChild(root)

        # 创建头节点
        header = self.doc.createElement('header')
        root.appendChild(header)
        header.setAttribute('name', '')
        header.setAttribute('date', str(datetime.datetime.now()))

        geoReference = self.doc.createElement('geoReference')
        header.appendChild(geoReference)

        userData = self.doc.createElement('userData')
        header.appendChild(userData)


    def add_junction(self, junctions):
        root = self.doc.getElementsByTagName('OpenDRIVE')[0]
        for junction in junctions:
            junction_node = self.doc.createElement('junction')
            root.appendChild(junction_node)
            junction_node.setAttribute('id', str(junction.tess_id))
            self.junction_node_mapping[junction.tess_id] = junction_node


    def add_road(self, roads):
        root = self.doc.getElementsByTagName('OpenDRIVE')[0]
        for road in roads:
            road_node = self.doc.createElement('road')
            root.appendChild(road_node)
            # 添加 link 映射
            if road.type == 'link':
                self.link_node_mapping[road.tess_id]['node'] = road_node

            road_node.setAttribute('name', f"Road_{road.id}")
            road_node.setAttribute('id', str(road.id))
            road_node.setAttribute('length', str(road.length))
            road_node.setAttribute('junction', str(-1))

            # 高程
            elevationProfile_node = self.doc.createElement('elevationProfile')
            road_node.appendChild(elevationProfile_node)

            for elevation in road.elevations:
                elevation_node = self.doc.createElement('elevation')
                elevationProfile_node.appendChild(elevation_node)

                elevation_node.setAttribute('s', str(elevation.s))
                elevation_node.setAttribute('a', str(elevation.a))
                elevation_node.setAttribute('b', str(elevation.b))
                elevation_node.setAttribute('c', str(elevation.c))
                elevation_node.setAttribute('d', str(elevation.d))

            # 超高程
            lateralProfile_node = self.doc.createElement('lateralProfile')
            road_node.appendChild(lateralProfile_node)

            # 参考线
            planView_node = self.doc.createElement('planView')
            road_node.appendChild(planView_node)
            for geometry in road.geometrys:
                geometry_node = self.doc.createElement('geometry')
                planView_node.appendChild(geometry_node)

                # 添加参考线
                geometry_node.setAttribute('s', str(geometry.s))
                geometry_node.setAttribute('x', str(geometry.x))
                geometry_node.setAttribute('y', str(geometry.y))
                geometry_node.setAttribute('hdg', str(geometry.hdg))
                geometry_node.setAttribute('length', str(geometry.length))

                # 添加线条
                line_node = self.doc.createElement('line')
                geometry_node.appendChild(line_node)

            # 车道信息
            lanes_node = self.doc.createElement('lanes')
            road_node.appendChild(lanes_node)
            # 中心车道偏移
            for lane_offset in road.lane_offsets:
                laneOffset_node = self.doc.createElement('laneOffset')
                lanes_node.appendChild(laneOffset_node)

                laneOffset_node.setAttribute('s', str(lane_offset.s))
                laneOffset_node.setAttribute('a', str(lane_offset.a))
                laneOffset_node.setAttribute('b', str(lane_offset.b))
                laneOffset_node.setAttribute('c', str(lane_offset.c))
                laneOffset_node.setAttribute('d', str(lane_offset.d))

            laneSection_node = self.doc.createElement('laneSection')
            lanes_node.appendChild(laneSection_node)

            laneSection_node.setAttribute('s', "0")

            # 添加中心车道,左侧车道，右侧车道
            center_node = self.doc.createElement('center')
            right_node = self.doc.createElement('right')
            left_node = self.doc.createElement('left')
            laneSection_node.appendChild(center_node)
            laneSection_node.appendChild(right_node)
            laneSection_node.appendChild(left_node)

            # 计算并添加所有的车道
            all_lane_node = []
            for lane in road.lanes:
                lane_node = self.doc.createElement('lane')
                eval(f'{lane["direction"]}_node').appendChild(lane_node)
                all_lane_node.append(lane_node)    # 从右向左排序

                # 添加车道信息到映射表
                if road.type == 'link' and lane['lane']:
                    self.link_node_mapping[road.tess_id]['lanes_node'][lane['lane'].number()] = lane_node

                lane_node.setAttribute('id', str(lane['id']))
                lane_node.setAttribute('level', "false")
                lane_node.setAttribute('type', lane['type'])

                link_node = self.doc.createElement('link')
                lane_node.appendChild(link_node)

                road_mark_node = self.doc.createElement('roadMark')
                lane_node.appendChild(road_mark_node)

                road_mark_node.setAttribute('sOffset', "0")

                # 添加车道宽度信息
                for width in lane['width']:
                    width_node = self.doc.createElement('width')
                    lane_node.appendChild(width_node)

                    width_node.setAttribute('sOffset', str(width.s))
                    width_node.setAttribute('a', str(width.a))
                    width_node.setAttribute('b', str(width.b))
                    width_node.setAttribute('c', str(width.c))
                    width_node.setAttribute('d', str(width.d))

            # 此时所有的基础路段(link)已经建立完成,对于连接段需要同步填充lanelink信息
            if road.type == 'connector':
                # 获取前置/后续连接关系
                from_link = road.fromLink
                to_link = road.toLink
                from_road_node_info = self.link_node_mapping[from_link.id()]
                to_road_node_info = self.link_node_mapping[to_link.id()]

                junction_node = self.junction_node_mapping[road.junction.tess_id]
                from_road_node = from_road_node_info['node']
                to_road_node = to_road_node_info['node']
                # 添加 junction_id
                road_node.setAttribute('junction', junction_node.getAttribute('id'))

                # 分别建立来路/去路的连接关系，即每对连接关系建立 两个 connection
                # 来路作为来路/去路 from_road_node/to_road_node
                for incoming_road_node in [from_road_node, to_road_node]:
                    connection_node = self.doc.createElement('connection')
                    junction_node.appendChild(connection_node)
                    contactPoint = 'start' if incoming_road_node == from_road_node else 'end'

                    # 建立基础的 连接node(无连接关系)
                    connection_node.setAttribute('id', str(road.junction.connection_count))
                    road.junction.connection_count += 1
                    connection_node.setAttribute('incomingRoad', incoming_road_node.getAttribute('id'))
                    connection_node.setAttribute('connectingRoad', road_node.getAttribute('id'))
                    connection_node.setAttribute('contactPoint', contactPoint)

                    # 查询连接关系
                    laneConnector = road.laneConnector
                    # 寻找 来路/去路 node
                    incoming_road_node_info = from_road_node_info if contactPoint == 'start' else to_road_node_info
                    incoming_lane_number = laneConnector.fromLane().number() if contactPoint == 'start' else laneConnector.toLane().number()
                    incoming_lane_node = incoming_road_node_info['lanes_node'][incoming_lane_number]  # 来路/去路 node

                    # 连接段上只会有一个右侧的车道 + 中心车道
                    connector_lane_node = right_node.childNodes[0]

                    # 创建 laneLink
                    laneLink_node = self.doc.createElement('laneLink')
                    connection_node.appendChild(laneLink_node)
                    laneLink_node.setAttribute('from', incoming_lane_node.getAttribute('id'))
                    laneLink_node.setAttribute('to', connector_lane_node.getAttribute('id'))
