# pyd所在路径,此文件需要放置在同级目录下，否则 import 失败
module_name = "Tessng"

exec("import %s" % module_name)

from pybind11_stubgen import ModuleStubsGenerator

module = ModuleStubsGenerator(module_name)
module.parse()
module.write_setup_py = False

with open(f"stubshome/{module_name}.pyi", "w") as fp:
    fp.write("#\n# Automatically generated file, do not edit!\n#\n\n")
    fp.write("\n".join(module.to_lines()))


# pyside2生成 pyi文件
# 将Tessng.pyd及tessng的6个动态库dll拷到PySide2目录下，修改了这个目录下的__init__.py
# 再执行python generate_pyi.py Tessng
# 注意，需要在 enum_sig.py 文件下的 def klass 函数第一行 import Tessng
# 同时，需要debug 运行 generate_pyi.py 文件,相关的动态库一定要提前放置在文件夹下