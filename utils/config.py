import json
from multiprocessing import Process
from multiprocessing import Queue
# TODO 对于biking driving 不在同一路段的问题，我们可以生成两个json，分别过滤不同的值，多次执行生成路段
from kafka import KafkaProducer


# opendrive —> tess 车道, 不在此映射表中的车道不予显示
lane_type_mapping = {
    'driving': '机动车道',
    'parking': '机动车道',
    'onRamp': '机动车道',
    'offRamp': '机动车道',
    'biking': '非机动车道',
}

# 需要被处理的车道类型及处理参数
width_limit = {
    '机动车道': {
        'split': 3,  # 作为正常的最窄距离
        'join': 0.2,  # 被忽略时的最宽距离
    },
    # 'biking': 1,
}

# 连续次数后可视为正常车道，或者连续次数后可视为连接段,最小值为2
point_require = 2
point_require = max(2, point_require)

KAFKA_HOST = 'tengxunyun'
KAFKA_PORT = 9092
topic = 'tess'

WEB_PORT = 8006
