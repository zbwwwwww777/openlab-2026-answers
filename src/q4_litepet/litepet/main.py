"""LitePet 入口。

    python -m litepet                  # 启动宠物
    python -m litepet --name 小花       # 给宠物起个名字
    python -m litepet --theme peach    # 换配色
    python -m litepet --reset          # 清空存档，重新开始
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from .brain import Brain
from .memory import Memory, ensure_dir, setup_logging
from .sprite import THEME_LABELS, theme_names
from .window import PetWindow


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="litepet",
        description="LitePet —— 一只住在你桌面上的猫（OpenLab 纳新题·君子六艺「御」）",
    )
    p.add_argument("--name", help="给宠物起个名字（只在第一次创建时生效）")
    p.add_argument("--theme", choices=theme_names(), help="配色：" +
                   " / ".join(f"{k}={v}" for k, v in THEME_LABELS.items()))
    p.add_argument("--pause", action="store_true", help="启动后不自己乱走")
    p.add_argument("--reset", action="store_true", help="清空存档")
    p.add_argument("--data-dir", type=Path, default=None, help="存档目录，默认 ~/.litepet")
    p.add_argument("-v", "--verbose", action="store_true", help="输出调试日志")
    return p


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)

    import logging

    log_path = setup_logging(args.data_dir,
                             logging.DEBUG if args.verbose else logging.INFO)

    memory = Memory(args.data_dir)
    if args.reset:
        memory.reset()

    state = memory.load()
    if args.name:
        state.name = args.name
    if args.theme:
        state.theme = args.theme

    brain = Brain(state)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = PetWindow(brain, memory, paused=args.pause)
    window.show()

    print(f"LitePet 已启动：{state.name}｜存档目录 {ensure_dir(args.data_dir)}｜日志 {log_path}")
    print("左键戳它 / 拖动它，双击让它坐下，右键看菜单，Ctrl+Alt+Q 退出。")

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
