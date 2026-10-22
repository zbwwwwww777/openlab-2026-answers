# 第 6 题 · 方向 A：VSCode 工作台

选的是 **C/C++**（顺带把 Python 也配了），链路完整跑通：写代码 → 命令行编译 → 断点调试 → 命令行运行。

## 目录说明

```
q6_env/
├── hello.c             # C 示例：阶乘，断点打在 factorial() 的 result *= i
├── hello.py            # Python 示例：等差数列求和，断点打在 acc += i
├── build.bat           # 一键配置 MSVC 环境并编译（普通终端可用）
├── version_info.bat    # 一次打印机器/路径/版本信息，方便截图
└── .vscode/
    ├── tasks.json      # Ctrl+Shift+B 编译；另有命令行运行任务
    └── launch.json     # F5 调试（cppvsdbg 调 C，debugpy 调 Python）
```

## 三条命令（题目要求：在终端里敲，不点界面按钮）

```bat
build.bat          :: 编译（= cl /Zi /EHsc /utf-8 /Fe:hello.exe hello.c）
hello.exe 7        :: 运行，7! = 5040
python hello.py 20 :: Python 那条链，1+...+20 = 210
```

调试：VSCode 里打开本文件夹 → 在 `result *= i;` 那行左侧点出红点 → F5 → F10 单步 → 看左侧「变量」面板。

## 需要截的图（对应答卷 6.3）

| # | 截图内容 | 怎么得到 |
| :--- | :--- | :--- |
| 1 | 版本信息 | 集成终端里跑 `version_info.bat` |
| 2 | 命令行编译 | 集成终端里跑 `build.bat` |
| 3 | 命令行运行 | 集成终端里跑 `hello.exe 7` |
| 4 | 断点命中 | F5 调试，程序停在断点上，左侧变量面板可见 `result` / `i` |
| 5 | Python 那条链 | 终端跑 `python hello.py 20`，或 F5 用 debugpy 断点 |

加分点：截图里带上**你的路径和用户名**（`version_info.bat` 已经打出来了），证明是本机的。

## 已知的两个坑（详见答卷 6.4）

1. **cl.exe 不在 PATH**：普通终端里敲 `cl` 会报"不是内部或外部命令"。`build.bat` 里先 `call vcvars64.bat` 解决。
2. **vcvars64 在本机没接上 Windows SDK**：跑完它以后 `INCLUDE` 里只有 MSVC 自己的目录，没有 Windows Kits，于是 `cl` 报 `fatal error C1083: 无法打开包括文件: 'stdio.h'`，链接时还会 `LNK1104: 无法打开 kernel32.lib`。`build.bat` 里手工把 SDK 的 `Include/…/ucrt|um|shared|winrt` 和 `Lib/…/ucrt\x64|um\x64` 追加进 `INCLUDE` / `LIB` 才通。
   （同一个坑在第 3 题编译 llama.cpp 时也遇到了，`build.ps1` 里用的是同一套兜底。）
3. 中文注释会触发 `warning C4819`（代码页 936 表示不了），加 `/utf-8` 消除。
