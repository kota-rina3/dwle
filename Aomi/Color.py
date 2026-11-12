#!/usr/bin/env python
# Copyright 2023-2026 RicerVM 

"""
Aomi UI for PyQt6
===================
参考 DTK (deepin Tool Kit) 设计规范，为 PyQt6 应用提供 deepin 风格控件。

核心控件:
- AomiTheme         — 主题管理器（亮色/暗色切换 + QSS 加载）
- AomiWindow        — 无边框圆角窗口 + 阴影
- AomiTitleBar      — 自定义标题栏（最小化/最大化/关闭）
- AomiDialog        — 圆角对话框
- AomiCard          — 卡片容器
- AomiButton        — 强调色按钮
- AomiLineEdit      — 圆角输入框
- AomiSwitch        — 开关切换
- AomiToast         — 轻量级通知提示
- AomiAvatar        — 圆形头像
- AomiProgressBar   — 进度条
- AomiSlider        — 滑块

用法:
    from deepin_ui import AomiTheme, AomiWindow

    app = QApplication(sys.argv)
    theme = AomiTheme.load(app)  # 自动加载 QSS

    window = AomiWindow()
    window.setWindowTitle("My App")
    window.resize(900, 640)
    window.show()

    sys.exit(app.exec())
"""

import os
from enum import Enum
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QGraphicsDropShadowEffect

class Colors:
    """Deepin 设计规范颜色令牌"""
    # 亮色主题
    BG_PRIMARY          = "#FFFFFF"
    BG_SECONDARY        = "#F8F8F8"
    BG_TERTIARY         = "#F0F0F0"
    BG_HOVER            = "#E8E8E8"
    BG_PRESSED          = "#DADADA"
    BG_SELECTED         = "#0081FF"
    FG_PRIMARY          = "#1A1A1A"
    FG_SECONDARY        = "#555555"
    FG_DISABLED         = "#BBBBBB"
    TEXT                = "#4D4D4D"
    ACCENT              = "#0081FF"
    ACCENT_HOVER        = "#2495FF"
    ACCENT_PRESSED      = "#006DD4"
    BORDER              = "#E0E0E0"
    BORDER_FOCUS        = "#0081FF"
    BUTTON_BORDER       = "#DBDBDB"
    IDLE                = "#E5E5E5"
    SHADOW              = "rgba(0, 0, 0, 0.08)"
    WARNING             = "#FF6D00"
    DANGER              = "#FF3B30"
    SUCCESS             = "#34C759"
    TITLEBAR_BG         = "#FFFFFF"
    SCROLLBAR_BG        = "#808080"
    SCROLLBAR_HOVER     = "#4C4C4C"

    # 暗色主题
    @staticmethod
    def dark():
        return {
            "BG_PRIMARY":     "#1E1E1E",
            "BG_SECONDARY":   "#252525",
            "BG_TERTIARY":    "#2D2D2D",
            "BG_HOVER":       "#353535",
            "BG_PRESSED":     "#404040",
            "BG_SELECTED":    "#0081FF",
            "FG_PRIMARY":     "#E0E0E0",
            "FG_SECONDARY":   "#A0A0A0",
            "FG_DISABLED":    "#555555",
            "ACCENT":         "#0081FF",
            "ACCENT_HOVER":   "#1A8FFF",
            "ACCENT_PRESSED": "#006DD4",
            "BORDER":         "#3A3A3A",
            "BORDER_FOCUS":   "#0081FF",
            "SHADOW":         "rgba(0, 0, 0, 0.08)",
            "WARNING":        "#FF6D00",
            "DANGER":         "#FF3B30",
            "SUCCESS":        "#34C759",
            "TITLEBAR_BG":    "#1E1E1E",
        }


class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"


# ============================================================
# 主题管理器
# ============================================================

class AomiTheme(QObject):
    """
    主题管理器 — 加载 QSS 样式并支持亮色/暗色切换。

    ```python
    theme = AomiTheme.load(app, Theme.LIGHT)
    theme.toggle()  # 切换到暗色
    ```
    """
    _instance: "AomiTheme | None" = None
    themeChanged = pyqtSignal(str)  # "light" / "dark"

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self._app = app
        self._theme = Theme.LIGHT
        self._qss_path: str = ""

    @classmethod
    def load(cls, app: QApplication, theme: Theme = Theme.LIGHT,
             qss_path: str = "") -> "AomiTheme":
        """加载主题并应用 QSS。qss_path 为空时在同目录查找 aomi.qss。"""
        if cls._instance is not None:
            return cls._instance
        instance = cls(app)
        cls._instance = instance

        if not qss_path:
            # 尝试从模块所在目录查找
            module_dir = Path(__file__).parent
            candidate = module_dir / "aomi.qss"
            if candidate.exists():
                qss_path = str(candidate)

        instance._qss_path = qss_path
        instance.apply_theme(theme)
        return instance

    @classmethod
    def instance(cls) -> "AomiTheme | None":
        return cls._instance

    @property
    def current_theme(self) -> Theme:
        return self._theme

    def apply_theme(self, theme: Theme):
        self._theme = theme
        if self._qss_path and os.path.exists(self._qss_path):
            with open(self._qss_path, "r", encoding="utf-8") as f:
                qss = f.read()

            if theme == Theme.DARK:
                qss = self._apply_dark_overrides(qss)

            self._app.setStyleSheet(qss)

        self.themeChanged.emit(theme.value)

    def toggle(self):
        next_theme = Theme.DARK if self._theme == Theme.LIGHT else Theme.LIGHT
        self.apply_theme(next_theme)

    def set_light(self):
        self.apply_theme(Theme.LIGHT)

    def set_dark(self):
        self.apply_theme(Theme.DARK)

    def _apply_dark_overrides(self, qss: str) -> str:
        """将 QSS 中的亮色颜色替换为暗色值。"""
        replacements = [
            ("#FFFFFF",   "#1E1E1E"),
            ("#F8F8F8",   "#252525"),
            ("#F0F0F0",   "#2D2D2D"),
            ("#E8E8E8",   "#353535"),
            ("#DADADA",   "#404040"),
            ("#1A1A1A",   "#E0E0E0"),
            ("#555555",   "#A0A0A0"),
            ("#888888",   "#808080"),
            ("#BBBBBB",   "#555555"),
            ("#CCCCCC",   "#505050"),
            ("#DDDDDD",   "#454545"),
            ("#E0E0E0",   "#3A3A3A"),
            ("#F5F5F5",   "#2A2A2A"),
            ("rgba(0, 129, 255, 0.08)",  "rgba(0, 129, 255, 0.15)"),
            ("rgba(0, 129, 255, 0.12)",  "rgba(0, 129, 255, 0.20)"),
            ("rgba(0, 129, 255, 0.16)",  "rgba(0, 129, 255, 0.25)"),
        ]
        for light, dark in replacements:
            qss = qss.replace(light, dark)
        return qss


# ============================================================
# 阴影效果工厂
# ============================================================

def make_shadow(blur_radius=60, offset=(0, 10), color=QColor(0, 0, 0, 50)):
    """创建 QGraphicsDropShadowEffect 阴影"""
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur_radius)
    effect.setOffset(*offset)
    effect.setColor(color)
    return effect

