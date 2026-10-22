/*
 * 第 6 题 · 方向 A 的 C 示例程序
 *
 * 目的不是"打印 Hello World"，而是把这条链路走通：
 *     写代码 -> 命令行编译 -> 打断点单步调试 -> 命令行运行
 *
 * 编译（必须在 x64 Native Tools Command Prompt / 或已跑过 vcvars64 的会话里）：
 *     cl /Zi /EHsc /Fe:hello.exe hello.c
 *
 * 或者在 VSCode 里 Ctrl+Shift+B（调用 .vscode/tasks.json）
 * 然后 F5 启动调试，在下面标记的断点处停住看变量。
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
