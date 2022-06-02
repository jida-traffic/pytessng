from PySide2.QtCore import QPointF
from Tessng import m2p


class Section:
    def __init__(self, road_id, section_id, lane_ids: list):
        self.road_id = road_id
        self.id = section_id

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
        index = 0
        for lane in obj.lanes():  # tess 的车道列表是有序的
            self.lane_mapping[self.left_lane_ids[index]] = lane
            index += 1
        self._left_link = obj

    @property
    def right_link(self):
        return self._right_link

    @right_link.setter
    def right_link(self, obj):
        index = 0
        for lane in obj.lanes():
            self.lane_mapping[self.right_lane_ids[index]] = lane
            index += 1
        self._right_link = obj

    # def set_lanes(self, lane_ids):

    def tess_lane(self, lane_id):
        return self.lane_mapping[lane_id]

    def tess_link(self, lane_id):
        if lane_id > 0:
            return self.left_link
        else:
            return self.right_link


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
        # list1.append(QPointF(m2p(vertice[0] + 1500), m2p(-(vertice[1] + 500))))  # 深圳数据
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