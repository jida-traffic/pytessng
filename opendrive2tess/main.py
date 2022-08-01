from lxml import etree
from opendrive2tess.opendrive2lanelet.opendriveparser.parser import parse_opendrive
from opendrive2tess.utils.network_utils import Network


def main(xodr_file):
    with open(xodr_file, "r", encoding='utf-8') as file_in:
        root_node = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(root_node)

    network = Network(opendrive)

    # unity 信息提取
    # from opendrive2tess.utils.unity_utils import convert_unity
    # unity_info = convert_unity(roads_info, lanes_info)

    return network


if __name__ == "__main__":
    network = main(r"仅交叉口.xodr")
