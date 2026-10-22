/*
 * 第 6 题 · 方向 A 的 C 示例程序
 *
 * 目的不是"打印 Hello World"，而是把这条链路走通：
 *     写代码 -> 命令行编译 -> 打断点单步调试 -> 命令行运行
 *
 * 编译（普通终端即可，不需要 x64 Native Tools Command Prompt）：
 *     build.bat
 * 它内部做三件事：跑 vcvars64.bat 把 cl.exe 拉进 PATH、补上本机 vcvars
 * 漏掉的 Windows SDK 的 INCLUDE/LIB、然后执行
 *     cl /Zi /EHsc /utf-8 /Fe:hello.exe hello.c
 * （/utf-8 是必需的：本文件有中文注释，不加会报 warning C4819。）
 *
 * 命令行运行（题目要求：敲命令，不是点界面按钮）：
 *     hello.exe
 *     hello.exe 7
 *
 * VSCode 里 Ctrl+Shift+B 编译、F5 调试，断点打在下面标记处看变量。
 */

#include <stdio.h>
#include <stdlib.h>

/* 计算阶乘。故意写成一个适合下断点的循环——
   在 VSCode 里把断点打在 for 那一行，单步几次，
   观察左侧"变量"面板里 result 和 i 的变化。 */
static long long factorial(int n) {
    long long result = 1;
    for (int i = 1; i <= n; ++i) {
        result *= i;   /* <-- 建议在这里下断点 */
    }
    return result;
}

int main(int argc, char **argv) {
    printf("Hello, OpenLab!\n");

    int n = 10;
    if (argc > 1) {
        n = atoi(argv[1]);
    }

    printf("%d! = %lld\n", n, factorial(n));

    /* 顺便证明一下命令行参数真的传进来了 */
    printf("argc = %d\n", argc);
    for (int i = 0; i < argc; ++i) {
        printf("  argv[%d] = %s\n", i, argv[i]);
    }

    return 0;
}
