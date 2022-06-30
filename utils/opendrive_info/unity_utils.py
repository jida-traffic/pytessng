import collections
import json
from numpy import sqrt, square


def deviation_point(coo1, coo2, width, right=False, is_last=False):
    signl = 1 if right else -1  #记录向左向右左右偏移
    x1, y1, x2, y2 = coo1[0], coo1[1], coo2[0], coo2[1]  # 如果是最后一个点，取第二个 点做偏移
    x_base, y_base = (x1, y1) if not is_last else (x2, y2)
    if not ((x2-x1) or (y2-y1)):  # 分母为0
        return [x_base, y_base]
    X = x_base + signl * width * (y2 - y1) / sqrt(square(x2-x1) + square((y2-y1)))
    Y = y_base + signl * width * (x1 - x2) / sqrt(square(x2-x1) + square((y2-y1)))
    return [X, Y]


def convert_unity(roads_info, lanes_info):
    xy_limit = None
    for road_id, road_info in roads_info.items():
        if road_info['junction_id'] == None:
            road_info['junction_id'] = -1
        # 记录 坐标点的极值
        for section_id, points in road_info['road_points'].items():
            for point in points['right_points']:
                position = point['position']
                if xy_limit is None:
                    xy_limit = [position[0], position[0], position[1], position[1]]
                else:
                    xy_limit[0] = min(xy_limit[0], position[0])
                    xy_limit[1] = max(xy_limit[1], position[0])
                    xy_limit[2] = min(xy_limit[2], position[1])
                    xy_limit[3] = max(xy_limit[3], position[1])
    x_move, y_move = sum(xy_limit[:2]) / 2, sum(xy_limit[2:]) / 2 if xy_limit else (0, 0)

    # unity 数据导出
    line_width = 0.2

    # 车道与unity 映射表
    unity_lane_mapping = {
        "Driving": ["driving", "stop", "parking", "entry", "exit", "offRamp", "onRamp", "connectingRamp", ],
        "None": ["none"],
        "GreenBelt": ["shoulder", "border", "median", "curb"],
        "SideWalk": ["sidewalk"],
        "Biking": ["biking", ],
        "Restricted": ["restricted"],
        "WhiteLine": [],
        "YellowLine": [],
        "Other": ["bidirectional", "special1", "special2", "special3", "roadWorks", "tram", "rail", ]
    }
    lane_unity_mapping = {}
    for unity, lane_types in unity_lane_mapping.items():
        for lane_type in lane_types:
            lane_unity_mapping[lane_type] = unity

    unity_info = collections.defaultdict(list)

    # 将车道信息绘制成三角形放入参考表中
    for lane_info in lanes_info.values():
        # if lane_info['road_id'] not in [498, 499, 500, 501, 359, 503,1059]:
        #     continue
        lane_type = lane_info["type"]
        left_vertices, right_vertices = lane_info['left_vertices'], lane_info['right_vertices']
        for index, distance in enumerate(lane_info['distance'][:-1]):  # 两两组合，最后一个不可作为首位
            left_0, left_1, right_0, right_1 = left_vertices[index], left_vertices[index + 1], right_vertices[index], \
                                               right_vertices[index + 1]
            coo_0 = [[left_0[0] - x_move, 0, left_0[1] - y_move], [left_1[0] - x_move, 0, left_1[1] - y_move],
                     [right_0[0] - x_move, 0, right_0[1] - y_move]]
            coo_1 = [[left_1[0] - x_move, 0, left_1[1] - y_move], [right_1[0] - x_move, 0, right_1[1] - y_move],
                     [right_0[0] - x_move, 0, right_0[1] - y_move]]
            unity_info[lane_unity_mapping[lane_type]] += coo_0 + coo_1

    # 绘制车道分隔线
    between_line = {}
    for lanelet_id, lane_info in lanes_info.items():
        width = 0.2
        between_line[lanelet_id] = {
            "road_id": lane_info["road_id"],
            "section_id": lane_info["section_id"],
            "lane_id": lane_info["lane_id"],
            "type": lane_info['type'],
            "road_marks": lane_info['road_marks'],
            'left_vertices': [],
            'center_vertices': [],
            'right_vertices': [],
        }
        base_points = lane_info['right_vertices']
        point_count = len(base_points)
        # left_vertices, right_vertices = lane_info['left_vertices'], lane_info['right_vertices']
        for index in range(point_count):
            if index + 1 == point_count:
                is_last = True
                num = index - 1
            else:
                is_last = False
                num = index
            left_point = deviation_point(base_points[num], base_points[num + 1], width / 2, right=False,
                                         is_last=is_last)
            right_point = deviation_point(base_points[num], base_points[num + 1], width / 2, right=True,
                                          is_last=is_last)
            between_line[lanelet_id]["left_vertices"].append(left_point)
            between_line[lanelet_id]["right_vertices"].append(right_point)
            between_line[lanelet_id]["center_vertices"].append(base_points)

    # 计算中心车道的分隔线
    for road_id, road_info in roads_info.items():
        width = 0.4
        for section_id, section in road_info["lane_sections"].items():
            lanelet_id = f"{road_id},{section_id},0"
            between_line[lanelet_id] = {
                "road_id": road_id,
                "section_id": section_id,
                "lane_id": 0,
                "type": None,
                "road_marks": section["center_lane"]["road_marks"],
                'left_vertices': [],
                'center_vertices': [],
                'right_vertices': [],
            }

            # 中心车道取参考线坐标作为偏移基准
            base_points = [i["position"] for i in road_info["road_points"][section_id]["right_points"]]
            point_count = len(base_points)
            # left_vertices, right_vertices = lane_info['left_vertices'], lane_info['right_vertices']
            for index in range(point_count):
                if index + 1 == point_count:
                    is_last = True
                    num = index - 1
                else:
                    is_last = False
                    num = index
                left_point = deviation_point(base_points[num], base_points[num + 1], width / 2, right=False,
                                             is_last=is_last)
                right_point = deviation_point(base_points[num], base_points[num + 1], width / 2, right=True,
                                              is_last=is_last)
                between_line[lanelet_id]["left_vertices"].append(left_point)
                between_line[lanelet_id]["right_vertices"].append(right_point)
                between_line[lanelet_id]["center_vertices"].append(base_points)

    # 绘制车道分隔线
    for lanelet_id, line_info in between_line.items():
        # break
        # 对于左向车道，road_mark 可能需要倒序
        road_marks = line_info["road_marks"]
        if not road_marks:
            continue

        road_id = line_info["road_id"]
        section_id = line_info["section_id"]
        lane_id = line_info["lane_id"]
        length = roads_info[road_id]['road_points'][section_id]["length"]
        left_vertices = line_info["left_vertices"]
        right_vertices = line_info["right_vertices"]

        # 对于左向的车道，应该需要重置mark
        for road_mark in road_marks:
            if lane_id < 0:
                # 只有最后一个 roadMark 没有 end_offset
                road_mark['start_offset'] = length - road_mark.get("end_offset", length)
                road_mark['end_offset'] = length - road_mark["start_offset"]
            else:
                road_mark['end_offset'] = road_mark.get("end_offset", length)

        section_info = roads_info[road_id]["road_points"][section_id]
        offsets = section_info["right_offsets"] if lane_id >= 0 else section_info["left_offsets"]
        if len(offsets) != len(line_info["center_vertices"]):
            raise
        for index, _ in enumerate(line_info["center_vertices"][:-1]):
            if index == 0:
                road_mark = road_marks[0]  # start_offset 可能不是从0 开始的，主动优化一下
            else:
                for road_mark in road_marks:
                    if offsets[index] >= road_mark["start_offset"] and offsets[index] <= road_mark["end_offset"]:
                        break  # 必须取到正确的mark
            color = road_mark["color"]
            type = road_mark["type"]
            if type == "broken" and index % 4 in [0, 1]:  # 断线
                continue

            left_0, left_1, right_0, right_1 = left_vertices[index], left_vertices[index + 1], right_vertices[index], \
                                               right_vertices[index + 1]
            coo_0 = [[left_0[0] - x_move, 0, left_0[1] - y_move], [left_1[0] - x_move, 0, left_1[1] - y_move],
                     [right_0[0] - x_move, 0, right_0[1] - y_move]]
            coo_1 = [[left_1[0] - x_move, 0, left_1[1] - y_move], [right_1[0] - x_move, 0, right_1[1] - y_move],
                     [right_0[0] - x_move, 0, right_0[1] - y_move]]
            if color == "yellow":
                unity_info["YellowLine"] += coo_0 + coo_1
            else:
                unity_info["WhiteLine"] += coo_0 + coo_1

    for key, info in unity_info.items():
        unity_info[key] = {'pointsArray': info, 'drawOrder': [i for i in range(len(info))], 'count': int(len(info))}
    # json.dump(unity_info, open("unity.json", 'w'))

    # 发送 unity地图消息 给前端
    import sys, copy
    my_process = sys.modules["__main__"].__dict__['myprocess']
    # from utils.external_utils import users
    # users = WebSocketUtil.users
    # 此处已经在子进程里，users 为空，应该采用队列的形式
    users = []
    for user in copy.copy(users):
        my_process.web.send_msg(user, bytes(json.dumps(unity_info), encoding="utf-8"))

    if my_process.my_queue.full():
        try:
            my_process.my_queue.get_nowait()
        except:
            pass
    try:
        my_process.my_queue.put_nowait(unity_info)
    except:
        pass

    return unity_info
