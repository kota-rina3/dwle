#!/usr/bin/env python
# Copyright 2023-2026 RicerVM

import os, tempfile, threading

from PyQt6.QtCore import QCoreApplication, QRectF, Qt, QPoint, QSize, QTimer
from PyQt6.QtGui import (QColor, QFont, QFontDatabase, QKeyEvent, QPaintEvent,
                         QPainter, QPainterPath, QPen, QPixmap)
from PyQt6.QtWidgets import (QApplication, QComboBox, QGraphicsDropShadowEffect,
                            QListWidget, QListWidgetItem, QVBoxLayout,
                            QFontComboBox, QWidget)
from Aomi.Color import Colors, AomiTheme, Theme


# ============================================================
# 主题辅助
# ============================================================

_DOWNARROW_PNG: str | None = None


def _downarrow_png() -> str:
    """生成一个透明底、深灰色下拉箭头（V 形）的 PNG 并缓存到临时目录，返回路径。"""
    global _DOWNARROW_PNG
    if _DOWNARROW_PNG:
        return _DOWNARROW_PNG
    size = 40
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(Colors.FG_SECONDARY))
    pen.setWidthF(size * 0.06)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    path = QPainterPath()
    path.moveTo(size * 0.26, size * 0.34)
    path.lineTo(size * 0.50, size * 0.64)
    path.lineTo(size * 0.74, size * 0.34)
    p.drawPath(path)
    p.end()
    fd, name = tempfile.mkstemp(prefix="aomi_arrow_", suffix=".png")
    os.close(fd)
    pm.save(name, "PNG")
    _DOWNARROW_PNG = name.replace("\\", "/")
    return _DOWNARROW_PNG

def _is_dark() -> bool:
    theme = AomiTheme.instance()
    return theme is not None and theme.current_theme == Theme.DARK


def _theme_color(key: str) -> str:
    """按当前主题返回颜色令牌值；主题未加载时用亮色。"""
    if _is_dark():
        return Colors.dark().get(key, getattr(Colors, key))
    return getattr(Colors, key)


# ============================================================
# 圆角卡片（自绘抗锯齿圆角背景 + 边框）
# ============================================================

class _PopupCard(QWidget):
    """
    下拉列表的圆角卡片。

    用 QPainter 的 Antialiasing 自绘圆角，而不是 QSS 的 border-radius
    （后者只作用于绘制、不裁角）或 QRegion mask（1-bit 无抗锯齿、圆角有锯齿）。
    """

    RADIUS = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor(_theme_color("BG_PRIMARY"))
        border = QColor(_theme_color("BORDER"))

        path = QPainterPath()
        path.addRoundedRect(
            QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5),
            self.RADIUS, self.RADIUS,
        )
        p.fillPath(path, bg)
        p.setPen(QPen(border, 1))
        p.drawPath(path)
        p.end()


# ============================================================
# 自定义下拉弹窗
# ============================================================

