import json
import os
import collections
from matlab import linspace, sqrt

import matplotlib.pyplot as plt
from commonroad.scenario.scenario import Scenario
from collections import defaultdict

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.network import Network
import csv


# TODO 注意对第三方包的修改 --> change_convert.py
def convert_opendrive(opendrive: OpenDrive, filter_types: list, roads_info, my_signal, pb) -> Scenario:
    road_network = Network()
    road_network.load_opendrive(opendrive)
    # TODO 在此处过滤车道类型
    # 精度 ParametricLaneGroup.to_lanelet(self, precision: float = 0.5)
    # 如果不传参数，将采取默认的过滤值 ["driving", "onRamp", "offRamp", "exit", "entry"]
    return road_network.export_commonroad_scenario(filter_types=filter_types, roads_info=roads_info, my_signal=my_signal, pb=pb)  # commonroad-io==2020.2 版本需要验证


def calc_elevation(pos, elevations):
    if not elevations:
        raise
    # 获取相应的 elevation
    for e in elevations:
        if pos >= e.start_pos:
            elevation = e
    a, b, c, d = elevation.polynomial_coefficients
    ds = pos - elevation.start_pos  # 每当新的元素出现，`ds`则清零
    high = a + b * ds + c * ds ** 2 + d * ds ** 3
    return high


def calc_width(l1, l2):
    width_list = []
    for index in range(len(l1)):
        width = sqrt((l1[index][0] - l2[index][0]) ** 2 + (l1[index][1] - l2[index][1]) ** 2)
        width_list.append(width)
    return width_list


