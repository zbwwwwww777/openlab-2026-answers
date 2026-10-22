"""LitePet 的窗口层：无边框透明窗口 + 走动动画 + 拖拽/点击/菜单/快捷键。

交互一览：
    左键单击     —— 戳一下，它会说话，好感度 +1
    左键拖拽     —— 把它拖到屏幕任何地方
    左键双击     —— 坐下 / 起来（切换是否到处走）
    右键         —— 菜单：喂食、换主题、暂停走动、关于、退出
    Ctrl+Alt+P  —— 归位到屏幕右下角
    Ctrl+Alt+H  —— 隐藏 / 显示
    Ctrl+Alt+Q  —— 退出
"""

from __future__ import annotations

import logging
import math
import random
from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import QMenu, QMessageBox, QWidget

from .brain import Brain, period_label
from .memory import Memory
from .sprite import CatSprite, THEME_LABELS, theme_names

LOG = logging.getLogger("litepet.window")

WIN_W = 200
WIN_H = 170        # 顶部 50px 是气泡预留区，下方 120px 画猫
CAT_TOP = 50       # 猫的画布在窗口内的纵向偏移（气泡区的下方）

TICK_MS = 40          # 动画帧间隔
AUTOSAVE_MS = 30_000  # 自动存档间隔
IDLE_MS = 25_000      # 多久没理它就自己嘀咕一句

# 到点提醒（HH:MM -> 提醒语）
REMINDERS = {
    "09:00": "九点了，先喝口水再开工。",
    "12:00": "午饭时间，别硬扛。",
    "15:00": "下午三点，站起来活动两分钟。",
    "18:00": "下班/下课啦，收拾一下吧。",
    "23:00": "十一点了，该睡了，明天再战。",
}


