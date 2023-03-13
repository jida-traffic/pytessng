# opendrive —> tess 车道, 不在此映射表中的车道不予显示
# tess 中车道类型定义 机动车道/机非共享/非机动车道/公交专用道
LANE_TYPE_MAPPING = {
    'driving': '机动车道',
    'onRamp': '机动车道',
    'offRamp': '机动车道',
    'entry': '机动车道',
    'exit': '机动车道',
    'connectingRamp': '机动车道',

    'shoulder': '机动车道',
    'border': '',
    'stop': '应急车道',
    # 'none': '',
    # 'redtricted': '',
    # 'parking': '',
    # 'median': '',
    # 'curb': '',

    'biking': '非机动车道',
    'sidewalk': '非机动车道',
}

# 连续次数后可视为正常车道，或者连续次数后可视为连接段,最小值为2
point_require = 2
POINT_REQUIRE = max(2, point_require)

# 当 opendrive 连接段的首尾连接长度低于此值时，抛弃原有的点序列，使用自动连接
MIN_CONNECTOR_LENGTH = None

# 是否将路网移至画面中心
is_center = False

# 需要被处理的车道类型及处理参数
WIDTH_LIMIT = {
    '机动车道': {
        'split': 2,  # 作为正常的最窄距离
        'join': 1.5,  # 被忽略时的最宽距离
    },
    # '非机动车道': {
    #     'split': 2,
    #     'join': 0.5,
    # },
}

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
