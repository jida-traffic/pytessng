# TODO 移除部分车道
# filter_ids = [3,6,5,4,80,67,82,83,748,749,2,668,723,391,116,668]
filter_ids = []
border_line_width = 0.2
center_line_width = 0.3
empty_line_lenfth, real_line_length = 3, 4  # 虚实线长度



# unity 信息提取的类型映射
UNITY_LANE_MAPPING = {
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
