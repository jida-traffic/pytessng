road_network.export_commonroad_scenario(filter_types=filter_types, roads_info=roads_info)


class Lane:
    """ """

    laneTypes = [
        "none",
        "driving",
        "stop",
        "shoulder",
        "biking",
        "sidewalk",
        "border",
        "restricted",
        "parking",
        "bidirectional",
        "median",
        "special1",
        "special2",
        "special3",
        "roadWorks",
        "tram",
        "rail",
        "entry",
        "exit",
        "offRamp",
        "onRamp",
    ]

def export_lanelet_network(
        self, filter_types: list = None, roads_info=None
) -> "ConversionLaneletNetwork":
    """Export network as lanelet network.

    Args:
      filter_types: types of ParametricLane objects to be filtered. (Default value = None)

    Returns:
      The converted LaneletNetwork object.
    """

    # Convert groups to lanelets
    lanelet_network = ConversionLaneletNetwork()

    for parametric_lane in self._planes:
        if filter_types is not None and parametric_lane.type not in filter_types:
            continue
        init_id = parametric_lane.id_.split('.')[0]
        # 在这里添加 lanelet 的 原始信息
        # 所有路段都会有这个属性,调整精度
        road_id = int(parametric_lane.id_.split('.')[0])
        section_id = int(parametric_lane.id_.split('.')[1])
        lengths = roads_info[road_id]['road_points'][section_id]['lengths']

        # 传入的是整条参考线点序列，需要减去初始值得到section对应的lane的点序列
        length_start = lengths[0]
        poses = [min(i - length_start, parametric_lane.length) for i in lengths]

        lanelet = parametric_lane.to_lanelet(0.5, poses)
        lanelet.type = parametric_lane.type

        lanelet.predecessor = self._link_index.get_predecessors(parametric_lane.id_)
        lanelet.successor = self._link_index.get_successors(parametric_lane.id_)

        lanelet_network.add_lanelet(lanelet)

    # prune because some
    # successorIds get encoded with a non existing successorID
    # of the lane link

    # TODO 此处进行了车道合并和修复,TESS并不需要
    # lanelet_network.prune_network()
    # lanelet_network.concatenate_possible_lanelets()

    # Perform lane splits and joins
    # lanelet_network.join_and_split_possible_lanes()

    # lanelet_network.convert_all_lanelet_ids()

    return lanelet_network


def to_lanelet(self, precision: float = 0.5, poses=None) -> ConversionLanelet:
    """Convert a ParametricLaneGroup to a Lanelet.

    Args:
      precision: Number which indicates at which space interval (in curve parameter ds)
        the coordinates of the boundaries should be calculated.
      mirror_border: Which lane to mirror, if performing merging or splitting of lanes.
      distance: Distance at start and end of lanelet, which mirroring lane should
        have from the other lane it mirrors.

    Returns:
      Created Lanelet.

    """
    print(poses)
    left_vertices, right_vertices = np.array([]), np.array([])
    parametric_lane_poses = {}
    temp_parametric_lanes = sorted(self.parametric_lanes, key=lambda x: int(x.id_.split('.')[-1]))
    for parametric_lane in temp_parametric_lanes:
        if parametric_lane == temp_parametric_lanes[-1]:
            parametric_lane_poses[parametric_lane.id_] = poses
        else:
            for index in range(len(poses)):
                if poses[index] > parametric_lane.length:
                    parametric_lane_poses[parametric_lane.id_] = copy.copy(poses[:index])
                    # poses 匹配width成功后移除匹配的元素, 减去 parametric_lane.length，否则后续可能长度不够用
                    poses = [i - parametric_lane.length for i in poses[index:]]
                    break
    # self.parametric_lanes.sort(key=lambda x:x.id_)
    for parametric_lane in self.parametric_lanes:
        # 通过 lane 点序列 获取 width 点序列， 特殊情况下，点序列可能为空
        if not parametric_lane_poses[parametric_lane.id_]:
            continue
        local_left_vertices, local_right_vertices = parametric_lane.calc_vertices(
            precision=precision, poses=parametric_lane_poses[parametric_lane.id_]
        )

        if local_left_vertices is None:
            continue
        try:
            if np.isclose(left_vertices[-1], local_left_vertices[0]).all():
                idx = 1
            else:
                idx = 0
            left_vertices = np.vstack((left_vertices, local_left_vertices))
            right_vertices = np.vstack((right_vertices, local_right_vertices))
        except IndexError:
            left_vertices = local_left_vertices
            right_vertices = local_right_vertices

    center_vertices = np.array(
        [(l + r) / 2 for (l, r) in zip(left_vertices, right_vertices)]
    )

    lanelet = ConversionLanelet(
        copy.deepcopy(self), left_vertices, center_vertices, right_vertices, self.id_
    )

    # Adjacent lanes
    self._set_adjacent_lanes(lanelet)

    return lanelet


def calc_vertices(self, precision: float = 0.5, poses=None) -> Tuple[np.ndarray, np.ndarray]:
    """Convert a ParametricLane to Lanelet.

    Args:
      plane_group: PlaneGroup which should be referenced by created Lanelet.
      precision: Number which indicates at which space interval (in curve parameter ds)
        the coordinates of the boundaries should be calculated.

    Returns:
       Created Lanelet, with left, center and right vertices and a lanelet_id.

    """
    # id_: roadId, sectionId, laneId, widthId
    # num_steps = int(max(3, np.ceil(self.length / float(precision))))
    # poses = np.linspace(0, self.length, num_steps)

    left_vertices = []
    right_vertices = []

    # width difference between original_width and width with merge algo applied

    # calculate left and right vertices of lanelet
    for pos in poses:
        # poses 是lane序列，需要转换
        pos = min(pos - poses[0], self.length)
        inner_pos = self.calc_border("inner", pos)[0]
        outer_pos = self.calc_border("outer", pos)[0]
        left_vertices.append(inner_pos)
        right_vertices.append(outer_pos)
    return (np.array(left_vertices), np.array(right_vertices))