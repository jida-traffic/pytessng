import collections

from Tessng import PyCustomerNet, tngIFace
from basic_info.info import roads_info, lanes_info
from utils import get_coo_list, get_inter, Road, Section


# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 创建路网
    def createNet(self):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()

        road_mapping = dict()
        # 创建基础路段,数据原因，不考虑交叉口
        link_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] == -1]
        junction_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] != -1]
        # 创建所有的Link，一个road 通过多个section，左右来向分为多个Link
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] != -1:
                continue  # 先行创建所有的基本路段
            tess_road = Road(road_id)
            for section_id, section_info in road_info['lane_sections'].items():
                section_id = int(section_id)
                tess_section = Section(road_id, section_id, section_info['all'])
                tess_road.sections.append(tess_section)

                points = road_info['road_points'][str(section_id)]['points']

                # 存在左车道
                if section_info['left']:
                    # 车道排序，车道id为正，越大的越先在tess中创建，路段序列取反向参考线
                    land_ids = tess_section.left_lane_ids
                    lCenterLinePoint = get_coo_list([point["position"] for point in points][::-1])
                    lanesWithPoints = [
                        {
                            'left': get_coo_list(road_info['sections'][section_id]["lanes"][lane_id]['left_vertices'],
                                                 True),
                            'center': get_coo_list(
                                road_info['sections'][section_id]["lanes"][lane_id]['center_vertices'], True),
                            'right': get_coo_list(road_info['sections'][section_id]["lanes"][lane_id]['right_vertices'],
                                                  True),
                        }
                        for lane_id in land_ids  # if roads_info[road_id]['lanes'][lane_id]['type']=='driving'
                    ]

                    tess_section.left_link = netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints,
                                                                               f"{road_id}_{section_id}_left")
                    # return
                # 存在右车道
                if section_info['right']:
                    # 车道id为负，越小的越先在tess中创建
                    land_ids = sorted(section_info['right'], reverse=False)
                    lCenterLinePoint = get_coo_list([point["position"] for point in points])
                    lanesWithPoints = [
                        {
                            'left': get_coo_list(road_info['sections'][section_id]["lanes"][lane_id]['left_vertices']),
                            'center': get_coo_list(
                                road_info['sections'][section_id]["lanes"][lane_id]['center_vertices']),
                            'right': get_coo_list(
                                road_info['sections'][section_id]["lanes"][lane_id]['right_vertices']),
                        }
                        for lane_id in land_ids  # if roads_info[road_id]['lanes'][lane_id]['type']=='driving'
                    ]

                    tess_section.right_link = netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints,
                                                                                f"{road_id}_{section_id}_right")
                road_mapping[road_id] = tess_road


        # 创建所有的连接段,交叉口本身不作为车道，直接生成连接段
        # 多条车道属于一个road
        def default_dict():
            return {
                'lFromLaneNumber': [],
                'lToLaneNumber': [],
                'lanesWithPoints3': [],
                'infos': [],
            }

        connector_mapping = collections.defaultdict(default_dict)
        # 创建路段间的连接
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] != -1:
                continue

            # lane_sections 保存基本信息，sections 保存详情
            for section_id, section_info in road_info['sections'].items():
                # section_id = int(section_id)
                # tess_section = road_mapping[road_id].sections[section_id] # 通过下标即可获取section，但注意，需要保证所有的section都被导入了，否则需要通过id判断后准确获取

                # 路段间的连接段只向后连接,本身作为前路段(向前也一样，会重复一次)
                for lane_id, lane_info in section_info["lanes"].items():
                    # 633 路段，L18（-） 只有两个后续车道连接？？？ 已确认，yes
                    predecessor_id = lane_info['name']

                    # 为了和交叉口保持一致，重新获取一次相关信息
                    is_true, from_road_id, from_section_id, from_lane_id, _ = get_inter(predecessor_id)

                    if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                        continue

                    from_section = road_mapping[from_road_id].section(from_section_id)
                    from_link = from_section.tess_link(from_lane_id)
                    from_lane = from_section.tess_lane(from_lane_id)

                    for successor_id in lane_info["successor_ids"]:
                        is_true, to_road_id, to_section_id, to_lane_id, _ = get_inter(successor_id)
                        if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                            continue
                        if to_road_id not in link_road_ids:  # 只针对性的创建路段间的连接
                            continue

                        to_section = road_mapping[to_road_id].section(to_section_id)
                        to_link = to_section.tess_link(to_lane_id)
                        to_lane = to_section.tess_lane(to_lane_id)

                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'].append(
                            from_lane.number() + 1)
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'].append(
                            to_lane.number() + 1)
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'].append(
                            get_coo_list([lane_info['center_vertices'][-1],
                                          lanes_info[successor_id]['center_vertices'][0]]))  # 注意连接线方向
                        connector_mapping[f"{from_link.id()}-{to_link.id()}"]['infos'].append(
                            {
                                "predecessor_id": predecessor_id,
                                "successor_id": successor_id,
                                'junction': False,
                            }
                        )
        # return

        # 仅交叉口
        error_junction = []
        for road_id, road_info in roads_info.items():
            if road_info['junction_id'] == -1:
                continue
            for section_id, section_info in road_info['sections'].items():
                # 获取路口的所有连接关系
                for lane_id, lane_info in section_info["lanes"].items():
                    for predecessor_id in lane_info['predecessor_ids']:
                        is_true, from_road_id, from_section_id, from_lane_id, _ = get_inter(predecessor_id)
                        if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                            continue

                        from_section = road_mapping[from_road_id].section(from_section_id)
                        from_link = from_section.tess_link(from_lane_id)
                        from_lane = from_section.tess_lane(from_lane_id)

                        for successor_id in lane_info["successor_ids"]:
                            is_true, to_road_id, to_section_id, to_lane_id, _ = get_inter(successor_id)
                            if not is_true:  # 部分车道的连接关系可能是'2.3.None.-1'，需要清除
                                continue

                            to_section = road_mapping[to_road_id].section(to_section_id)
                            to_link = to_section.tess_link(to_lane_id)
                            to_lane = to_section.tess_lane(to_lane_id)

                            # TODO 交叉口可能产生自连接，记录并跳过
                            if from_road_id == to_road_id and from_section_id != to_section_id:
                                error_junction.append(
                                    {
                                        "lane": lane_info['name'],
                                        "predecessor": predecessor_id,
                                        "successor": successor_id,
                                    }
                                )
                                continue

                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'].append(
                                from_lane.number() + 1)
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'].append(
                                to_lane.number() + 1)

                            # 用前后车道的首尾坐标替换原有首尾坐标
                            connector_vertices = lanes_info[predecessor_id]['center_vertices'][-1:] + \
                                                 lane_info['center_vertices'][1:-1] + \
                                                 lanes_info[successor_id]['center_vertices'][:1]
                            # connector_vertices = lane_info['center_vertices']
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'].append(
                                get_coo_list(connector_vertices))  # 注意连接线方向
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['infos'].append(
                                {
                                    "predecessor_id": predecessor_id,
                                    "successor_id": successor_id,
                                    "lane_id": lane_info["name"],
                                    "connector_vertices": connector_vertices,
                                    'junction': True,
                                    "from_link": from_link,
                                    "to_link": to_link,
                                }
                            )

        # 创建所有的连接关系
        for link_id, link_info in connector_mapping.items():
            from_link_id = int(link_id.split('-')[0])
            to_link_id = int(link_id.split('-')[1])
            lFromLaneNumber = link_info['lFromLaneNumber']
            lToLaneNumber = link_info['lToLaneNumber']
            lanesWithPoints3 = link_info['lanesWithPoints3']

            types = set(i['junction'] for i in link_info['infos'])
            if True in types and False in types:
                link_type = 'all'
            elif True in types:
                link_type = 'junction'
            else:
                link_type = 'link'

            # 源数据建立连接
            netiface.createConnectorWithPoints(from_link_id, to_link_id,
                                               lFromLaneNumber, lToLaneNumber,
                                               lanesWithPoints3, f"{from_link_id}-{to_link_id}-{link_type}")
            # TESS 自动计算，建立连接
            # netiface.createConnector(from_link_id, to_link_id, lFromLaneNumber, lToLaneNumber)

        print(error_junction)

        # print(connector_mapping)
        # 创建连接段，自动计算断点
        # #connector2 = netiface.createConnector(link1.id(), link2.id(), lFromLaneNumber, lToLaneNumber)

    def afterLoadNet(self):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # 设置场景大小
        # netiface.setSceneSize(1000, 1000)  # 测试数据
        netiface.setSceneSize(4000, 1000)  # 华为路网
        # netiface.setSceneSize(4000, 1000)  # 深圳路网
        # 获取路段数
        count = netiface.linkCount()
        if (count == 0):
            self.createNet()
