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
        '__custsimubysteps': True,
        '__simuafterload': False,
    }

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
