import struct
import copy
import json
import socket
import hashlib
import base64

# 此功能用于与外界交互，可不使用
from kafka import KafkaProducer
from threading import Thread
from multiprocessing import Process
from multiprocessing import Queue


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

    def __init__(self, config):
        self.my_queue = Queue(maxsize=100)
        # 子进程创建时，会将主进程的所有元素深拷贝一份，所以在子进程中，使用的是自己的生产者
        # 采用安全的队列，将队列传入进程中
        KAFKA_HOST, KAFKA_PORT, topic = config.KAFKA_HOST, config.KAFKA_PORT, config.topic
        p = Process(target=self.post, args=(self.my_queue, KAFKA_HOST, KAFKA_PORT, topic))
        p.start()

    # websocket
    def post(self, my_queue, *args):
        # TODO 主进程初始化子进程时启动,此(子)进程里保存了users，外部看不到,需要采用队列的方式
        # 子进程有一个websocket，用来与前端进行通信
        # producer 和 users 列表都在子进程初始化，不会影响主进程
        producer = Producer(*args)
        # self.web = WebSocketUtil(port=WEB_PORT)
        # self.web.start_socket_server()
        while True:
            data = my_queue.get()
            # print(len(users))
            producer.send(data)
            # 判断是否有客户端连接，有才推送消息
            # for user in copy.copy(users):
            #     self.web.send_msg(user, bytes(json.dumps(data), encoding="utf-8"))
            #     print(f"{user} send ok")
            # print(f"send done")


# 汽车数据转换
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


class WebSocketUtil(object):
    global users
    users = set()
    def __init__(self, port=8765, max_wait_user=5):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(max_wait_user)

    # 请求头转换格式为字典
    def get_headers(self, data):
        """将请求头转换为字典"""
        header_dict = {}

        data = str(data, encoding="utf-8")

        header, body = data.split("\r\n\r\n", 1)
        header_list = header.split("\r\n")
        for i in range(0, len(header_list)):
            if i == 0:
                if len(header_list[0].split(" ")) == 3:
                    header_dict['method'], header_dict['url'], header_dict['protocol'] = header_list[0].split(" ")
            else:
                k, v = header_list[i].split(":", 1)
                header_dict[k] = v.strip()
        return header_dict

    # 等待用户连接
    def socket_connect(self):
        conn, addr = self.sock.accept()
        users.add(conn)
        print('add user:', users)
        # 获取握手消息，magic string ,sha1加密  发送给客户端  握手消息
        data = conn.recv(8096)
        headers = self.get_headers(data)
        # 对请求头中的sec-websocket-key进行加密
        response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
                       "Upgrade:websocket\r\n" \
                       "Connection: Upgrade\r\n" \
                       "Sec-WebSocket-Accept: %s\r\n" \
                       "WebSocket-Location: ws://%s%s\r\n\r\n"

        magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        value = headers['Sec-WebSocket-Key'] + magic_string
        ac = base64.b64encode(hashlib.sha1(value.encode('utf-8')).digest())
        response_str = response_tpl % (ac.decode('utf-8'), headers['Host'], headers['url'])

        # 响应握手信息
        conn.send(bytes(response_str, encoding='utf-8'), )

        # # 新的连接成功立马发一次数据
        data = {"message": "connect done"}
        self.send_msg(conn, bytes(json.dumps(data), encoding="utf-8"))


    # 向客户端发送数据
    def send_msg(self, conn, msg_bytes):
        """
        WebSocket服务端向客户端发送消息
        :param conn: 客户端连接到服务器端的socket对象,即： conn,address = socket.accept()
        :param msg_bytes: 向客户端发送的字节
        :return:
        """
        token = b"\x81"  # 接收的第一字节，一般都是x81不变
        length = len(msg_bytes)
        print(length)
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)
        msg = token + msg_bytes
        # 如果出错就是客户端断开连接
        try:
            conn.send(msg)
        except Exception as e:
            # 删除断开连接的记录
            print('error', users)
            users.remove(conn)

    # 循环等待客户端建立连接
    def wait_socket_connect(self):
        while True:
            self.socket_connect()

    # socket服务端监听客户端连接并批量推送数据
    def start_socket_server(self):
        # 启线程循环等待客户端建立连接
        Thread(target=self.wait_socket_connect).start()
        # # 消息推送
        # while True:
        #     # 判断是否有客户端连接，有才推送消息
        #     if len(users):
        #         send_users = copy.copy(users)
        #         # 自定义的消息内容
        #         data = summary()
        #         # 遍历
        #         for user in send_users:
        #             self.send_msg(user, bytes(json.dumps(data), encoding="utf-8"))