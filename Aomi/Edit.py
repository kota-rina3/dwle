#!/usr/bin/env python
# Copyright 2023-2026 RicerVM 

import os
import tempfile

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (QTextEdit, QPlainTextEdit, QLineEdit, QSpinBox, 
                            QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit)
from Aomi.Color import Colors

# ============================================================
# 滚动条样式（供多行编辑器复用）
# ============================================================

_SCROLLBAR_QSS = f"""
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 2px 1px 2px 1px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {Colors.SCROLLBAR_BG};
        width: 6px;
        border-radius: 3px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {Colors.SCROLLBAR_HOVER};
        width: 8px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        margin: 1px 2px 1px 2px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {Colors.SCROLLBAR_BG};
        border-radius: 3px;
        height: 4px;
        min-width: 32px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {Colors.SCROLLBAR_HOVER};
        height: 8px;
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}
"""

class AomiLineEdit(QLineEdit):
    """Deepin 风格圆角输入框"""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.IDLE};
                color: {Colors.FG_PRIMARY};
                border: 1.5px solid transparent;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                selection-background-color: {Colors.ACCENT};
            }}
            QLineEdit:focus {{
                border: 2px solid {Colors.ACCENT};
            }}
        """)


# ============================================================
# AomiTextEdit
# ============================================================

class AomiTextEdit(QTextEdit):
    """
    Deepin 风格多行文本编辑器

    - 内置 placeholder 支持（QTextEdit 原本无此功能）。
    - 焦点时 Accent 蓝色边框高亮，hover 时背景微调。
    - 只读模式自动切换为更浅的背景色。

    基本用法::

        editor = AomiTextEdit(placeholder="请输入内容…")
        editor.setPlainText("Hello Deepin")
        print(editor.toPlainText())

        # 只读模式
        editor.setReadOnly(True)

        # 信号
        editor.textChanged.connect(lambda: print("内容已更改"))
    """

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.TEXT};
                border: 1.45px solid {Colors.BUTTON_BORDER};
                font-size: 16px;
                selection-background-color: {Colors.ACCENT};
                selection-color: {Colors.BG_PRIMARY};
            }}
            {_SCROLLBAR_QSS}
        """)

# ============================================================
# AomiPlainTextEdit
# ============================================================

class AomiPlainTextEdit(QPlainTextEdit):
    """
    Deepin 风格纯文本编辑器

    与 AomiTextEdit 的差异：
    - 纯文本格式，无富文本开销，适合大文本 / 日志 / 代码。
    - 原生 placeholder（Qt 内置，无需自绘）。
    - 同样的圆角、焦点高亮、只读、亮暗主题自适应。

    基本用法::

        editor = AomiPlainTextEdit(placeholder="输入纯文本…")
        editor.setPlainText("第 1 行\\n第 2 行")
        print(editor.toPlainText())
    """

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)          # 原生支持

        self.setStyleSheet(f"""
                    QPlainTextEdit {{
                        background-color: {Colors.BG_PRIMARY};
                        color: {Colors.TEXT};
                        border: 1.45px solid {Colors.BUTTON_BORDER};
                        font-size: 16px;
                        selection-background-color: {Colors.ACCENT};
                        selection-color: {Colors.BG_PRIMARY};
                    }}
                    {_SCROLLBAR_QSS}
                """)

# ============================================================
# AomiSpinBox
# ============================================================

_SPIN_ICON_CACHE: dict = {}


def _spin_icon(kind: str, color: str) -> str:
    """生成透明底的 `+` / `-` / `arrow` 图标 PNG（抗锯齿圆头线），缓存到临时目录并返回路径。"""
    key = (kind, color)
    if key in _SPIN_ICON_CACHE:
        return _SPIN_ICON_CACHE[key]

    size = 18
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)

    c = size / 2
    half = size * 0.26
    if kind == "plus":
        p.drawLine(QPointF(c - half, c), QPointF(c + half, c))
        p.drawLine(QPointF(c, c - half), QPointF(c, c + half))
    elif kind == "minus":
        p.drawLine(QPointF(c - half, c), QPointF(c + half, c))
    else:  # arrow（V 形下拉箭头，用于日期/时间的日历按钮）
        path = QPainterPath()
        path.moveTo(c - half, c - half * 0.55)
        path.lineTo(c, c + half * 0.55)
        path.lineTo(c + half, c - half * 0.55)
        p.drawPath(path)
    p.end()

    fd, name = tempfile.mkstemp(prefix=f"aomi_spin_{kind}_", suffix=".png")
    os.close(fd)
    pm.save(name, "PNG")
    _SPIN_ICON_CACHE[key] = name.replace("\\", "/")
    return _SPIN_ICON_CACHE[key]


_SPINBOX_QSS: str | None = None


