import os
from lxml import etree
from opendrive2tessng.opendrive2lanelet.opendriveparser.parser import parse_opendrive
from opendrive2tessng.utils.network_utils import Network


def main(xodr_file: str) -> Network:
    """
        初始化opendrive文件，得到原始的路网对象
    Args:
        xodr_file: 文件位置

    Returns:

    """
    with open(xodr_file, "r", encoding='utf-8') as file_in:
        root_node = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(root_node)

    file_name = os.path.splitext(os.path.split(xodr_file)[-1])[0]
    network = Network(opendrive, file_name)
    
    # import collections
    # road_signals = collections.defaultdict(list)
    # for road in root_node.getroottree().findall('road'):
    #     signals = road.find('signals') and road.find('signals').findall("signal") or []
    #     for signal in signals:
    #         road_signals[road.get('id')].append(dict(signal.items()))
    # network.road_signals = road_signals

    return network


if __name__ == "__main__":
    network = main(r"仅交叉口.xodr")
