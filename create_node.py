import collections
import datetime
import xml.dom.minidom

from tess2xodr import Road, Connector

# 只会记录路段，不会记录连接段
link_node_mapping = collections.defaultdict(lambda: {'node': None, 'lanes_node': {}, })
connector_node_mapping = collections.defaultdict(lambda: {'node': None, 'lanes_node': {}, })


# TODO 全局不考虑section
def init_doc(header_info):
    doc = xml.dom.minidom.Document()

    # 创建一个根节点Managers对象
    root = doc.createElement('OpenDRIVE')
    doc.appendChild(root)


    # 创建头节点
    header = doc.createElement('header')
    root.appendChild(header)
    header.setAttribute('name', '')
    header.setAttribute('date', str(datetime.datetime.now()))

    geoReference = doc.createElement('geoReference')
    header.appendChild(geoReference)

    userData = doc.createElement('userData')
    header.appendChild(userData)
    return doc


junction_node_mapping = {}
def add_junction(doc, junctions):
    root = doc.getElementsByTagName('OpenDRIVE')[0]
    for junction in junctions:
        junction_node = doc.createElement('junction')
        root.appendChild(junction_node)
        junction_node.setAttribute('id', str(junction.tess_id))
        junction_node_mapping[junction.tess_id] = junction_node
    return doc



