# TODO 对于biking driving 不在同一路段的问题，我们可以生成两个json，分别过滤不同的值，多次执行生成路段
width_limit = {
    'driving': {
        'split': 2,  # 作为正常的最窄距离
        'join': 0.1, # 被忽略时的最宽距离
    },
    # 'biking': 1,
}

lane_type_mapping = {
    'driving': '机动车道',
    'parking': '机动车道',
    'onRamp': '机动车道',
    'offRamp': '机动车道',
    'biking': '非机动车道',
}

point_require = 2  # 连续次数后可视为正常车道，或者连续次数后可视为连接段,最小值为2
if point_require < 2:
    raise 1