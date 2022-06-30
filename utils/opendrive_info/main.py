from lxml import etree
from opendrive2lanelet.opendriveparser.parser import parse_opendrive
from utils.opendrive_info.utils import convert_opendrive, convert_roads_info, convert_lanes_info
from utils.opendrive_info.unity_utils import convert_unity


def main(xodr_file, filter_types, step_length, my_signal, pb):
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
    # 车道点位不再独立计算，采用road info 中参考线的点位
    # 这一步最消耗时间，所以需要添加进度条
    scenario = convert_opendrive(opendrive, filter_types, roads_info, my_signal, pb)
    lanes_info = convert_lanes_info(opendrive, scenario, roads_info)

    # TODO 尽量不要转换，太耗性能
    import time
    start_time = time.time()
    convert_unity(roads_info, lanes_info)
    print(f"unity use: {time.time() - start_time}")
    # 写入文件&绘制参考线
    return header_info, roads_info, lanes_info
