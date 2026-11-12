#!/usr/bin/env python
# Copyright 2023-2026 RicerVM 

import os, tempfile

import math

from PyQt6.QtCore import Qt, QRect, QRectF, QPointF, QSize
from PyQt6.QtGui import QBrush, QPaintEvent, QPainter, QColor, QMouseEvent, QPen, QPixmap, QPainterPath, QPolygonF
from PyQt6.QtWidgets import QDial, QPushButton, QCheckBox, QRadioButton
from Aomi.Color import Colors

# 白色对勾图标的缓存路径（临时 PNG，供 QSS 的 image url() 使用）
_CHECKMARK_PNG: str | None = None


def _checkmark_png() -> str:
    """生成一个透明底、白色对勾 + ACCENT 出锋的 PNG 并缓存到系统临时目录，返回规范化路径。"""
    global _CHECKMARK_PNG
    if _CHECKMARK_PNG:
        return _CHECKMARK_PNG
    size = 40
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    width = size * 0.13
    cap = Qt.PenCapStyle.RoundCap
    join = Qt.PenJoinStyle.RoundJoin

    # 白色主体：起笔 -> 折点 -> 第二笔（拉长后的主体部分）
    white_pen = QPen(QColor(Colors.BG_PRIMARY))
    white_pen.setWidthF(width)
    white_pen.setCapStyle(cap)
    white_pen.setJoinStyle(join)
    p.setPen(white_pen)
    white = QPainterPath()
    white.moveTo(size * 0.16, size * 0.54)
    white.lineTo(size * 0.34, size * 0.80)
    white.lineTo(size * 0.93, size * 0.10)
    p.drawPath(white)

    # 出锋出不了。。。。。。。
    p.end()
    fd, name = tempfile.mkstemp(prefix="aomi_check_", suffix=".png")
    os.close(fd)
    pm.save(name, "PNG")
    _CHECKMARK_PNG = name.replace("\\", "/")
    return _CHECKMARK_PNG

# ============================================================
# AomiPushButton
# ============================================================

class AomiPushButton(QPushButton):
    """
    Deepin 风格按钮

    """

    def __init__(self, text: str = "我是按钮", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #E6E6E6, stop:0.9 #E3E3E3);
                border: 1.45px solid {Colors.BUTTON_BORDER};
                border-radius: 12px;
                font-size: 16px; 
                outline: none;
            }}

            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #CFCFCF, stop:0.9 #CCCCCC);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #A8B2C8, stop:0.9 #B1BBCD);
                color:{Colors.ACCENT};
            }}
            QPushButton[keyboardFocused="true"] {{
                border: 2px solid {Colors.ACCENT};
                outline: none;
            }}
    """)

    # 按钮点击时不显示边框，按Tab时才显示

    def focusInEvent(self, event):
        super().focusInEvent(event)
        keyboard = event.reason() in (
            Qt.FocusReason.TabFocusReason,
            Qt.FocusReason.BacktabFocusReason,
            Qt.FocusReason.ShortcutFocusReason,
        )
        self.setProperty("keyboardFocused", keyboard)
        self.style().unpolish(self)
        self.style().polish(self)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.setProperty("keyboardFocused", False)
        self.style().unpolish(self)
        self.style().polish(self)

class AomiRadioButton(QRadioButton):

    def __init__(self, text: str = "选择1", parent=None):
        super().__init__(parent)
        self.setText(text)
        #self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(f"""
            QRadioButton {{
                font-size: 16px;
                spacing: 10px;
                outline: none;
            }}
            QRadioButton::indicator {{
                border: 1px solid {Colors.FG_PRIMARY};
                width: 14px;
                height: 14px;
                border-radius: 8.4px;
            }}
            QRadioButton::indicator:checked {{
                width: 8px;
                height: 8px;
                border-radius: 8.4px;
                border: 3.6px solid {Colors.ACCENT};
                background: {Colors.BG_PRIMARY};
            }}
            QRadioButton::indicator:checked:hover {{
                width: 8px;
                height: 8px;
                border-radius: 8.4px;
                border: 3.6px solid {Colors.ACCENT_HOVER};
                background: {Colors.BG_PRIMARY};
            }}
        """)


class AomiCheckBox(QCheckBox):

    def __init__(self, text: str = "选择1", parent=None):
        super().__init__(parent)
        self.setText(text)
        #self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(f"""
            QCheckBox {{
                font-size: 16px;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                border: 1.5px solid {Colors.FG_PRIMARY};
                width: 13px;
                height: 13px;
                border-radius: 5px;
            }}
            QCheckBox::indicator:checked {{
                width: 17px;
                height: 17px;
                border: 0px solid transparent;
                border-radius: 4px;
                background: {Colors.ACCENT};
                image: url("{_checkmark_png()}");
            }}
            QCheckBox::indicator:checked:hover {{
                width: 17px;
                height: 17px;
                border: 0px solid transparent;
                border-radius: 4px;
                background: {Colors.ACCENT_HOVER};
                image: url("{_checkmark_png()}");
            }}
        """)

# ============================================================
# AomiSwitchButton
# ============================================================

class AomiSwitchButton(QCheckBox):
    """
    Deepin 风格开关控件。

    ```python
    switch = AomiSwitchButton()
    switch.toggled.connect(lambda on: print("Switch:", on))
    ```
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self._anim = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        track_h = 24
        track_y = (h - track_h) // 2
        handle_d = 20
        handle_y = (h - handle_d) // 2

        if self.isChecked():
            track_color = QColor(Colors.ACCENT)
            handle_x = w - handle_d - 2
        else:
            track_color = QColor("#CCCCCC")
            handle_x = 2

        # 轨道
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(QRect(0, track_y, w, track_h), 8, 8)

        # 手柄
        p.setBrush(QColor("#FFFFFF"))
        #p.drawEllipse(QRect(handle_x, handle_y, handle_d, handle_d))
        p.drawRoundedRect(QRect(handle_x, handle_y, handle_d, handle_d), 8, 8)

        p.end()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())
            self.update()
        super().mouseReleaseEvent(event)

