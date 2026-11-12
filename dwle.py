#!/usr/bin/env python

from PyQt6.QtWidgets import QApplication,QMainWindow,QFileDialog,QMessageBox,QComboBox,QLineEdit,QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.uic import loadUi
import sys,os,shutil,subprocess

from Aomi.Button import AomiPushButton
from Aomi.ComboBox import AomiComboBox
from Aomi.Edit import AomiLineEdit
from Aomi.Color import Colors


def _promote(old, new):
    """把 loadUi 生成的原生控件 old 原位替换为 Aomi 控件 new（保留名称/位置/内容）"""
    parent = old.parentWidget()
    new.setObjectName(old.objectName())
    new.setParent(parent)
    new.setGeometry(old.geometry())
    if isinstance(old, QComboBox) and isinstance(new, QComboBox):
        new.addItems([old.itemText(i) for i in range(old.count())])
        new.setCurrentIndex(old.currentIndex())
    if hasattr(old, "text") and hasattr(new, "setText"):
        new.setText(old.text())
    old.hide()
    old.deleteLater()
    return new


def aomify(window):
    """批量把窗口里的原生控件替换为 Aomi 风格控件，并恢复 loadUi 生成的属性名"""
    mapping = {
        QComboBox: AomiComboBox,
        QLineEdit: AomiLineEdit,
        QPushButton: AomiPushButton,
    }
    for base, cls in mapping.items():
        for old in window.findChildren(base):
            new = _promote(old, cls())
            name = new.objectName()
            if name:
                setattr(window, name, new)

class dwle(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("./dwle.ui", self)
        aomify(self)
        self.setStyleSheet(f"#centralwidget {{ background-color: {Colors.BG_SECONDARY}; }}")
        self.setWindowTitle("Deepin-Wine转区工具")
        self.setWindowIcon(QIcon("./dwle.ico"))

        self.ChoseLang.addItems(["ja_JP.SJIS","ja_JP.UTF-8","ja_JP.EUC-JP","zh_CN.UTF-8","zh_CN.GB2312","zh_CN.GBK","zh_CN.GB18030","zh_HK.UTF-8","zh_HK.BIG5","zh_TW.EUC-TW","zh_TW.UTF-8","zh_TW.BIG5"])  #"ja_JP.SJIS",
        self.ChoseWine.addItems(["wine","deepin-wine6-stable","deepin-wine8-stable","deepin-wine10-stable","deepin-wine11-stable","deepin-wine-staging","deepin-proton9","deepin-ge-proton9","deepin-ge-proton10","deepin-ge-proton11"])
        
        self.ChoseJP.clicked.connect(self.setjp)
        self.ChoseApp.clicked.connect(self.chooseapp)
        self.ResetWine.clicked.connect(self.resetwine)
        
        self.RunApp.clicked.connect(self.exerun)
        self.BuilDstp.clicked.connect(self.desktop)
        self.AllClear.clicked.connect(self.allclear)
        self.AbtMe.clicked.connect(self.about)
        self.Exit.clicked.connect(self.close)

    def setjp(self):
        self.ChoseLang.setCurrentIndex(0)

    def resetwine(self):
        self.ChoseWine.setCurrentIndex(0)

    def chooseapp(self):
        exe , _ = QFileDialog.getOpenFileName(self, "选择Windows软件", "/","Windows程序 (*.exe *.msi)")
        self.AppDir.setText(exe)
        #print(self.ChoseLang.currentText()[0:5])
        #print(self.ChoseLang.currentText().split(".")[-1])

    def allclear(self):
        self.ChoseLang.setCurrentIndex(-1)
        self.AppDir.clear()
        self.ChoseWine.setCurrentIndex(-1)

    def exerun(self):
        exedir = os.path.dirname(self.AppDir.text())
        locate = self.ChoseLang.currentText()[0:5]
        ecding = self.ChoseLang.currentText().split(".")[-1]
        charmap_map = {
        "SJIS": "SHIFT_JIS",
        "EUC-JP": "EUC-JP",          # 根据实际情况调整，也可能是 "EUC_JP"
        "GBK": "GBK",
        "GB2312": "GB2312",
        "GB18030": "GB18030",
        "BIG5": "BIG5",
        "EUC-TW": "EUC-TW",
        "UTF-8": "UTF-8",
        }
        charmap = charmap_map.get(ecding, ecding)

        if not exedir.strip():   # 空文本
            QMessageBox.warning(self, "未导入程序", "请导入程序！")
            return
        if not shutil.which(self.ChoseWine.currentText()):   # Wine未安装
            QMessageBox.warning(self, "选择的Wine找不到", f"请先安装 {self.ChoseWine.currentText()} 软件包！")
            return

        if not os.path.exists(f"{exedir}/DWLE"):
            subprocess.Popen(["mkdir", exedir+"/DWLE"], encoding="utf-8")
        
        subprocess.Popen(["localedef", "-f", charmap, "-i", locate, os.path.join(exedir, "DWLE", self.ChoseLang.currentText())], encoding="utf-8")
            
        subprocess.Popen(["env", "LOCPATH="+exedir+"/DWLE", "LANG="+self.ChoseLang.currentText(), self.ChoseWine.currentText(), self.AppDir.text()], encoding="utf-8")
        QMessageBox.information(self, "软件已启动", f"软件的语言环境已设为{self.ChoseLang.currentText()}")
    
    def desktop(self):
        user = os.getlogin()

        appname = self.AppDir.text().split("/")[-1].split(".")[0]

        if os.path.exists(f"/home/{user}/Desktop"):
            dstp_name = f"/home/{user}/Desktop/{appname}.desktop"
        elif os.path.exists(f"/home/{user}/桌面"):
            dstp_name = f"/home/{user}/桌面/{appname}.desktop"

        dstp_text = [f'''[Desktop Entry]
Name={appname}
GenericName={appname}
Exec=env LOCPATH={os.path.dirname(self.AppDir.text())}/DWLE LANG={self.ChoseLang.currentText()} {self.ChoseWine.currentText()} {self.AppDir.text()}
StartupNotify=true
Terminal=false
Type=Application
Categories=Application;
Comment={appname}''']
        
        with open(dstp_name, 'w', encoding="utf-8") as d:
            d.write(''.join(dstp_text))
        QMessageBox.information(self, "已创建快捷方式", f'已创建{appname}的快捷方式')
    
    def about(self):
        QMessageBox.about(self, "关于", "Deepin-Wine转区工具 <br>版本：v4.1 <br>By 校医软件室 <br>项目地址：<a href='https://github.com/kota-rina3/dwle'>https://github.com/kota-rina3/dwle</a> <br>来保健室玩：<a href='https://github.com/kota-rina3/hokeshi'>https://github.com/kota-rina3/hokeshi</a>")

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = QApplication(sys.argv)
    
    window = dwle()
    window.show()
    sys.exit(app.exec())
    