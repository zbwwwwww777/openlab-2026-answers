"""LitePet 的形象——全部用 QPainter 画出来，不依赖任何外部图片资源。

这样打包/分发时不用带着一堆 png，也方便换主题配色。
一只小猫由这些部件组成：影子、身体、四条腿（走路摆动）、尾巴（摆动）、
头、耳朵、眼睛（会眨）、嘴、睡觉时头顶的 Zzz。
"""

from __future__ import annotations

from typing import Dict

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QPainter, QPen, QPolygonF,
)

# 三套配色：主体色 / 深色（耳朵、尾巴尖）/ 腮红 / 描边
THEMES: Dict[str, Dict[str, str]] = {
    "mint":  {"body": "#A8E6CF", "dark": "#5CC9A0", "blush": "#FFB7B2", "line": "#2F4858"},
    "peach": {"body": "#FFD3B6", "dark": "#FFAAA5", "blush": "#FF8B94", "line": "#5C4A4A"},
    "night": {"body": "#9DB4D6", "dark": "#5D7CA8", "blush": "#C8A2C8", "line": "#2B3A55"},
}

THEME_LABELS: Dict[str, str] = {
    "mint": "薄荷",
    "peach": "蜜桃",
    "night": "夜色",
}


def theme_names() -> list:
    return list(THEMES.keys())


