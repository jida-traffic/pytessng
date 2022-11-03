# -*- coding: utf-8 -*-

import os
import sys

from pathlib import Path
from PySide2.QtWidgets import *
from MyPlugin import MyPlugin
from Tessng import *
from opendrive2tessng.utils.external_utils import MyProcess

if __name__ == '__main__':
    app = QApplication()

    workspace = os.fspath(Path(__file__).resolve().parent)

    # 本地数据库
    config = {
        '__workspace': workspace,
        # '__netfilepath': r"C:\Users\yang\Desktop\Projects\TESS_PYAPI\Data\第一类路网.tess",
        # "__dbhost": "139.196.51.214",
        # "__dbport": 5432,
        # "__dbdriver": "QPSQL",
        # "__dbname": "tess",
        # "__dbuser": "postgres",
        # "__dbpassword": "123456",
        '__custsimubysteps': True,
        '__simuafterload': False,
    }

    # 海信数据库
    # config = {
    #     '__workspace': workspace,
    #     # '__netfilepath': "C:/TESSNG_2.0.0/Example/教学视频案例-机动车交叉口.tess",
    #
    #     # 读取数据库
    #     "__dbhost": "10.16.7.14",
    #     "__dbport": 8003,
    #     "__dbdriver": "QPSQL",
    #     "__dbname": "wgfz",
    #     "__dbuser": "wgfz",
    #     "__dbpassword": "wgfz!@#",
    #     '__custsimubysteps': True,
    #     '__simuafterload': False,
    #
    #     # 写入数据库
    #     "__pgdbhost": "10.16.7.14",
    #     "__pgdbport": 8003,
    #     "__pgdbdriver": "QPSQL",
    #     "__pgdbname": "wgfz",
    #     "__pgdbuser": "wgfz",
    #     "__pgdbpassword": "wgfz!@#",
    # }
    plugin = MyPlugin()
    factory = TessngFactory()
    tessng = factory.build(plugin, config)

    try:
        config_module = __import__('config')
    except:
        config_module = object()
    finally:
        sys.modules["config"] = config_module

    if getattr(config_module, 'IS_SAVE'):
        my_process = MyProcess(config_module)
        sys.modules["__main__"].__dict__['myprocess'] = my_process

    if tessng is None:
        sys.exit(0)
    else:
        sys.exit(app.exec_())