class PetWindow(QWidget):
    """一只住在桌面上的猫。"""

    def __init__(self, brain: Brain, memory: Memory, *, paused: bool = False) -> None:
        super().__init__()
        self.brain = brain
        self.memory = memory
        self.state = brain.state
        self.sprite = CatSprite(self.state.theme)

        # ---- 窗口外观：无边框 + 透明 + 置顶 + 不进任务栏
        self.setWindowTitle(self.state.name)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(WIN_W, WIN_H)
        self.setMouseTracking(True)

        # ---- 运动状态
        geo = self._screen_geometry()
        self.x = self.state.pos.get("x", geo.right() - WIN_W - 40)
        self.y = self.state.pos.get("y", geo.bottom() - WIN_H - 40)
        self._clamp_to_screen(geo)
        self.vx = random.choice([-1.0, 1.0])
        self.vy = random.choice([-0.6, 0.6])
        self.walk_phase = 0.0
        self.facing_right = self.vx >= 0

        self.dragging = False
        self.drag_offset = QPoint(0, 0)
        self.drag_moved = False
        self.paused = paused        # 菜单里的"暂停走动"
        self.sitting = False        # 双击切换的"坐下"
        self.hidden = False

        # ---- 说话 / 眨眼
        self.bubble_text = ""
        self.bubble_until: Optional[datetime] = None
        self._blink_at = datetime.now() + timedelta(seconds=3)
        self._blink_progress = 0.0
        self._fired_reminders: set = set()

        self._build_menu()
        self._build_shortcuts()
        self._build_timers()

        # 出场第一句话
        self.say(self.brain.greet_back(), duration=6)
        LOG.info("宠物 %s 已启动（好感度 %d，心情：%s）",
                 self.state.name, self.state.affinity, self.brain.mood)

    # ------------------------------------------------------------ 构造辅助

    def _build_menu(self) -> None:
        self.menu = QMenu(self)

        act_feed = QAction("喂它一根小鱼干", self)
        act_feed.triggered.connect(self._on_feed)
        self.menu.addAction(act_feed)

        self.menu.addSeparator()

        self.theme_actions = {}
        for name in theme_names():
            act = QAction(f"换颜色：{THEME_LABELS[name]}", self)
            act.setCheckable(True)
            act.setChecked(name == self.state.theme)
            act.triggered.connect(lambda checked=False, n=name: self._on_theme(n))
            self.menu.addAction(act)
            self.theme_actions[name] = act

        self.menu.addSeparator()

        self.act_pause = QAction("暂停走动", self)
        self.act_pause.setCheckable(True)
        self.act_pause.setChecked(self.paused)
        self.act_pause.triggered.connect(self._on_toggle_pause)
        self.menu.addAction(self.act_pause)

        act_about = QAction("关于 / 统计", self)
        act_about.triggered.connect(self._on_about)
        self.menu.addAction(act_about)

        self.menu.addSeparator()

        act_quit = QAction("退出", self)
        act_quit.triggered.connect(self.close)
        self.menu.addAction(act_quit)

    def _build_shortcuts(self) -> None:
        def bind(seq: str, slot) -> None:
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
            sc.activated.connect(slot)

        bind("Ctrl+Alt+P", self._reset_position)
        bind("Ctrl+Alt+H", self._toggle_hidden)
        bind("Ctrl+Alt+Q", self.close)

    def _build_timers(self) -> None:
        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(TICK_MS)
        self.tick_timer.timeout.connect(self._on_tick)
        self.tick_timer.start()

        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(IDLE_MS)
        self.idle_timer.timeout.connect(lambda: self.say(self.brain.idle(), duration=5))
        self.idle_timer.start()

        self.save_timer = QTimer(self)
        self.save_timer.setInterval(AUTOSAVE_MS)
        self.save_timer.timeout.connect(self.save_state)
        self.save_timer.start()

    # ------------------------------------------------------------ 几何

    def _screen_geometry(self) -> QRect:
        screen = self.screen()
        if screen is None:
            return QRect(0, 0, 1280, 720)
        return screen.availableGeometry()

    def _clamp_to_screen(self, geo: Optional[QRect] = None) -> None:
        """别让猫跑到屏幕外面去。"""
        geo = geo or self._screen_geometry()
        self.x = max(geo.left(), min(self.x, geo.right() - WIN_W))
        self.y = max(geo.top(), min(self.y, geo.bottom() - WIN_H))

    # ------------------------------------------------------------ 绘制

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt 规定的驼峰命名)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        now = datetime.now()
        bubble = self.bubble_text if (self.bubble_until and now < self.bubble_until) else ""

        # 猫画在气泡区下方：整体下移 CAT_TOP，气泡单独画在顶部预留区
        p.save()
        p.translate(0, CAT_TOP)
        self.sprite.draw(
            p,
            walk_phase=self.walk_phase,
            blink=self._blink_progress,
            sleepy=self.brain.is_sleepy() and not self.sitting,
            facing_right=self.facing_right,
        )
        p.restore()

        if bubble:
            self.sprite.draw_bubble(p, bubble, self.brain.mood, WIN_W)
        p.end()

    # ------------------------------------------------------------ 主循环

    def _on_tick(self) -> None:
        now = datetime.now()

        # 眨眼
        if now >= self._blink_at:
            self._blink_progress += 0.25
            if self._blink_progress >= 1.0:
                self._blink_progress = 0.0
                self._blink_at = now + timedelta(seconds=random.uniform(2.5, 6.0))
        else:
            self._blink_progress = 0.0

        # 走动
        if not self.dragging and not self.paused and not self.hidden and not self.sitting:
            behavior = self.brain.behavior()
            speed = 1.1 * behavior["speed"]

            if random.random() < 0.03:          # 偶尔改个方向
                self.vx += random.uniform(-0.8, 0.8)
                self.vy = max(-0.8, min(0.8, self.vy + random.uniform(-0.4, 0.4)))
                norm = math.hypot(self.vx, self.vy) or 1.0
                self.vx, self.vy = self.vx / norm, self.vy / norm

            self.x += self.vx * speed
            self.y += self.vy * speed
            self.walk_phase += 0.35 * speed
            self.facing_right = self.vx >= 0

            geo = self._screen_geometry()
            if self.x <= geo.left() or self.x + WIN_W >= geo.right():
                self.vx = -self.vx
            if self.y <= geo.top() or self.y + WIN_H >= geo.bottom():
                self.vy = -self.vy
            self._clamp_to_screen(geo)
            self.move(int(self.x), int(self.y))

        self._check_reminder(now)

        # 气泡过期就重画一次，让它消失
        if self.bubble_until and now >= self.bubble_until:
            self.bubble_until = None
        self.update()

    def _check_reminder(self, now: datetime) -> None:
        key = now.strftime("%H:%M")
        if key in REMINDERS and key not in self._fired_reminders:
            self._fired_reminders.add(key)
            self.say("⏰ " + REMINDERS[key], duration=10)
            LOG.info("触发定时提醒 %s", key)
        if now.hour == 0 and now.minute == 0:
            self._fired_reminders.clear()

    # ------------------------------------------------------------ 说话

    def say(self, text: str, duration: float = 4.0) -> None:
        self.bubble_text = text
        self.bubble_until = datetime.now() + timedelta(seconds=duration)
        LOG.info("[%s] %s", self.state.name, text)
        self.update()

    # ------------------------------------------------------------ 鼠标

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_moved = False
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.menu.exec(event.globalPosition().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.dragging:
            new_pos = event.globalPosition().toPoint() - self.drag_offset
            self.drag_moved = True
            self.x, self.y = new_pos.x(), new_pos.y()
            self._clamp_to_screen()
            self.move(int(self.x), int(self.y))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            if not self.drag_moved:
                # 没拖动 => 算作"戳一下"
                self.say(self.brain.poke(), duration=4)
            self.save_state()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self.sitting = not self.sitting
        self.say("我坐下了（再双击站起来）。" if self.sitting else "起来活动活动！", duration=3)
        event.accept()

    # ------------------------------------------------------------ 菜单回调

    def _on_feed(self) -> None:
        self.say(self.brain.feed(), duration=4)
        self.save_state()

    def _on_theme(self, name: str) -> None:
        self.state.theme = name
        self.sprite.set_theme(name)
        for n, act in self.theme_actions.items():
            act.setChecked(n == name)
        self.say(f"换上了{THEME_LABELS[name]}色，好看吗？", duration=3)
        self.save_state()

    def _on_toggle_pause(self) -> None:
        self.paused = not self.paused
        self.act_pause.setChecked(self.paused)
        LOG.info("走动已%s", "暂停" if self.paused else "恢复")

    def _on_about(self) -> None:
        s = self.state
        QMessageBox.information(
            self,
            f"关于 {s.name}",
            f"名字：{s.name}\n"
            f"好感度：{s.affinity}/100（{self.brain.mood}）\n"
            f"被戳次数：{s.total_clicks}\n"
            f"被喂次数：{s.total_feeds}\n"
            f"当前时段：{period_label()}\n"
            f"最近说过：\n  " + ("\n  ".join(s.history[-5:]) or "（还没有）"),
        )

    # ------------------------------------------------------------ 快捷键回调

    def _reset_position(self) -> None:
        geo = self._screen_geometry()
        self.x = geo.right() - WIN_W - 20
        self.y = geo.bottom() - WIN_H - 20
        self.move(int(self.x), int(self.y))
        self.say("我回到老地方了。", duration=3)

    def _toggle_hidden(self) -> None:
        self.hidden = not self.hidden
        self.setHidden(self.hidden)

    # ------------------------------------------------------------ 生命周期

    def save_state(self) -> None:
        self.state.pos = {"x": int(self.x), "y": int(self.y)}
        self.memory.save(self.state)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.save_state()
        LOG.info("宠物 %s 已退出，状态已保存", self.state.name)
        super().closeEvent(event)
