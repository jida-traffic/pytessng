import os
import json
from lxml import etree
from opendrive2lanelet.opendriveparser.parser import parse_opendrive
from utils.opendrive_info.utils import convert_opendrive, convert_roads_info, write_lanes, convert_lanes_info, write_roads


# def main(work_dir, file_name, filter_types, step_length=0.5, detail=False):
#     xodr_file = os.path.join(work_dir, f"{file_name}.xodr")
def main(xodr_file, filter_types, step_length=0.5):
    with open(xodr_file, "r") as file_in:
        root_node = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(root_node)

    header_info = {
        "date": opendrive.header.date,
        "geo_reference": opendrive.header.geo_reference,
    }

    # 这一步加载道路信息，比如参考线之类，但同时删除了过多的历史信息，需要手动调整源码
    # 车道信息借助第三方包解析,width 要如何处理
    roads_info = convert_roads_info(opendrive, filter_types, step_length)
    # lane step_length需要对第三方包进行修改
    scenario = convert_opendrive(opendrive, filter_types, roads_info)
    # 车道点位不再独立计算，采用road info 中参考线的点位
    lanes_info, road_junction, road_section_distance = convert_lanes_info(opendrive, scenario)

    # 写入文件&绘制参考线
    return header_info, roads_info, lanes_info


if __name__ == '__main__':
    step_length = 0.5
    detail = False
    # 定义静态文件及所处位置文件夹
    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
    file_name = '第I类路网'
    laneTypes = [
        "none",  # 不应有车辆在上面行驶的车道
        "restricted",  # 不应有车辆在上面行驶的车道
        "driving",  # 正常机动车道
        "stop",  # 高速公路的硬路肩，用于紧急停车
        "shoulder",  # 道路边缘的软边界
        "biking",  # 非机动车道
        "sidewalk",  # 允许行人在上面行走的道路, 人行横道由道路附属设施定义，不属于道路属性
        "border",  # 道路边缘的硬边界
        "parking",  # 带泊车位的车道
        "median",  # 分隔带
        # "bidirectional",  # 现在文档上已经不存在这种类型
        # "special1",  # 这是第三方包的过滤条件，目前看来应该较为原始，需要更新 Lane.laneTypes
        # "special2",
        # "special3",
        # "roadWorks",
        # "tram",
        # "rail",
        "entry",  # 用于平行于主路路段的车道。主要用于加速。
        "exit",  # 用于平行于主路路段的车道。主要用于减速
        "offRamp",  # 驶出高速公路的匝道
        "onRamp",  # 驶向高速公路的匝道

        'curb',  # 路缘石 这是新增的types
        'connectingRamp',  # 连接两条高速公路的匝道
    ]
    filter_types = laneTypes
    filter_types = ["driving", "onRamp", "offRamp", "exit", "entry"]  # 一般用于机动车行驶的车道
    # filter_types = ["driving", "biking", "parking", "onRamp", "offRamp", "exit", "entry", "connectingRamp"]
    # TODO 注意对第三方包的修改 --> change_convert.py
    header_info, roads_info, lanes_info = main(work_dir, file_name, filter_types, step_length=step_length,
                                               detail=detail)
    road_lane_info = {
        "header": header_info,
        "road": roads_info,
        "lane": lanes_info,
    }
    with open(os.path.join(work_dir, f"{file_name}.json"), 'w') as f:
        json.dump(road_lane_info, f)




    # show section with lanes 已经确认参考线和车道线是一致的，并未出现参考线过长现象
    # with open(os.path.join(work_dir, f"{file_name}.json"), 'r') as f:
    #     data = json.load(f)
    # header_info = data['header']
    # roads_info = data['road']
    # lanes_info = data['lane']
    # roads_info = {
    #     int(k): v for k, v in roads_info.items()
    # }
    # from matplotlib import pyplot as plt
    #
    # for road_id, road_info in roads_info.items():
    #     for section_id, section_info in roads_info[road_id]['road_points'].items():
    #         link_points = [i['position'] for i in section_info['points']]
    #         plt.plot([i[0] for i in link_points], [i[1] for i in link_points], color='r', linestyle="", marker=".",
    #                  linewidth=3)
    #         for lane_name, lane_info in lanes_info.items():
    #             lane_road_id = lane_info['road_id']
    #             lane_section_id = lane_info['section_id']
    #             if lane_road_id == int(road_id) and lane_section_id == int(section_id):
    #                 lane_points = lane_info['center_vertices']
    #                 plt.plot([i[0] for i in lane_points], [i[1] for i in lane_points], color='g', linestyle="",
    #                          marker=".", linewidth=1)
    #         plt.show()
