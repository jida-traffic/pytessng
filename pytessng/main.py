# -*- coding: utf-8 -*-

import os
import sys

from pathlib import Path
from PySide2.QtWidgets import *
from MyPlugin import MyPlugin
from Tessng import *


def TessNgObject():
    app = QApplication()

    workspace = os.fspath(Path(__file__).resolve().parent)

    # 本地数据库
    config = {
        # '__netfilepath': r"C:\TESSNG_2.0.0\Example\上海江桥收费站.tess",
        # '__netfilepath': r"C:\Users\yang\Desktop\test.tess",
        '__workspace': workspace,
        '__custsimubysteps': True,
        '__simuafterload': False,
        "__allowspopup": False,
    }

    plugin = MyPlugin()
    factory = TessngFactory()
    tessng = factory.build(plugin, config)

    if tessng is None:
        sys.exit(0)
    else:
        sys.exit(app.exec_())


if __name__ == '__main__':
    TessNgObject()