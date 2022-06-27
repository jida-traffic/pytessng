from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Process
from multiprocessing import Queue


# TODO 对于biking driving 不在同一路段的问题，我们可以生成两个json，分别过滤不同的值，多次执行生成路段
width_limit = {
    '机动车道': {
        'split': 3,  # 作为正常的最窄距离
        'join': 0.1, # 被忽略时的最宽距离
    },
    # 'biking': 1,
}

# 不在此映射表中的车道不予显示
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


KAFKA_HOST = 'tengxunyun'
KAFKA_PORT = 9092
topic = 'tess'
# import redis
# REDIS_HOST = 'tengxunyun'
# REDIS_PORT = 6379
# pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, db=4)   # 前端传入的数据放在db=2
# redis_client = redis.Redis(connection_pool=pool)


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
                'color': None, #get_attr(vehiStatus, 'mColor'),
                'distance': get_attr(vehiStatus, 'mrDrivDistance'),
                'speed': get_attr(vehiStatus, 'mrSpeed'),
                'vehiType': get_attr(vehiStatus, 'vehiType'),
                'startSimuTime': get_attr(vehiStatus, 'startSimuTime'),
            }
        )
    return data


class MyProcess:
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(MyProcess, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
            print('create')
        return cls._instance

    def __init__(self):
        self.my_queue = Queue(maxsize=100)
        p = Process(target=self.post, args=(self.my_queue,))
        p.start()


    def post(self, my_queue):
        while True:
            if not my_queue.empty():
                print(f"post:{id(my_queue)}")
                pass
                print(my_queue.get())

# my_process = MyProcess()

if __name__ == "__main__":
    my_process = MyProcess()
    while True:
        print(1)
        my_process.my_queue.put('aaaaaaaa')