def add_road(doc, roads):
    root = doc.getElementsByTagName('OpenDRIVE')[0]
    for road in roads:
        print(road.id)
        road_node = doc.createElement('road')
        root.appendChild(road_node)
        # 添加 link 映射
        if isinstance(road, Road):
            link_node_mapping[road.tess_id]['node'] = road_node
        else:
            connector_node_mapping[road.tess_id]['node'] = road_node

        road_node.setAttribute('name', f"Road_{road.id}")
        road_node.setAttribute('id', str(road.id))
        road_node.setAttribute('length', str(road.length))
        road_node.setAttribute('junction', str(-1))

        # 高程
        elevationProfile_node = doc.createElement('elevationProfile')
        road_node.appendChild(elevationProfile_node)

        # 超高程
        lateralProfile_node = doc.createElement('lateralProfile')
        road_node.appendChild(lateralProfile_node)

        # 参考线
        planView_node = doc.createElement('planView')
        road_node.appendChild(planView_node)
        for geometry in road.geometrys:
            geometry_node = doc.createElement('geometry')
            planView_node.appendChild(geometry_node)

            # 添加参考线
            geometry_node.setAttribute('s', str(geometry.s))
            geometry_node.setAttribute('x', str(geometry.x))
            geometry_node.setAttribute('y', str(geometry.y))
            geometry_node.setAttribute('hdg', str(geometry.hdg))
            geometry_node.setAttribute('length', str(geometry.length))

            # 添加线条
            line_node = doc.createElement('line')
            geometry_node.appendChild(line_node)

        # 车道信息
        lanes_node = doc.createElement('lanes')
        road_node.appendChild(lanes_node)
        # 中心车道偏移
        for lane_offset in road.lane_offsets:
            laneOffset_node = doc.createElement('laneOffset')
            lanes_node.appendChild(laneOffset_node)

            laneOffset_node.setAttribute('s', str(lane_offset.s))
            laneOffset_node.setAttribute('a', str(lane_offset.a))
            laneOffset_node.setAttribute('b', str(lane_offset.b))
            laneOffset_node.setAttribute('c', str(lane_offset.c))
            laneOffset_node.setAttribute('d', str(lane_offset.d))

        laneSection_node = doc.createElement('laneSection')
        lanes_node.appendChild(laneSection_node)

        laneSection_node.setAttribute('s', "0")

        # 添加中心车道,左侧车道，右侧车道
        center_node = doc.createElement('center')
        right_node = doc.createElement('right')
        left_node = doc.createElement('left')
        laneSection_node.appendChild(center_node)
        laneSection_node.appendChild(right_node)
        laneSection_node.appendChild(left_node)

        all_lane_node = []
        for lane in road.lanes:
            lane_node = doc.createElement('lane')
            eval(f'{lane["direction"]}_node').appendChild(lane_node)
            all_lane_node.append(lane_node)    # 从右向左排序

            # 添加车道信息到映射表
            if isinstance(road, Road) and lane['lane']:
                link_node_mapping[road.tess_id]['lanes_node'][lane['lane'].number()] = lane_node
            # else:
            #     connector_node_mapping[road.tess_id]['lanes_node'][lane['lane'].number()] = lane_node

            lane_node.setAttribute('id', str(lane['id']))
            lane_node.setAttribute('level', "false")
            lane_node.setAttribute('type', lane['type'])

            link_node = doc.createElement('link')
            lane_node.appendChild(link_node)

            roadMark_node = doc.createElement('roadMark')
            lane_node.appendChild(roadMark_node)

            roadMark_node.setAttribute('sOffset', "0")

            for width in lane['width']:
                width_node = doc.createElement('width')
                lane_node.appendChild(width_node)

                width_node.setAttribute('sOffset', str(width.s))
                width_node.setAttribute('a', str(width.a))
                width_node.setAttribute('b', str(width.b))
                width_node.setAttribute('c', str(width.c))
                width_node.setAttribute('d', str(width.d))

        # 此时所有的基础路段(link已经建立完成)
        if isinstance(road, Connector):
            # 获取前置/后续连接关系
            from_link = road.fromLink
            to_link = road.toLink
            from_road_node_info = link_node_mapping[from_link.id()]
            to_road_node_info = link_node_mapping[to_link.id()]

            junction_node = junction_node_mapping[road.junction.tess_id]
            from_road_node = from_road_node_info['node']
            to_road_node = to_road_node_info['node']
            # 添加 junction_id
            road_node.setAttribute('junction', junction_node.getAttribute('id'))

            # 每组连接关系建立两对 connection
            # 来路作为来路 from_road_node
            for incoming_road_node in [from_road_node, to_road_node]:
                connection_node = doc.createElement('connection')
                junction_node.appendChild(connection_node)

                if incoming_road_node == from_road_node:
                    contactPoint = 'start'
                else:
                    contactPoint = 'end'


                connection_node.setAttribute('id', str(road.junction.connection_count))
                road.junction.connection_count += 1
                connection_node.setAttribute('incomingRoad', incoming_road_node.getAttribute('id'))
                connection_node.setAttribute('connectingRoad', road_node.getAttribute('id'))
                connection_node.setAttribute('contactPoint', contactPoint)

                from_lane_numbers, to_lane_numbers = set(), set()
                for laneConnector in road.connector.laneConnectors():
                    from_lane_numbers.add(laneConnector.fromLane().number())
                    to_lane_numbers.add(laneConnector.toLane().number())
                from_lane_numbers = sorted(list(from_lane_numbers))
                to_lane_numbers = sorted(list(to_lane_numbers))

                for laneConnector in road.connector.laneConnectors():
                    incoming_road_node_info = from_road_node_info if contactPoint == 'start' else to_road_node_info
                    incoming_lane_number = laneConnector.fromLane().number() if contactPoint == 'start' else laneConnector.toLane().number()
                    incoming_lane_node = incoming_road_node_info['lanes_node'][incoming_lane_number]

                    # 来路在其所在连接段的车道位置
                    incoming_lane_index = from_lane_numbers.index(incoming_lane_number) if contactPoint == 'start' else to_lane_numbers.index(incoming_lane_number)

                    incoming_lane_id = incoming_lane_node.getAttribute('id')

                    # 被连接的车道（连接段上）,取右侧车道，反序列获取,连接段没有车道编号，所以直接采用下标顺序获取一个
                    connector_lane_count = len(right_node.childNodes)  # 车道数取的是前后被连接道路的最大数量
                    # connector_lane_id = right_node.childNodes[connector_lane_count - incoming_lane_index - 1].getAttribute('id')
                    connector_lane_id = right_node.childNodes[- incoming_lane_index - 1].getAttribute('id')

                    laneLink_node = doc.createElement('laneLink')
                    connection_node.appendChild(laneLink_node)

                    laneLink_node.setAttribute('from', incoming_lane_id)
                    laneLink_node.setAttribute('to', connector_lane_id)
                    # successor_node = doc.createElement('successor')
                    # link_node.appendChild(successor_node)



                # for laneConnector in road.connector.laneConnectors():
                #     from_lane_number, to_lane_number = laneConnector.fromLane().number(), laneConnector.toLane().number()
                #     from_lane_node = from_road_node_info['lanes'][from_lane_number]
                #     to_lane_node = to_road_node_info['lanes'][to_lane_number]
                #
                #     # connector_lane_node = right_node[max(from_lane_number, to_lane_number)] # 本来想用最左边的
                #     from_lane_id = from_lane_node.getAttribute('id')
                #     connector_lane_id = right_node[from_lane_number].getAttribute('id')



            # # 在 连接段（road） 上 添加路段连接关系
            # link_node = doc.createElement('link')
            # road_node.appendChild(link_node)
            #
            # predecessor_node = doc.createElement('predecessor')
            # link_node.appendChild(predecessor_node)
            #
            # predecessor_node.setAttribute('contactPoint', 'stop')
            # predecessor_node.setAttribute('elementId', from_road_node.getAttribute('id'))
            #
            # successor_node = doc.createElement('successor')
            # link_node.appendChild(successor_node)
            #
            # successor_node.setAttribute('contactPoint', 'start')
            # successor_node.setAttribute('elementId', to_road_node.getAttribute('id'))

            # TODO 暂时不为 前置/后续 路段添加连接信息
            # link_node = doc.createElement('link')
            # from_road_node.appendChild(link_node)
            #
            # predecessor_node = doc.createElement('predecessor')
            # predecessor_node.setAttribute('a', str(width.a))

            # # 1.5 仅支持车道多前后继，不支持道路多前后继，1.4 都不支持，所以在此处我们全采用junction
            # for laneConnector in road.connector.laneConnectors():
            #     from_lane_number, to_lane_number = laneConnector.fromLane().number(), laneConnector.toLane().number()
            #     from_lane_node = from_road_node_info['lanes'][from_lane_number]
            #     to_lane_node = to_road_node_info['lanes'][to_lane_number]
            #
            #     connector_lane_node = right_node[max(from_lane_number, to_lane_number)]
            #
            #     # 建立车道连接关系
            #     link_node = doc.createElement('link')
            #     connector_lane_node.appendChild(link_node)
            #
            #     predecessor_node = doc.createElement('predecessor')
            #     link_node.appendChild(predecessor_node)
            #     predecessor_node.setAttribute('id', from_lane_node.getAttribute('id'))
            #     predecessor_node = doc.createElement('predecessor')
            #     link_node.appendChild(predecessor_node)
            #     predecessor_node.setAttribute('id', from_lane_node.getAttribute('id'))

    # 记录所有的连接关系
    # doc.getElementById()
    return doc

