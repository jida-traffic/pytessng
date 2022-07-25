# -*- coding: utf-8 -*-

import os
import sys

from pathlib import Path
from PySide2.QtWidgets import *
from MyPlugin import MyPlugin
from Tessng import *
from opendrive2tess.utils.external_utils import MyProcess


if __name__ == '__main__':
    app = QApplication()

    workspace = os.fspath(Path(__file__).resolve().parent)
    config = {'__workspace':workspace,
              #'__netfilepath':"C:/TESSNG_2.0.0/Example/教学视频案例-机动车交叉口.tess"
              }
    plugin = MyPlugin()
    factory = TessngFactory()
    tessng = factory.build(plugin, config)

    try:
        config = __import__('config')
    except:
        config = object()
        sys.modules["config"] = config

    if getattr(config, 'IS_SAVE'):
        my_process = MyProcess(config)
        sys.modules["__main__"].__dict__['myprocess'] = my_process

    if tessng is None:
        sys.exit(0)
    else:
        sys.exit(app.exec_())




