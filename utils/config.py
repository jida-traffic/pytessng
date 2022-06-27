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


def get_vehi_info(simuiface):
    data = {
        'msgCnt': simuiface.vehiCountRunning(),
        'simuTime': simuiface.simuTimeIntervalWithAcceMutiples(),
        'startSimuTime': simuiface.startMSecsSinceEpoch(),
        # 'type',
        'vehiCountTotal': simuiface.vehiCountTotal(),
        'data': []
    }
    lAllVehi = simuiface.allVehiStarted()
    lAllVehi_mapping = {
        i.id(): i
        for i in lAllVehi
    }
    # import pdb;pdb.set_trace()
    VehisStatus = simuiface.getVehisStatus()
    VehisStatus_mapping = {
        i.vehiId: i
        for i in VehisStatus
    }

    def get_attr(obj, attr):
        try:
            if obj:
                be_called_function = getattr(obj, attr)
                # import pdb;pdb.set_trace()
                if callable(be_called_function):
                    return be_called_function()
                else:
                    return be_called_function
        except:
            pass
        return None

    for vehi in lAllVehi:
        vehiStatus = VehisStatus_mapping.get(vehi.id())
        data['data'].append(
            {
                'id': get_attr(vehi, 'id'),
                'acc': get_attr(vehi, 'acce'),
                'color': None,  # get_attr(vehiStatus, 'mColor'),
                'distance': get_attr(vehiStatus, 'mrDrivDistance'),
                'speed': get_attr(vehiStatus, 'mrSpeed'),
                'vehiType': get_attr(vehiStatus, 'vehiType'),
                'startSimuTime': get_attr(vehiStatus, 'startSimuTime'),
            }
        )
    return data


class Producer:
    def __init__(self, host, port, topic):
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=[f'{host}:{port}'], api_version=(0, 10))

    def send(self, value):  # key@value 采用同样的key可以保证消息的顺序
        self.producer.send(self.topic, key=json.dumps(self.topic).encode('utf-8'),
                           value=json.dumps(value).encode('utf-8')).add_callback(self.on_send_success).add_errback(
            self.on_send_error)
        self.producer.flush()

    # 定义一个发送成功的回调函数
    def on_send_success(self, record_metadata):
        pass

    # 定义一个发送失败的回调函数
    def on_send_error(self, excp):
        print(f"send error:{excp}")


class MyProcess:
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            cls._instance = super(MyProcess, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.my_queue = Queue(maxsize=100)
        # 子进程创建时，会将主进程的所有元素深拷贝一份，所以在子进程中，使用的是自己的生产者
        p = Process(target=self.post, args=(self.my_queue,))
        p.start()

    def post(self, my_queue):  # 主进程初始化子进程时启动
        producer = Producer(KAFKA_HOST, KAFKA_PORT, topic)
        while True:
            data = my_queue.get()
            producer.send(data)
            print(data)