class _AomiComboPopup(QWidget):
    """
    替代 QComboBox 内置弹窗的下拉列表：
    圆角卡片 + 柔和阴影 + QListWidget，圆角真正平滑。
    """

    SHADOW_MARGIN = 28   # 阴影扩展边距
    ITEM_HEIGHT   = 34   # 单项高度
    MAX_VISIBLE   = 10   # 最多同时显示的项数（超出则在列表内滚动）
    GAP           = 4    # 与下拉框的间距

    def __init__(self, combo: QComboBox):
        super().__init__(combo)
        self._combo = combo
        self._built_key = None   # 已构建条目的签名，用于避免每次弹出都重建
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 圆角卡片 + 阴影
        self._card = _PopupCard()
        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self._card.setGraphicsEffect(shadow)

        # 列表
        self._list = QListWidget(self._card)
        self._list.setMouseTracking(True)
        self._list.viewport().setAutoFillBackground(False)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._apply_list_style()

        # 布局：外圈留出阴影空间，卡片内列表上下留白
        outer = QVBoxLayout(self)
        outer.setContentsMargins(self.SHADOW_MARGIN, self.SHADOW_MARGIN,
                                 self.SHADOW_MARGIN, self.SHADOW_MARGIN)
        outer.addWidget(self._card)

        card = QVBoxLayout(self._card)
        card.setContentsMargins(0, 6, 0, 6)
        card.addWidget(self._list)

    # ── 列表样式 ─────────────────────────────────────────────
    def _apply_list_style(self):

        self._list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 0 4px;
                margin: 1px 6px;
                border-radius: 12px;
                color: {Colors.FG_PRIMARY};
            }}
            QListWidget::item:hover {{
                background-color: {Colors.ACCENT};
                color: #FFFFFF;
            }}
            
            QScrollBar:vertical {{
                background: transparent;
                width: 12px;
                margin: 2px 3px 2px 1px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {Colors.SCROLLBAR_BG};
                width: 8px;
                border-radius: 4px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {Colors.SCROLLBAR_HOVER};
                width: 10px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)

    # ── 弹出 ────────────────────────────────────────────────
    def popup(self):
        combo = self._combo
        count = combo.count()

        # 重建条目：仅在内容变化时重建，避免每次弹出都重建大量条目（字体列表尤慢）
        key = tuple(combo.itemText(i) for i in range(count))
        if key != self._built_key:
            self._list.clear()
            is_font_combo = isinstance(combo, QFontComboBox)
            for i in range(count):
                item = QListWidgetItem(combo.itemIcon(i), combo.itemText(i))
                item.setSizeHint(QSize(0, self.ITEM_HEIGHT))
                if is_font_combo:
                    # 字体下拉：每项用其对应字体渲染
                    font = QFont(combo.itemText(i))
                    font.setPixelSize(14)
                    item.setFont(font)
                self._list.addItem(item)
            self._built_key = key

        current = combo.currentIndex()
        if current >= 0:
            self._list.setCurrentRow(current)
            self._list.scrollToItem(self._list.item(current))

        # 尺寸：宽度与下拉框一致，高度按条目数（超限滚动）
        visible = max(1, min(count, self.MAX_VISIBLE))
        list_h = visible * self.ITEM_HEIGHT
        card_w = max(combo.width(), 100)
        self._list.setFixedHeight(list_h)
        self.setFixedSize(card_w + self.SHADOW_MARGIN * 2,
                          list_h + 12 + self.SHADOW_MARGIN * 2)

        # 定位：卡片左对齐下拉框，位于其正下方
        anchor = combo.mapToGlobal(QPoint(0, combo.height()))
        self.move(anchor.x() - self.SHADOW_MARGIN,
                  anchor.y() + self.GAP - self.SHADOW_MARGIN)

        # 每次弹出刷新样式（跟随主题切换）
        self._apply_list_style()
        self.show()
        self.grabKeyboard()

    def _on_item_clicked(self, item: QListWidgetItem):
        self._combo.setCurrentIndex(self._list.row(item))
        self.close()

    # ── 键盘导航 ────────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
            return
        if key == Qt.Key.Key_Up or key == Qt.Key.Key_Down:
            row = self._list.currentRow()
            row = (max(0, row - 1) if key == Qt.Key.Key_Up
                   else min(self._list.count() - 1, row + 1))
            self._list.setCurrentRow(row)
            self._list.scrollToItem(self._list.item(row))
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            row = self._list.currentRow()
            if row >= 0:
                self._combo.setCurrentIndex(row)
            self.close()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.releaseKeyboard()
        super().closeEvent(event)


# ============================================================
# 下拉框公共样式
# ============================================================

def _combo_stylesheet() -> str:
    """AomiComboBox / AomiFontCombo 共用的下拉框 QSS。"""
    return f"""
        QComboBox {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #E6E6E6, stop:0.9 #E3E3E3);
            border: 2px solid transparent;          /* 固定宽度，focus 只改色不抖动 */
            border-radius: 12px;
            padding: 8px 10px 8px 14px;            
            font-size: 16px;
            color: {Colors.FG_PRIMARY};
            selection-background-color: {Colors.ACCENT};
            selection-color: #FFFFFF;
        }}
        QComboBox:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #CFCFCF, stop:0.9 #CCCCCC);
        }}
        QComboBox:focus {{
            border-color: {Colors.ACCENT};
        }}
        QComboBox:disabled {{
            color: {Colors.FG_DISABLED};
        }}

        /* 可编辑/字体预览的输入框：透明融入圆角背景 */
        QComboBox QLineEdit {{
            background: transparent;
            border: none;
            padding: 0;
            color: {Colors.FG_PRIMARY};
            selection-background-color: {Colors.ACCENT};
            selection-color: #FFFFFF;
        }}

        /* 下拉箭头 */
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: right center;
            border: none;
            width: 20px;
            image: url("{_downarrow_png()}");
        }}
        QComboBox[keyboardFocused="true"] {{
            border: 2px solid {Colors.ACCENT};
            outline: none;
        }}
    """


class _ComboPopupMixin:
    """圆角自绘下拉弹窗 + 键盘焦点边框（AomiComboBox 与 AomiFontCombo 共用）。"""

    def showPopup(self):
        if self.count() == 0:
            return
        if self._popup is None:
            self._popup = _AomiComboPopup(self)
        self._popup.popup()

    def hidePopup(self):
        if self._popup is not None:
            self._popup.close()

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


# ============================================================
# AomiComboBox
# ============================================================

class AomiComboBox(_ComboPopupMixin, QComboBox):
    """
    Deepin 风格下拉选择框 — 圆角 + 自绘箭头 + 圆角下拉列表 + 亮暗主题自适应。

    - 下拉列表使用自绘圆角卡片 + 阴影，圆角真正平滑（非 QSS/mask 的硬边）。
    - 下拉列表支持 hover 高亮、选中项浅蓝背景。
    - 自动跟随 AomiTheme 切换亮色/暗色样式。
    - 支持可编辑模式（``setEditable(True)``）。

    用法::

        combo = AomiComboBox()
        combo.addItems(["选项一", "选项二", "选项三"])
        combo.currentIndexChanged.connect(lambda i: print(i))

        # 可编辑模式
        combo.setEditable(True)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(False)
        self._popup: _AomiComboPopup | None = None

        self.setStyleSheet(_combo_stylesheet())


class AomiFontCombo(_ComboPopupMixin, QFontComboBox):
    """
    Deepin 风格字体选择框 — 复用 AomiComboBox 的圆角自绘下拉列表与主题自适应。

    - 自动列出系统可用字体，下拉每项用对应字体渲染。
    - 下拉列表使用自绘圆角卡片 + 阴影 + hover 高亮。
    - 自动跟随 AomiTheme 切换亮色/暗色样式。

    用法::

        combo = AomiFontCombo()
        combo.setDefaultFont("Microsoft YaHei")
        combo.currentFontChanged.connect(lambda f: print(f.family()))
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup: _AomiComboPopup | None = None
        self.setStyleSheet(_combo_stylesheet())
        # QFontComboBox 依赖 lineEdit 显示当前字体名；设为只读避免手动输入。
        line_edit = self.lineEdit()
        if line_edit is not None:
            line_edit.setReadOnly(True)
        # 让关闭状态的显示区用当前字体渲染，实现“预览所选字体”。
        self.currentFontChanged.connect(self._schedule_preview_font)
        self._schedule_preview_font(self.currentFont())

    def _schedule_preview_font(self, font: QFont):
        # 延迟到事件循环再应用，避免 QSS 的 deferred polish 覆盖 lineEdit 字体。
        QTimer.singleShot(0, lambda: self._apply_preview_font(font))

    def _apply_preview_font(self, font: QFont):
        """把显示区字体族设为当前选中字体，实现字体预览（固定字号 16px）。"""
        line_edit = self.lineEdit()
        if line_edit is None:
            return
        preview = QFont(font)
        preview.setPixelSize(16)
        line_edit.setFont(preview)

    @staticmethod
    def preload():
        """立即在后台线程预热字体数据库（需 QApplication 已完全构造）。

        通常无需手动调用——模块导入后会自动等待 QApplication 就绪并预热；
        此方法用于希望在特定时机显式触发预热的场景。
        """
        if QApplication.instance() is None or QCoreApplication.startingUp():
            return
        threading.Thread(target=_warm_fonts, daemon=True).start()

    def setDefaultFont(self, family: str):
        """设置默认（当前选中）字体。"""
        self.setCurrentFont(QFont(family))


# ============================================================
# 字体数据库自动预热
# ============================================================

def _warm_fonts():
    """在后台线程扫描字体数据库（需 QApplication 已就绪）。"""
    try:
        QFontDatabase.families()
    except Exception:
        pass


def _auto_preload_fonts():
    """模块导入即启动：等待 QApplication 完全构造后在后台预热字体数据库。

    用 QCoreApplication.startingUp() 判断就绪，避免固定延迟过早访问
    QFontDatabase 而触发 “Must construct a QGuiApplication” 警告。
    """
    import time

    def _wait_and_warm():
        while True:
            app = QApplication.instance()
            if app is not None and not QCoreApplication.startingUp():
                break
            time.sleep(0.03)
        # QCoreApplication 构造完成后再等一小段，覆盖 QGuiApplication 收尾
        time.sleep(0.05)
        _warm_fonts()

    threading.Thread(target=_wait_and_warm, daemon=True).start()


_auto_preload_fonts()