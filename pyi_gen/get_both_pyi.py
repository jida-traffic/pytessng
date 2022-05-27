import re
import collections


# 读取 back 填充内容
with open("Tessng.pyi.back", 'r') as f:
    back_context = f.readlines()


class_map = collections.defaultdict(dict)

before_class, before_line = None, None
class_map[before_class]["start_line"] = 0

for index in range(len(back_context)):
    line = back_context[index]
    if line != '\n':
        class_map[before_class]["end_line"] = index - 1
    if line.find('class ') != -1:
        class_name = (re.findall('class (.*)\(', line) or re.findall('class (.*)[(:]', line))[0]
        class_map[class_name]["start_line"] = index
        # class_map[before_class]["end_line"] = index - 1
        before_class = class_name

print(class_map)

# for class_name, value in class_map.items():
#     # print(i, class_map[i])
#     print(class_name)
#     print(context[value['start_line']: value["end_line"] + 1])
#

import re
import collections

# with open("Tessng.pyi", 'r') as f:
#      context = f.read()
#      class_list = re.findall('class (.*)\(', context) or re.findall('class (.*)[(:]', context)

with open("Tessng.pyi", 'r') as f:
    context = f.readlines()
    for index in range(len(context)):
        line = context[index]
        if line.find('class ') != -1:
            class_name = (re.findall('class (.*)\(', line) or re.findall('class (.*)[(:]', line))[0]
            if class_name in class_map:
                start_line = class_map[class_name]['start_line']
                end_line = class_map[class_name]['end_line']
                con = ''.join(back_context[start_line + 1: end_line])  # 首行是名称，末行是pass
                print(con)
                context[index] = context[index] + con

with open("Both.pyi", 'w') as f:
    f.write(''.join(context))
            # 匹配成功，读取相应内容并插入