def _spinbox_stylesheet() -> str:
    """数字/日期时间输入框共用的 QSS（QAbstractSpinBox 族）。

    用 ``QAbstractSpinBox`` 选择器统一覆盖 QSpinBox / QDoubleSpinBox /
    QDateEdit / QTimeEdit / QDateTimeEdit；日期时间类额外美化日历下拉按钮。
    """
    global _SPINBOX_QSS
    if _SPINBOX_QSS is not None:
        return _SPINBOX_QSS

    plus = _spin_icon("plus", Colors.FG_SECONDARY)
    minus = _spin_icon("minus", Colors.FG_SECONDARY)
    plus_hover = _spin_icon("plus", Colors.ACCENT)
    minus_hover = _spin_icon("minus", Colors.ACCENT)
    arrow = _spin_icon("arrow", Colors.FG_SECONDARY)
    arrow_hover = _spin_icon("arrow", Colors.ACCENT)

    _SPINBOX_QSS = f"""
        QAbstractSpinBox {{
            background-color: {Colors.IDLE};
            border: 2px solid transparent;
            border-radius: 12px;
            padding: 6px 8px;
            font-size: 16px;
            color: {Colors.FG_PRIMARY};
            selection-background-color: {Colors.ACCENT};
            selection-color: #FFFFFF;
        }}
        QAbstractSpinBox:hover {{
            border-color: {Colors.BUTTON_BORDER};
        }}
        QAbstractSpinBox:focus {{
            border-color: {Colors.ACCENT};
        }}
        QAbstractSpinBox:disabled {{
            color: {Colors.FG_DISABLED};
            background-color: {Colors.BG_TERTIARY};
        }}

        /* 上下按钮：自绘 +/− 图标，去掉默认三角形 */
        QAbstractSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 24px;
            height: 14px;
            border: none;
            background: transparent;
            margin: 4px 4px 0 0;
            image: url("{plus}");
        }}
        QAbstractSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 24px;
            height: 14px;
            border: none;
            background: transparent;
            margin: 0 4px 4px 0;
            image: url("{minus}");
        }}
        QAbstractSpinBox::up-button:hover {{
            background-color: {Colors.BG_HOVER};
            border-radius: 6px;
            image: url("{plus_hover}");
        }}
        QAbstractSpinBox::down-button:hover {{
            background-color: {Colors.BG_HOVER};
            border-radius: 6px;
            image: url("{minus_hover}");
        }}
        QAbstractSpinBox::up-button:pressed {{
            background-color: {Colors.BG_PRESSED};
        }}
        QAbstractSpinBox::down-button:pressed {{
            background-color: {Colors.BG_PRESSED};
        }}

        /* 日期/时间：日历下拉按钮（打开日历弹窗） */
        QDateTimeEdit::drop-down {{
            subcontrol-origin: border;
            subcontrol-position: right center;
            width: 22px;
            border: none;
            background: transparent;
            margin: 2px 3px;
            image: url("{arrow}");
        }}
        QDateTimeEdit::drop-down:hover {{
            background-color: {Colors.BG_HOVER};
            border-radius: 6px;
            image: url("{arrow_hover}");
        }}
        QDateTimeEdit::drop-down:pressed {{
            background-color: {Colors.BG_PRESSED};
        }}

        /* 日期/时间：当前编辑分段高亮 */
        QDateTimeEdit::section {{
            background-color: transparent;
            color: {Colors.FG_PRIMARY};
            border: none;
            padding: 0 2px;
        }}
        QDateTimeEdit::section:selected {{
            background-color: {Colors.ACCENT};
            color: #FFFFFF;
            border-radius: 4px;
        }}
    """
    return _SPINBOX_QSS


class AomiSpinBox(QSpinBox):
    """
    Deepin 风格数字输入框 — 圆角背景 + 自绘 `+/−` 按钮 + 焦点高亮。

    - 去掉系统默认的小三角形箭头，换成抗锯齿自绘的 `+` / `−` 图标。
    - hover 时按钮浅灰高亮、图标转为 Accent 蓝色；pressed 时加深。
    - 焦点时 Accent 蓝色边框高亮，disabled 自动变灰。

    基本用法::

        spin = AomiSpinBox()
        spin.setRange(0, 100)
        spin.setValue(50)
        spin.valueChanged.connect(lambda v: print(v))
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_spinbox_stylesheet())


class AomiDoubleSpinBox(QDoubleSpinBox):
    """
    Deepin 风格浮点数输入框 — 圆角背景 + 自绘 `+/−` 按钮 + 焦点高亮。

    与 AomiSpinBox 相同的视觉风格，支持小数与步长::

        spin = AomiDoubleSpinBox()
        spin.setRange(0.0, 1.0)
        spin.setSingleStep(0.1)
        spin.setDecimals(2)
        spin.valueChanged.connect(lambda v: print(v))
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_spinbox_stylesheet())


class AomiTimeEdit(QTimeEdit):
    """
    Deepin 风格时间输入框 — 圆角背景 + 自绘 `+/−` 按钮。

    用法::

        time = AomiTimeEdit()
        time.setTime(QTime(14, 30))
        time.timeChanged.connect(lambda t: print(t.toString()))
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_spinbox_stylesheet())


class AomiDateEdit(QDateEdit):
    """
    Deepin 风格日期输入框 — 圆角背景 + 自绘 `+/−` 按钮 + 日历下拉按钮。

    用法::

        date = AomiDateEdit()
        date.setDate(QDate.currentDate())
        date.dateChanged.connect(lambda d: print(d.toString()))
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_spinbox_stylesheet())


class AomiDateTimeEdit(QDateTimeEdit):
    """
    Deepin 风格日期时间输入框 — 圆角背景 + 自绘 `+/−` 按钮 + 日历下拉按钮。

    用法::

        dt = AomiDateTimeEdit()
        dt.setDateTime(QDateTime.currentDateTime())
        dt.dateTimeChanged.connect(lambda dt: print(dt.toString()))
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_spinbox_stylesheet())