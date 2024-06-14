import argparse
import json
from abc import ABC, abstractmethod

'''
深度优先遍历 JSON 数据结构的迭代器。
使用栈来管理遍历状态，通过迭代器协议方法 __iter__ 和 __next__ 实现遍历。
在遍历过程中，判断每个节点是否是最后一个元素，
并将字典节点的子项递归地添加到栈中，确保能够遍历整个 JSON 结构。
'''
class JSONIterator:
    def __init__(self, data):
        self.data = data
        self.stack = [(data, iter(data.items()))]

    def __iter__(self):
        return self

    def __next__(self):
        while self.stack:
            parent, children = self.stack[-1]  # 处理栈顶元素
            # len_parent = len(parent)
            try:
                key, value = next(children)  # 获取下一个键值对
                # is_last = len_parent == 1
                # len_parent -= 1
                level = len(self.stack)
                # del parent[key]
                is_last = next(children, None) is None  # 是该parent的最后一个了
                if not is_last:
                    self.stack[-1] = (parent, iter(parent.items()))
                    next(self.stack[-1][1])

                if isinstance(value, dict):  # 如果值是字典，将其添加到栈中，以便进一步迭代其子项。
                    self.stack.append((value, iter(value.items())))
                return key, value, is_last, level # 返回当前键、值、是否是最后一个元素以及当前层级（栈的长度减一）。
            except StopIteration:  # 如果当前迭代器耗尽（没有更多元素），从栈中移除当前项。
                self.stack.pop()
        raise StopIteration  # 如果栈为空，抛出 StopIteration 以终止迭代。


class JSONVisitor(ABC):
    @abstractmethod
    def visit(self, key, value, is_last, level, parent_is_last):
        pass


class TreeJSONVisitor(JSONVisitor):
    def __init__(self, icons):
        self.icons = icons
        self.result = ""
        self.pre_parent_stack = []

    def finish(self):
        pass

    def visit(self, key, value, is_last, level, parent_is_last):
        icon = self.icons['leaf'] if value is None or not isinstance(value, dict) else self.icons['intermediate']
        connector = "└─" if is_last else "├─"
        # pre = "│  " if parent_is_last else "   "

        if len(self.pre_parent_stack) < level:
            self.pre_parent_stack.append("")

        # if is_last and level > 0:
        #     self.prefix_stack[level - 1] = "   "
        # else:
        #     self.prefix_stack[level - 1] = "│  "  # dd 或许level-1 应该是“”

        if level != 1:
            if parent_is_last:
                self.pre_parent_stack[level - 1] = "   "

            else:
                self.pre_parent_stack[level - 1] = "│  "

            # if is_last and level > 0:
            #     self.prefix_stack[level - 1] = "   "
            #
            # elif parent_is_last:
            #     self.prefix_stack[level - 1] = "│  "

        # prefix = ""
        # if level > 1:
        #     prefix = pre + "   " * (level-2)
        # else:
        prefix = "".join(self.pre_parent_stack[:level])
        self.result += f"{prefix}{connector}{icon}{key}"
        if isinstance(value, dict):
            self.result += "\n"
        else:
            self.result += f": {value}\n"

class RectangleJSONVisitor(JSONVisitor):
    def __init__(self, icons):
        self.icons = icons
        self.result = ""
        self.width = 30

    def visit(self, key, value, is_last, level, parent_is_last):
        icon = self.icons['leaf'] if not isinstance(value, dict) else self.icons['intermediate']
        # connector = "└─" if is_last else "├─"
        connector = "├─"
        prefix = "│  " * (level - 1) + connector
        line = f"{prefix}{icon}{key} ─{'─' * (self.width - len(prefix) - len(key) - 3)}┤\n"
        # if not isinstance(value, dict):
        #     line = line.replace("─┤", f": {value} ─┤\n")
        self.result += line

    def finish(self):
        str_list = list(self.result)
        str_list[0] = '┌'
        str_list[self.width] = '┐'
        str_list[-2] = '┘'
        begin = -2-self.width
        str_list[begin:begin+4] = ['└', '─', '─', '┴']
        self.result = ''.join(str_list)

class JSONVisualizerFactory(ABC):
    @abstractmethod
    def create_visitor(self, icons):
        pass

class TreeJSONVisualizerFactory(JSONVisualizerFactory):
    def create_visitor(self, icons):
        return TreeJSONVisitor(icons)

class RectangleJSONVisualizerFactory(JSONVisualizerFactory):
    def create_visitor(self, icons):
        return RectangleJSONVisitor(icons)


def load_icon_families(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="JSON file visualizer")
    parser.add_argument('-f', '--file', required=True, help="Path to JSON file")
    parser.add_argument('-s', '--style', required=True, choices=['tree', 'rectangle'], help="Visualization style")
    parser.add_argument('-i', '--icon', default='default', help="Icon family (optional)")
    parser.add_argument('-c', '--config', default='icons.json', help="Path to icon configuration file")

    args = parser.parse_args()

    icon_families = load_icon_families(args.config)
    if args.icon not in icon_families:
        raise ValueError(f"Icon family '{args.icon}' not found in configuration file")

    icons = icon_families[args.icon]

    with open(args.file, 'r') as f:
        data = json.load(f)

    if args.style == 'tree':
        factory = TreeJSONVisualizerFactory()
    elif args.style == 'rectangle':
        factory = RectangleJSONVisualizerFactory()
    else:
        raise ValueError("Unknown style")

    visitor = factory.create_visitor(icons)
    iterator = JSONIterator(data)
    is_last_stack = [True]
    for key, value, is_last, level in iterator:
        while len(is_last_stack) <= level:
            is_last_stack.append(True)

        is_last_stack[level] = is_last

        visitor.visit(key, value, is_last, level, is_last_stack[level-1])

    visitor.finish()
    print(visitor.result)

if __name__ == "__main__":
    main()