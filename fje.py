import argparse
import json
import graphviz
from abc import ABC, abstractmethod

# Function to load icon families from a configuration file
def load_icon_families(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

# Abstract base class for JSON visualizer
class JSONVisualizer(ABC):
    def __init__(self, data, icons):
        self.data = data
        self.icons = icons

    @abstractmethod
    def visualize(self, data=None, prefix=""):
        pass
# Concrete visualizer for tree style
class TreeJSONVisualizer(JSONVisualizer):
    def visualize(self, data=None, prefix="", is_last=True):
        if data is None:
            data = self.data
        result = ""
        items = list(data.items())
        for i, (key, value) in enumerate(items):
            icon = self.icons['leaf'] if not isinstance(value, dict) or not value else self.icons['intermediate']
            connector = "└─" if i == len(items) - 1 else "├─"
            result += f"{prefix}{connector}{icon}{key}"
            if isinstance(value, dict):
                result += "\n"
                new_prefix = "   " if i == len(items) - 1 else "│  "
                result += self.visualize(value, prefix + new_prefix, i == len(items) - 1)
            else:
                result += f": {value}\n"
        return result


# Concrete visualizer for rectangle style
class RectangleJSONVisualizer(JSONVisualizer):
    def get_result(self, result, key, prefix="", width=0, is_leaf=False):
        icon = self.icons['leaf'] if is_leaf else self.icons['intermediate']
        res = f"{prefix}├─{icon}{key} ─" + "┤\n"
        num = width - len(res)
        result += f"{prefix}├─{icon}{key} ─" + "─" * num + "┤\n"
        return result

    def visualize(self, data=None, prefix="", width=0, level=0):
        if data is None:
            data = self.data
        result = ""
        keys = list(data.keys())
        for i, key in enumerate(keys):
            is_leaf = not isinstance(data[key], dict)
            if isinstance(data[key], dict):
                if i == 0 and level == 0:
                    res = f"┌─{self.icons['intermediate']}{key} ─" + "─" * 30 + "┐\n"
                    width = len(res)
                    result += res
                else:
                    result = self.get_result(result, key, prefix, width)
                result += self.visualize(data[key], prefix + "│  ", width, level + 1)
            else:
                val = data[key]
                if val is None:
                    result = self.get_result(result, key, prefix, width, is_leaf=True)
                else:
                    res = f"{prefix}├─{self.icons['leaf']}{key}: {data[key]} ─┤\n"
                    num = width - len(res)
                    result += f"{prefix}├─{self.icons['leaf']}{key}: {data[key]} ─" + "─" * num + "┤\n"
        # 替换最后一行
        if level == 0:
            # 找到换行符的位置
            last_newline = result[:-1].rfind('\n')
            if last_newline != -1:
                # 截取最后两个换行符之间的内容
                original_string = result[last_newline + 1:-1]
                # 替换
                original_string = original_string.replace('│  ', '└──')
                original_string = original_string.replace('├─', '┴─')
                original_string = original_string.replace('─┤', '─┘')
                result = result[:last_newline + 1] + original_string
        return result


# Abstract factory for JSON visualizer
class JSONVisualizerFactory(ABC):
    @abstractmethod
    def create_visualizer(self, data, icons):
        pass

# Concrete factory for tree style
class TreeJSONVisualizerFactory(JSONVisualizerFactory):
    def create_visualizer(self, data, icons):  # create 多种icons
        return TreeJSONVisualizer(data, icons)

# Concrete factory for rectangle style
class RectangleJSONVisualizerFactory(JSONVisualizerFactory):
    def create_visualizer(self, data, icons):
        return RectangleJSONVisualizer(data, icons)

# Director for building the visualizer
class JSONVisualizerBuilder:
    def __init__(self, factory):
        self.factory = factory

    def build(self, data, icons):
        return self.factory.create_visualizer(data, icons)

def main():
    parser = argparse.ArgumentParser(description="JSON file visualizer")
    parser.add_argument('-f', '--file', required=True, help="Path to JSON file")
    parser.add_argument('-s', '--style', required=True, choices=['tree', 'rectangle'], help="Visualization style")
    parser.add_argument('-i', '--icon', default='default', help="Icon family (optional)")
    parser.add_argument('-c', '--config', default='icons.json', help="Path to icon configuration file")

    args = parser.parse_args()
    # Load icon families from configuration file
    icon_families = load_icon_families(args.config)
    # Check if the specified icon family exists in the configuration file
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

    builder = JSONVisualizerBuilder(factory)
    visualizer = builder.build(data, icons)
    print(visualizer.visualize())

if __name__ == "__main__":
    main()

