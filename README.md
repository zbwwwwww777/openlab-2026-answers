# OpenLab 2026 纳新笔试 · 答卷仓库

> 学号_姓名_Openlab初试 —— 本仓库是这次笔试所有题目答案与源码的存放地。

## 目录结构

```
openlab-answers/
├── README.md              本文件
├── .gitignore             忽略环境/模型/构建产物，仓库控制在 10MB 以下
├── 答卷.md                正式答卷（Markdown 源，导出 PDF 后提交）
├── res/                   截图、渲染图等资源（答卷里用相对路径引用）
│   └── litepet_preview.png
└── src/                   各题代码
    ├── q3_llama/          第 3 题：llama.cpp 编译与运行脚本
    │   ├── build.ps1      装工具链 + 从源码编译，日志写入 build_log.txt
    │   └── run.ps1        跑 llama-cli，并做 CPU / GPU 速度对比
    ├── q4_litepet/        第 4 题：桌面宠物 LitePet（二档·桌宠）
    │   ├── litepet/       brain / memory / sprite / window / main
    │   ├── tests/         16 个单元测试 + GUI 冒烟测试
    │   └── README.md      项目说明
    ├── q6_env/            第 6 题：VSCode 工作台示例工程
    │   ├── hello.c / hello.py
    │   └── .vscode/       tasks.json（编译）+ launch.json（调试）
    └── q7_brainfuck/      第 7 题：Brainfuck 解释器与答案验证脚本
        └── bf_interpreter.py
```

## 各题完成情况

| 题号 | 题目 | 状态 | 说明 |
| :--- | :--- | :---: | :--- |
| 1 | 让阅卷的人舒服一点 | ✅ | 选 Markdown 排版，统一标题/代码块/表格/相对路径图片 |
| 2 | Git 与 GitHub | 🔧 | 目录结构与 `.gitignore` 已就绪，待初始化仓库并推送 |
| 3 | ！？模型？！ | 🔧 | 编译/运行脚本已写好，参数问题的书面答案已完成；编译待在本机执行 |
| 4 | 君子六艺——御 | ✅ | LitePet 桌面宠物，二档 + 两项扩展任务，含单测 |
| 5 | 阅读理解（HarmonyOS） | ✅ | 全部小问已作答，均对照官方文档 |
| 6 | 环境三选一 | 🔧 | 选方向 A（VSCode + C/C++），示例工程与调试配置就绪 |
| 7 | 奇怪的书 | ✅ | 三页全部解出，附解释器实测 |

✅ 已完成　🔧 需在本机执行后补齐截图/日志

## 怎么复现

```bash
# 第 7 题：验证三页答案
python src/q7_brainfuck/bf_interpreter.py --demo

# 第 4 题：跑起来
pip install PySide6
python -m litepet                       # 需先 cd src/q4_litepet
python src/q4_litepet/tests/test_brain.py
```

第 3、6 题需要在本机执行，脚本见 `src/q3_llama/build.ps1` 与 `src/q6_env/`。

## 关于本仓库的 Git 使用

- 每个题目一个目录，代码统一放 `src/`，资源统一放 `res/`；
- `.gitignore` 明确排除了 `*.gguf`、`llama.cpp/`、Rust 的 `target/` 等大文件，保证仓库远小于 10 MB；
- 提交按题目分次进行，每次提交只做一件事，便于回溯历史版本。
