#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第 6 题 · 方向 A 的 Python 示例程序。

目的同样不是打印一句话，而是走通：
    写代码 -> 解释器运行 -> 打断点单步调试 -> 命令行运行

命令行运行（题目要求：必须是敲命令，不是点界面按钮）：
    python hello.py
    python hello.py 20

VSCode 里按 F5 用 "Python: 调试 hello.py" 配置启动，
把断点打在 for 那一行，观察 acc 的变化。
"""

import sys


def triangular(n: int) -> int:
    """返回 1+2+...+n。故意写成循环，方便下断点看累加过程。"""
    acc = 0
    for i in range(1, n + 1):
        acc += i          # <-- 建议在这里下断点
    return acc


def main(argv: list) -> int:
    print("Hello, OpenLab!")

    n = 10
    if len(argv) > 1:
        try:
            n = int(argv[1])
        except ValueError:
            print(f"参数不是数字：{argv[1]}，用默认值 10")
            n = 10

    print(f"1+...+{n} = {triangular(n)}")
    print(f"argv = {argv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
