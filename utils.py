from PySide2.QtCore import QPointF
from Tessng import m2p


class Section:
    def __init__(self, road_id, section_id, lane_ids: list):
        self.road_id = road_id
        self.id = section_id
        # if road_id == 2 and section_id == 2:
        #     lane_ids.remove(-5)

        self._left_link = None
        self._right_link = None
        self.lane_ids = list(lane_ids or [])
        # 左右来向的车道id分别为正负， 需要根据tess的规则进行排序
        self.left_lane_ids = sorted(filter(lambda i: i > 0, self.lane_ids, ), reverse=True)
        self.right_lane_ids = sorted(filter(lambda i: i < 0, self.lane_ids, ), reverse=False)
        self.lane_mapping = {}

    @property
    def left_link(self):
        return self._left_link

    @left_link.setter
    def left_link(self, obj):
        # for link_info in obj:
        #     link = link_info['link']
        #     lane_ids = link_info['lane_ids']
        #     index = 0
        #     for lane in link.lanes():  # tess 的车道列表是有序的
        #         self.lane_mapping[self.left_lane_ids[index]] = lane
        #         index += 1
        for link_info in obj:
            link = link_info['link']
            lane_ids = link_info['lane_ids']
            index = 0
            for lane in link.lanes():
                link_info[lane_ids[index]] = lane
                index += 1

        self._left_link = obj

    @property
    def right_link(self):
        return self._right_link

    @right_link.setter
    def right_link(self, obj):
        # is_t = False
        for link_info in obj:
            link = link_info['link']
            lane_ids = link_info['lane_ids']
            index = 0
            for lane in link.lanes():
                link_info[lane_ids[index]] = lane
                index += 1

        self._right_link = obj

    # def set_lanes(self, lane_ids):

    def tess_lane(self, lane_id, type):
        if lane_id > 0:
            if type == 'from':
                link_info = self.left_link[-1]
            else:
                link_info = self.left_link[0]
        else:
            if type == 'from':
                link_info = self.right_link[-1]
            else:
                link_info = self.right_link[0]
        return link_info.get(lane_id)

    def tess_link(self, lane_id, type):
        if lane_id > 0:
            if type == 'from':
                return self.left_link[-1]['link']
            else:
                return self.left_link[-0]['link']
        else:
            if type == 'from':
                return self.right_link[-1]['link']
            else:
                return self.right_link[0]['link']



class Road:
    def __init__(self, road_id):
        self.id = road_id
        self.sections = []

    def section(self, section_id: int = None):
        if section_id is None:
            return self.sections
        else:
            for section in self.sections:
                if section.id == section_id:
                    return section
            # return self.sections[section_id]

    def section_append(self, section: Section):
        self.sections.append(section)
        self.sections.sort(key=lambda i: i.id)


def get_coo_list(vertices, is_link=False):
    # TODO 路段线与车道线的密度保持一致
    list1 = []
    for index in range(0, len(vertices), 1):
        vertice = vertices[index]
        # list1.append(QPointF(m2p(vertice[0] + 2000), m2p(-(vertice[1] + 0))))  # 深圳数据
        list1.append(QPointF(m2p(vertice[0] - 2000), m2p(-(vertice[1] - 1500))))  # 华为路网
        # list1.append(QPointF(m2p(vertice[0] + 1700), m2p(-(vertice[1] - 2500))))  # 测试数据
    return list1


def get_inter(string):
    inter_list = []
    is_true = True
    for i in string.split('.'):
        try:
            inter_list.append(int(i))
        except:
            inter_list.append(None)
            is_true = False
    return [is_true, *inter_list]


class Child:
    def __init__(self, data):
        self.points = data
        self.childs = []

    def covert_network(self):
        self.get_link()

    def get_link(self, start_index=0):
        link_start = None
        for index in range(start_index, len(self.points)):
            point = self.points[index]
            if link_start is None and point['type'] == 'link':
               link_start = index
            if link_start is not None and (point['type'] != 'link' or index == len(self.points) - 1):
                self.childs.append({
                    'index': [link_start, index],
                    'lanes': self.points[index-1]['lane_ids']
                })
                return self.get_link(index+1)
