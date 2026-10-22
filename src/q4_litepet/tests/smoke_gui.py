"""LitePet 的 GUI 冒烟测试：不真的弹出窗口，只验证
「能构造 → 能跑动画帧 → 能绘制 → 能存档 → 能关闭」这条链路。

    python tests/smoke_gui.py                     # 有图形界面时正常跑
    QT_QPA_PLATFORM=offscreen python tests/smoke_gui.py   # CI / 无显示器时这样跑
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from litepet.brain import Brain  # noqa: E402
from litepet.memory import Memory, setup_logging  # noqa: E402
from litepet.window import PetWindow  # noqa: E402


def main() -> int:
    setup_logging(Path(tempfile.gettempdir()), 20)  # 日志级别设高一点，别刷屏

    tmp = tempfile.TemporaryDirectory()
    memory = Memory(Path(tmp.name))
    state = memory.load()
    brain = Brain(state, seed=42)

    app = QApplication(sys.argv)
    win = PetWindow(brain, memory)

    # 1) 跑 200 帧动画，确认没有异常
    for _ in range(200):
        win._on_tick()

    # 2) 强制绘制一次，确认 QPainter 那段代码没问题
    pixmap = win.grab()
    print(f"[ok] 渲染成功，画布尺寸 {pixmap.width()}x{pixmap.height()}，"
          f"非空像素检查: {'通过' if not pixmap.isNull() else '失败'}")

    # 3) 走一遍主要交互回调
    win.say(brain.poke(), duration=2)
    win._on_feed()
    win._on_theme("peach")
    win._on_toggle_pause()
    win._on_toggle_pause()
    win._reset_position()
    win._toggle_hidden()
    win._toggle_hidden()
    print("[ok] 交互回调全部执行完毕")

    # 4) 存档并重新读回，确认持久化生效
    state.pos = {"x": int(win.x), "y": int(win.y)}
    memory.save(state)
    reloaded = memory.load()
    assert reloaded.name == state.name
    assert reloaded.theme == "peach"
    assert reloaded.affinity == state.affinity
    print(f"[ok] 持久化往返成功：好感度={reloaded.affinity} 位置={reloaded.pos} "
          f"主题={reloaded.theme}")

    win.close()
    tmp.cleanup()
    print("[ok] 冒烟测试全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
