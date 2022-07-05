from lxml import etree
from opendrive2tess.opendrive2lanelet.opendriveparser.elements.roadLanes import Lane
from opendrive2tess.opendrive2lanelet.opendriveparser.parser import parse_opendrive
from opendrive2tess.convert_utils import convert_opendrive, convert_roads_info, convert_lanes_info


def main(xodr_file, step_length, filter_types=None, my_signal=None, pb=None):
    filter_types = filter_types or Lane.laneTypes

    with open(xodr_file, "r") as file_in:
        root_node = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(root_node)

    # 头信息
    header_info = {
        "date": opendrive.header.date,
        "geo_reference": opendrive.header.geo_reference,
    }

    # 参考线信息解析
    roads_info = convert_roads_info(opendrive, filter_types, step_length)

    # 车道点位序列不再独立计算，采用 road info 中参考线的点位
    # 车道信息解析，这一步最消耗时间，允许传入进度条
    scenario = convert_opendrive(opendrive, filter_types, roads_info, my_signal=my_signal, pb=pb)
    lanes_info = convert_lanes_info(opendrive, scenario, roads_info)

    return header_info, roads_info, lanes_info


if __name__ == "__main__":
    header_info, roads_info, lanes_info = main(r"仅交叉口.xodr", 10)
    print(header_info, roads_info, lanes_info)
