# opendrive —> tess 车道, 不在此映射表中的车道不予显示
lane_type_mapping = {
    'driving': '机动车道',
    # 'parking': '机动车道',
    'onRamp': '机动车道',
    'offRamp': '机动车道',
    'entry': '机动车道',
    'exit': '机动车道',
    'connectingRamp': '机动车道',
    # 'biking': '非机动车道',
    # 'sidewalk': '人行道',
}


# 需要被处理的车道类型及处理参数
width_limit = {
    '机动车道': {
        'split': 3,  # 作为正常的最窄距离
        'join': 0.2,  # 被忽略时的最宽距离
    },
    # 'biking': {},
}

# 连续次数后可视为正常车道，或者连续次数后可视为连接段,最小值为2
point_require = 2
point_require = max(2, point_require)