def convert_roads_info(opendrive, filter_types, step_length):  # step_length需要对第三方包进行修改
    roads_info = {}
    for road in opendrive.roads:
        road_length = road.length
        planView = road.planView  # 每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
        road_points = {}
        # 为了适配tess，将road按照section切分为多个link
        for section in road.lanes.lane_sections:
            right_points = []
            left_points = []
            section_id = section.idx
            section_length = section.length
            section_sPos = section.sPos
            section_ePos = section_sPos + section_length

            steps = int(section_length // step_length + 2)  # steps >= 2
            lengths = list(linspace(section_sPos, section_ePos, steps))
            left_offsets = []
            right_offsets = []
            # lengths = list(road_section_distance[road.id][section_id].values())[0] # 尽量拟合路段与车道
            # 计算每一点的坐标和角度
            for length in lengths:
                right_length = length
                left_length = road_length - length
                if length > road_length:
                    right_length = road_length
                    left_length = 0
                right_position, right_angle = planView.calc_geometry(right_length)
                left_position, left_angle = planView.calc_geometry(left_length)
                right_points.append(
                    {
                        "position": list(right_position),
                        'angle': right_angle,
                        "offset": right_length,  # 记录在本section内此点的移动位置
                    }
                )
                left_points.append(
                    {
                        "position": list(left_position),
                        'angle': left_angle,
                        "offset": left_length,
                    }
                )
                left_offsets.append(left_length)
                right_offsets.append(right_length)

            # 左右方向参考线点计算不一样
            road_points[section_id] = {
                "right_points": right_points,
                "left_points": left_points,
                'sPos': section_sPos,
                'ePos': section_ePos,
                'length': section_length,
                'steps': steps,
                'lengths': lengths,
                "left_offsets": left_offsets,
                "right_offsets": right_offsets,
            }

        # 计算每一段section 的高程信息
        # 获取高程分段列表
        elevations = [elevation[0] for elevation in road.elevationProfile.elevations]
        for section_id, section_info in road_points.items():
            sPos = section_info["sPos"]
            ePos = section_info["ePos"]
            section_info["start_high"] = calc_elevation(sPos, elevations)
            section_info["end_high"] = calc_elevation(ePos, elevations)


        sections_mapping = convert_section_info(road.lanes.lane_sections, filter_types)
        # elevations [(e1),(e2),(e3)]  start_pos, road.elevationProfile.elevations[0][0].polynomial_coefficients
        roads_info[road.id] = {
            "name": road.name,
            "junction_id": road.junction and road.junction.id,  # -1 为非junction，此道路是在交叉口内部
            'road_points': road_points,  # 每个section 分开，方便微观处理,每条lane点位详情
            # 'geometry_center_vertices': geometry_center_vertices,
            'length': road_length,
            # 'start_high': road_start_high,
            # 'end_high': road_end_high,
            'lane_sections': sections_mapping,  # lane 概况
            # 路段边界作用不大，TESS是固定的车道宽度
        }

    return roads_info


def convert_lanes_info(opendrive, scenario, roads_info):
    # 获取 link与交叉口关系
    scenario_mapping = {
        "roads": {},
        "sections": {},
        "lanes": {},
    }
    for road in opendrive.roads:
        scenario_mapping["roads"][road.id] = road
        for sectionidx, section in enumerate(road.lanes.lane_sections):
            scenario_mapping["sections"][f"{road.id},{sectionidx}"] = section
            for lane in section.allLanes:
                scenario_mapping["lanes"][f"{road.id},{sectionidx},{lane.id}"] = lane
                if lane.id == 0: # 中心车道信息保存在road info中
                    roads_info[road.id]['lane_sections'][sectionidx]['center_lane'] = {
                        "lane_id": lane.id,
                        "road_marks": lane.road_marks,
                        "widths": lane.widths,
                    }

    # 获取道路与路段关系
    lanes_info = defaultdict(dict)
    # 中心车道未转换，用参考线代替
    for lane in scenario.lanelet_network.lanelets:
        if lane.stop_line:
            raise Exception("ccccccccccccccccccc 车辆停止线")

        # center_lane
        # 获取所在路段
        lane_name = lane.lanelet_id
        ids = lane_name.split('.')
        road_id = int(ids[0])
        section_id = int(ids[1])
        lane_id = int(ids[2])
        road_marks = scenario_mapping["lanes"][f"{road_id},{section_id},{lane_id}"].road_marks

        # 计算车道宽度
        center_vertices, left_vertices, right_vertices = lane.center_vertices.tolist(), lane.left_vertices.tolist(), lane.right_vertices.tolist()
        widths = calc_width(left_vertices, right_vertices)

        # lane.lanelet_id 自定义的车道编号,取消转换后，指的就是原始编号
        lanes_info[lane.lanelet_id] = {
            "road_id": road_id,
            "section_id": section_id,
            "lane_id": lane_id,
            "left": {
                "lane_id": lane.adj_left,
                "same_direction": lane.adj_left_same_direction,
            },
            "right": {
                "lane_id": lane.adj_right,
                "same_direction": lane.adj_right_same_direction,
            },
            "predecessor_ids": lane.predecessor,
            "successor_ids": lane.successor,
            "type": lane.type,
            "name": lane_name,  # road_id+lane_section+lane_id+-1
            "center_vertices": center_vertices,
            "left_vertices": left_vertices,
            "right_vertices": right_vertices,
            "widths": widths,
            "road_marks": road_marks,
            'traffic_lights': list(lane.traffic_lights),
            'traffic_signs': list(lane.traffic_signs),
            'distance': list(lane.distance),
        }

    # 车道ID，中心车道为0， 正t方向升序，负t方向降序(基本可理解为沿参考线从左向右下降)
    return lanes_info


def lane_restrictions(lane):
    speed_info = []
    access_info = []
    for speed in lane.getElementsByTagName('speed'):
        speed_info.append(
            {
                "sOffset ": speed.getAttribute("sOffset"),
                "max": float(speed.getAttribute("max")),
                "unit": speed.getAttribute("unit"),
            }
        )
    for access in lane.getElementsByTagName('access'):
        access_info.append(
            {
                "sOffset ": access.getAttribute("sOffset"),
                "rule ": access.getAttribute("rule"),
                "restriction ": access.getAttribute("restriction"),
            }
        )
    return {
        "speeds": speed_info,
        'accesss': access_info,
    }


def convert_section_info(sections, filter_types):
    # 车道信息
    def default_section():
        return {
            'right': [],
            'center': [],
            'left': [],
            'all': [],
            'infos': {}
        }

    sections_mapping = collections.defaultdict(default_section)
    for section in sections:
        section_id = sections.index(section)
        for lane in section.allLanes:
            if filter_types is not None and lane.type not in filter_types:
                continue
            if lane.id == 0:
                direction = 'center'
            elif lane.id >= 0:
                direction = 'left'
            else:
                direction = 'right'
            sections_mapping[section_id][direction].append(lane.id)
            # sections_mapping[index]['infos'][lane.id] = get_lane_restrictions(lane)

        sections_mapping[section_id]['all'] = sections_mapping[section_id]['right'] + sections_mapping[section_id]['left'] + sections_mapping[section_id]['center']
    # 缺少限制数据
    return sections_mapping
