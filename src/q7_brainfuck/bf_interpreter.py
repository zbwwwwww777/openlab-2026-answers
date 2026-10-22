#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「奇怪的书」解释器与验证脚本
—— 第 7 题的答案验证工具

这门只有 8 个关键字的语言就是经典的 Brainfuck：
    +  指针所指单元值 +1
    -  指针所指单元值 -1
    >  指针右移一格
    <  指针左移一格
    [  若当前单元为 0，跳到向后最近的 ]
    ]  若当前单元非 0，跳到向前最近的 [
    .  输出当前单元的值（ASCII）
    ,  输入一个字符，ASCII 值存入当前单元

单元格取值范围 0-255，超出即溢出回绕。

用法：
    python bf_interpreter.py <程序文件> [输入字符串]
    python bf_interpreter.py --demo          # 直接演示三页的答案
"""

import sys

TAPE_SIZE = 30000


def build_jump_table(code: str) -> dict:
    """预处理括号配对，避免运行时反复扫描。"""
    pairs = {}
    stack = []
    for i, c in enumerate(code):
        if c == '[':
            stack.append(i)
        elif c == ']':
            if not stack:
                raise SyntaxError(f'第 {i} 位出现了不匹配的 ]')
            j = stack.pop()
            pairs[i] = j
            pairs[j] = i
    if stack:
        raise SyntaxError(f'第 {stack[-1]} 位的 [ 没有对应的 ]')
    return pairs


def run(code: str, inp: bytes = b'', trace: bool = False) -> bytes:
    """执行程序，返回输出的字节序列。"""
    tape = [0] * TAPE_SIZE
    ptr = 0
    ip = 0
    ii = 0
    out = bytearray()
    pairs = build_jump_table(code)

    while ip < len(code):
        c = code[ip]

        if c == '+':
            tape[ptr] = (tape[ptr] + 1) % 256
        elif c == '-':
            tape[ptr] = (tape[ptr] - 1) % 256
        elif c == '>':
            ptr += 1
            if ptr >= TAPE_SIZE:
                raise OverflowError('指针越界（右）')
        elif c == '<':
            ptr -= 1
            if ptr < 0:
                raise OverflowError('指针越界（左）')
        elif c == '.':
            out.append(tape[ptr])
        elif c == ',':
            tape[ptr] = inp[ii] if ii < len(inp) else 0
            ii += 1
        elif c == '[':
            if tape[ptr] == 0:
                ip = pairs[ip]
        elif c == ']':
            if tape[ptr] != 0:
                ip = pairs[ip]

        if trace:
            print(f'  ip={ip:>3} 执行 {c!r} -> ptr={ptr} tape[0:4]={tape[0:4]}')
        ip += 1

    return bytes(out)


def demo() -> None:
    print('=' * 60)
    print('第一页：,[>+<-]>-.')
    print('=' * 60)
    p1 = ',[>+<-]>-.'
    for ch in ['B', 'Z', 'b']:
        o = run(p1, ch.encode())
        print(f'  输入 {ch}({ord(ch)})  ->  输出 {chr(o[0])}({o[0]})')
    print('  结论：输出 = 输入字符的 ASCII 值 - 1\n')

    print('=' * 60)
    print('第二页：++++++++++[>++++++++>++++++++<<-]>-.>.')
    print('=' * 60)
    p2 = '++++++++++[>++++++++>++++++++<<-]>-.>.'
    o = run(p2, trace=False)
    print('  执行过程：cell0=10 作计数器，循环 10 次给 cell1、cell2 各 +8')
    print('  -> cell1 = cell2 = 80')
    print('  -> cell1-1 = 79, cell2 = 80')
    print(f'  输出：{"".join(chr(x) for x in o)}  ({[x for x in o]})\n')

    print('=' * 60)
    print('第三页：,>,<[>+<-]>.')
    print('=' * 60)
    p3 = ',>,<[>+<-]>.'
    for s in ['AB', '33', 'aa', 'AZ']:
        o = run(p3, s.encode())
        a, b = ord(s[0]), ord(s[1])
        print(f'  输入 {s}  ({a} + {b} = {(a + b) % 256})  ->  输出 {chr(o[0])!r}({o[0]})')
    print('  结论：输出两字符 ASCII 值之和对应的字符（和超过 255 时溢出回绕）')


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo()
        return
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        code = ''.join(f.read().split())
    inp = sys.argv[2].encode() if len(sys.argv) > 2 else b''
    sys.stdout.buffer.write(run(code, inp))
    sys.stdout.buffer.write(b'\n')


if __name__ == '__main__':
    main()