class AomiDial(QDial):
    """
    Deepin 风格旋钮（完全自绘）。

    由圆角表盘、轨道弧、已填充弧与手柄指示点组成：
    - 最小值位于左下方（7:30 方向），最大值位于右下方（4:30 方向），
      弧线沿顶部扫过，底部留 90° 缺口（与 Qt 默认 QDial 视觉一致）；
    - ``setWrapping(True)`` 时弧线闭合为整圈；
    - ``setNotchesVisible(True)`` 沿弧线外侧绘制刻度（间距由 ``notchTarget`` 控制）；
    - 值、范围、步进、键盘/鼠标交互均沿用 QDial 内建行为。

    用法:
        dial = AomiDial()
        dial.setRange(0, 100)
        dial.setValue(42)
    """

    # 表盘角度（QPainter 度，0° = 3 点钟方向，正角度逆时针）
    _START_ANGLE = 270.0   # 最小值对应角度（左下方）
    _SPAN_ANGLE = 270.0    # 未包裹时弧线扫角（顺时针，顶部大弧）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(44, 44)
        self.resize(44, 44)

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return QSize(44, 44)

    # ── 几何换算 ──

    def _value_ratio(self) -> float:
        """当前值在 [minimum, maximum] 区间内的归一化比例 [0, 1]"""
        span = self.maximum() - self.minimum()
        if span <= 0:
            return 0.0
        return (self.value() - self.minimum()) / span

    def _span_degrees(self) -> float:
        """有效扫角：未包裹 270°，包裹时闭合为整圈 360°"""
        return 360.0 if self.wrapping() else self._SPAN_ANGLE

    def _value_angle(self, ratio: float) -> float:
        """值对应的角度（QPainter 度）"""
        return self._START_ANGLE - ratio * self._span_degrees()

    # ── 绘制 ──

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        enabled = self.isEnabled()
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        diameter = min(rect.width(), rect.height())

        # 颜色（禁用时淡化为灰）
        accent = QColor(Colors.ACCENT)
        track = QColor(Colors.BORDER)
        handle_fill = QColor(Colors.BG_PRIMARY)
        if not enabled:
            accent = QColor(
                max(0, min(255, accent.red() + 80)),
                max(0, min(255, accent.green() + 80)),
                max(0, min(255, accent.blue() + 80)),
            )
            track = QColor(
                max(0, min(255, track.red() + 40)),
                max(0, min(255, track.green() + 40)),
                max(0, min(255, track.blue() + 40)),
            )

        # ── 表盘背景 ──
        p.setPen(QPen(QColor(Colors.BG_SECONDARY), 1.5))
        p.setBrush(QColor(Colors.BG_SECONDARY))
        p.drawEllipse(rect.adjusted(2, 2, -2, -2))

        # ── 刻度线（可选，notchesVisible） ──
        if self.notchesVisible():
            tick_color = QColor(Colors.FG_SECONDARY)
            if not enabled:
                tick_color = QColor(Colors.FG_DISABLED)
            r_outer = (diameter - 4) / 2.0 - 1.0
            tick_len = max(3.0, diameter * 0.06)
            tick_span = self._span_degrees()
            r_tick_mid = r_outer - tick_len / 2.0
            arc_len = 2.0 * math.pi * r_tick_mid * (tick_span / 360.0)
            count = max(2, int(round(arc_len / self.notchTarget())))
            p.setPen(QPen(tick_color, 1.0))
            for i in range(count):
                ratio_i = i / count if self.wrapping() else (i / (count - 1))
                theta = math.radians(self._value_angle(ratio_i))
                dx = math.cos(theta)
                dy = -math.sin(theta)
                p.drawLine(
                    QPointF(cx + r_outer * dx, cy + r_outer * dy),
                    QPointF(cx + (r_outer - tick_len) * dx, cy + (r_outer - tick_len) * dy),
                )

        # ── 轨道弧 ──
        ratio = self._value_ratio()
        span_deg = self._span_degrees()
        track_diameter = diameter * 0.72
        track_rect = QRectF(
            cx - track_diameter / 2, cy - track_diameter / 2,
            track_diameter, track_diameter,
        )
        pen_width = max(2.5, diameter * 0.06)
        start16 = int(self._START_ANGLE * 16)
        span16 = int(-span_deg * 16)  # 负跨度 = 顺时针

        track_pen = QPen(track, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(track_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(track_rect, start16, span16)

        # ── 已填充弧 ──
        if ratio > 0.0:
            filled16 = int(-ratio * span_deg * 16)
            accent_pen = QPen(accent, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(accent_pen)
            p.drawArc(track_rect, start16, filled16)

        # ── 手柄指示点 ──
        handle_center_radius = track_diameter / 2
        handle_radius = max(3.0, diameter * 0.11)
        theta = math.radians(self._value_angle(ratio))
        hx = cx + handle_center_radius * math.cos(theta)
        hy = cy - handle_center_radius * math.sin(theta)

        p.setPen(QPen(accent, 2.0))
        p.setBrush(handle_fill)
        p.drawEllipse(QPointF(hx, hy), handle_radius, handle_radius)

        p.end()