class CatSprite:
    """把一只猫画进给定的 QPainter。"""

    W = 120      # 画布宽
    H = 120      # 画布高

    def __init__(self, theme: str = "mint") -> None:
        self.theme = THEMES.get(theme, THEMES["mint"])

    def set_theme(self, theme: str) -> None:
        self.theme = THEMES.get(theme, THEMES["mint"])

    # ------------------------------------------------------------ 主绘制

    def draw(self, p: QPainter, *, walk_phase: float = 0.0, blink: float = 0.0,
             sleepy: bool = False, facing_right: bool = True,
             bubble: str = "", mood: str = "") -> None:
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        line = QPen(QColor(self.theme["line"]))
        line.setWidth(2)
        p.setPen(line)
        p.setBrush(QBrush(QColor(self.theme["body"])))

        self._draw_shadow(p)
        self._draw_legs(p, walk_phase)
        self._draw_tail(p, walk_phase)
        self._draw_body(p)
        self._draw_head(p)
        self._draw_ears(p)
        self._draw_blush(p)
        self._draw_face(p, blink, sleepy)

        if sleepy:
            self._draw_zzz(p)

        if bubble:
            self._draw_bubble(p, bubble, mood)

    # ------------------------------------------------------------ 各部件

    def _draw_shadow(self, p: QPainter) -> None:
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 45)))
        p.drawEllipse(QRectF(18, 100, 84, 14))
        p.restore()

    def _draw_body(self, p: QPainter) -> None:
        p.drawEllipse(QRectF(26, 52, 68, 48))

    def _draw_legs(self, p: QPainter, phase: float) -> None:
        """走路时前后腿交替，用 sin 做往复运动。"""
        import math

        swing = math.sin(phase) * 5.0
        p.save()
        p.setBrush(QBrush(QColor(self.theme["dark"])))
        p.drawEllipse(QRectF(34 + swing, 92, 14, 12))
        p.drawEllipse(QRectF(52 - swing, 92, 14, 12))
        p.restore()

    def _draw_tail(self, p: QPainter, phase: float) -> None:
        import math

        p.save()
        pen = QPen(QColor(self.theme["dark"]))
        pen.setWidth(7)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        wag = math.sin(phase * 0.8) * 14.0
        p.drawLine(QPointF(88, 78), QPointF(88, 66))
        p.drawLine(QPointF(88, 66), QPointF(104 + wag, 52 - abs(wag) * 0.4))
        p.restore()

    def _draw_head(self, p: QPainter) -> None:
        p.drawEllipse(QRectF(28, 16, 64, 56))

    def _draw_ears(self, p: QPainter) -> None:
        p.save()
        p.setBrush(QBrush(QColor(self.theme["dark"])))
        left = QPolygonF([QPointF(30, 30), QPointF(38, 6), QPointF(50, 24)])
        right = QPolygonF([QPointF(70, 24), QPointF(82, 6), QPointF(90, 30)])
        p.drawPolygon(left)
        p.drawPolygon(right)
        p.restore()

    def _draw_blush(self, p: QPainter) -> None:
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(self.theme["blush"])))
        p.setOpacity(0.75)
        p.drawEllipse(QRectF(36, 48, 14, 9))
        p.drawEllipse(QRectF(70, 48, 14, 9))
        p.restore()

    def _draw_face(self, p: QPainter, blink: float, sleepy: bool) -> None:
        """blink: 0 = 睁眼，1 = 完全闭眼。"""
        pen = QPen(QColor(self.theme["line"]))
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)

        openness = 1.0 - blink
        if sleepy:
            openness = 0.0

        for cx in (48.0, 72.0):
            cy = 40.0
            if openness > 0.35:
                p.save()
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(self.theme["line"])))
                r = 4.6 * openness + 1.4
                p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
                # 高光
                p.setBrush(QBrush(QColor(255, 255, 255, 220)))
                p.drawEllipse(QRectF(cx - r * 0.4, cy - r * 0.7, r * 0.7, r * 0.7))
                p.restore()
            else:
                # 闭眼：画一条弧线
                p.drawArc(QRectF(cx - 7, cy - 3, 14, 8), 0, 180 * 16)

        # 嘴：一个小 w
        mouth = QPen(QColor(self.theme["line"]))
        mouth.setWidth(2)
        p.setPen(mouth)
        p.drawArc(QRectF(54, 48, 6, 6), 200 * 16, 140 * 16)
        p.drawArc(QRectF(60, 48, 6, 6), 200 * 16, 140 * 16)

    def _draw_zzz(self, p: QPainter) -> None:
        p.save()
        p.setPen(QColor(self.theme["line"]))
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QPointF(84, 26), "Z")
        p.drawText(QPointF(94, 18), "z")
        p.restore()

    # ------------------------------------------------------------ 对话气泡

    def _draw_bubble(self, p: QPainter, text: str, mood: str) -> None:
        font = QFont()
        font.setPointSize(9)
        p.setFont(font)

        # 按字数折行，简单粗暴但够用
        lines = self._wrap(text, 12)
        line_height = 16
        pad = 8
        width = max(p.fontMetrics().horizontalAdvance(s) for s in lines) + pad * 2
        if mood:
            # 心情行用 7pt 小字单独量宽，避免比正文行宽而被截断
            small_fm = QFontMetrics(QFont("", 7))
            width = max(width, small_fm.horizontalAdvance("心情：" + mood) + pad * 2)
        height = line_height * len(lines) + pad * 2 + (14 if mood else 0)

        # 气泡右对齐到窗口右缘（而不是从右缘向右画，否则整段画出窗口外）
        x = self.W - 4.0 - width
        x = max(4.0, x)
        y = 2.0
        rect = QRectF(x, y, width, height)

        p.save()
        p.setPen(QPen(QColor(self.theme["line"])))
        p.setBrush(QBrush(QColor(255, 255, 255, 240)))
        p.drawRoundedRect(rect, 10, 10)
        # 气泡小尾巴
        p.drawPolygon(QPolygonF([
            QPointF(x + 10, y + height),
            QPointF(x + 18, y + height),
            QPointF(x + 8, y + height + 8),
        ]))

        p.setPen(QColor(self.theme["line"]))
        for i, s in enumerate(lines):
            p.drawText(QPointF(x + pad, y + pad + 12 + i * line_height), s)
        if mood:
            p.setPen(QColor(120, 120, 120))
            small = QFont()
            small.setPointSize(7)
            p.setFont(small)
            p.drawText(QPointF(x + pad, y + height - 5), "心情：" + mood)
        p.restore()

    @staticmethod
    def _wrap(text: str, per_line: int) -> list:
        """按固定字数硬折行（中文场景够用，不用引入 QTextLayout）。"""
        out = []
        for i in range(0, len(text), per_line):
            out.append(text[i:i + per_line])
        return out[:4]
