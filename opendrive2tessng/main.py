import os

from lxml import etree
from utils.network_utils import Network
from opendrive2lanelet.opendriveparser.parser import parse_opendrive


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
    return network


if __name__ == "__main__":
    network = main(r"仅交叉口.xodr")
