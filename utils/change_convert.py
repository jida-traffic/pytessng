road_network.export_commonroad_scenario(filter_types=filter_types, roads_info=roads_info)


def export_commonroad_scenario(
        self, dt: float = 0.1, benchmark_id=None, filter_types=None, roads_info=None, my_signal=None, pb=None
):
    """Export a full CommonRoad scenario

    Args:
      dt:  (Default value = 0.1)
      benchmark_id:  (Default value = None)
      filter_types:  (Default value = None)

    Returns:

    """

    scenario = Scenario(
        dt=dt, benchmark_id=benchmark_id if benchmark_id is not None else "none"
    )

    scenario.add_objects(
        self.export_lanelet_network(
            filter_types=filter_types
            if isinstance(filter_types, list)
            else ["driving", "onRamp", "offRamp", "exit", "entry"],
            roads_info=roads_info,
            my_signal=my_signal,
            pb=pb
        )
    )

    return scenario



def export_lanelet_network(
        self, filter_types: list = None, roads_info=None, my_signal=None, pb=None
) -> "ConversionLaneletNetwork":
    """Export network as lanelet network.

    Args:
      filter_types: types of ParametricLane objects to be filtered. (Default value = None)

    Returns:
      The converted LaneletNetwork object.
    """

    # Convert groups to lanelets
    lanelet_network = ConversionLaneletNetwork()
    progress = 0
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
        progress += 1
        my_signal.emit(pb, int(progress / len(self._planes) * 80), {})

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
        "curb",
        "connectingRamp",
    ]

    def __init__(self, parentRoad, lane_section):
        self._parent_road = parentRoad
        self._id = None
        self._type = None
        self._level = None
        self._link = LaneLink()
        self._widths = []
        self._borders = []
        self._road_marks = []
        self.lane_section = lane_section
        self.has_border_record = False

    @property
    def parentRoad(self):
        """ """
        return self._parent_road

    @property
    def id(self):
        """ """
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def type(self):
        """ """
        return self._type

    @type.setter
    def type(self, value):
        if value not in self.laneTypes:
            raise Exception()

        self._type = str(value)

    @property
    def level(self):
        """ """
        return self._level

    @level.setter
    def level(self, value):
        if value not in ["true", "false"] and value is not None:
            raise AttributeError("Value must be true or false.")

        self._level = value == "true"

    @property
    def link(self):
        """ """
        return self._link

    @property
    def widths(self):
        """ """
        self._widths.sort(key=lambda x: x.start_offset)
        return self._widths

    @widths.setter
    def widths(self, value):
        """"""
        self._widths = value

    def getWidth(self, widthIdx):
        """

        Args:
          widthIdx:

        Returns:

        """
        for width in self._widths:
            if width.idx == widthIdx:
                return width

        return None

    def getLastLaneWidthIdx(self):
        """Returns the index of the last width sector of the lane"""

        numWidths = len(self._widths)

        if numWidths > 1:
            return numWidths - 1

        return 0

    @property
    def borders(self):
        """ """
        return self._borders

    @property
    def road_marks(self):
        """ """
        return self._road_marks


def parse_opendrive_road_lane_section(newRoad, lane_section_id, lane_section):
    """

    Args:
      newRoad:
      lane_section_id:
      lane_section:

    """

    newLaneSection = RoadLanesSection(road=newRoad)

    # Manually enumerate lane sections for referencing purposes
    newLaneSection.idx = lane_section_id

    newLaneSection.sPos = float(lane_section.get("s"))
    newLaneSection.singleSide = lane_section.get("singleSide")

    sides = dict(
        left=newLaneSection.leftLanes,
        center=newLaneSection.centerLanes,
        right=newLaneSection.rightLanes,
    )

    for sideTag, newSideLanes in sides.items():

        side = lane_section.find(sideTag)

        # It is possible one side is not present
        if side is None:
            continue

        for lane in side.findall("lane"):

            new_lane = RoadLaneSectionLane(
                parentRoad=newRoad, lane_section=newLaneSection
            )
            new_lane.id = lane.get("id")
            new_lane.type = lane.get("type")

            # In some sample files the level is not specified according to the OpenDRIVE spec
            new_lane.level = (
                "true" if lane.get("level") in [1, "1", "true"] else "false"
            )

            # Lane Links
            if lane.find("link") is not None:

                if lane.find("link").find("predecessor") is not None:
                    new_lane.link.predecessorId = (
                        lane.find("link").find("predecessor").get("id")
                    )

                if lane.find("link").find("successor") is not None:
                    new_lane.link.successorId = (
                        lane.find("link").find("successor").get("id")
                    )

            # Width
            for widthIdx, width in enumerate(lane.findall("width")):

                newWidth = RoadLaneSectionLaneWidth(
                    float(width.get("a")),
                    float(width.get("b")),
                    float(width.get("c")),
                    float(width.get("d")),
                    idx=widthIdx,
                    start_offset=float(width.get("sOffset")),
                )

                new_lane.widths.append(newWidth)

            # Border
            for borderIdx, border in enumerate(lane.findall("border")):

                newBorder = RoadLaneSectionLaneBorder(
                    float(border.get("a")),
                    float(border.get("b")),
                    float(border.get("c")),
                    float(border.get("d")),
                    idx=borderIdx,
                    start_offset=float(border.get("sOffset")),
                )

                new_lane.borders.append(newBorder)

            if lane.find("width") is None and lane.find("border") is not None:
                new_lane.widths = new_lane.borders
                new_lane.has_border_record = True

            # Road Marks
            # TODO implementation 添加roadMark
            for markIdx, roadMark in enumerate(lane.findall("roadMark")):
                newMark = {
                    "idx": markIdx,
                    "color": roadMark.get("color"),
                    "start_offset": float(roadMark.get("sOffset")),
                    "type": roadMark.get("type"),
                }
                new_lane.road_marks.append(newMark)

            # Material
            # TODO implementation

            # Visiblility
            # TODO implementation

            # Speed
            # TODO implementation

            # Access
            # TODO implementation

            # Lane Height
            # TODO implementation

            # Rules
            # TODO implementation

            newSideLanes.append(new_lane)

    newRoad.lanes.lane_sections.append(newLaneSection)