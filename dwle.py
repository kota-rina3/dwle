#!/usr/bin/env python

from PyQt5.QtWidgets import QApplication,QMainWindow,QFileDialog,QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.uic import loadUi
import sys,os,subprocess

class dwle(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("./dwle.ui", self)
        self.setWindowTitle("Deepin-Wine转区工具")
        self.setWindowIcon(QIcon("./dwle.ico"))

        self.ChoseLang.addItems(["ja_JP.SJIS","ja_JP.UTF-8","ja_JP.EUC-JP","zh_CN.UTF-8","zh_CN.GB2312","zh_CN.GBK","zh_CN.GB18030","zh_HK.UTF-8","zh_HK.BIG5","zh_TW.EUC-TW","zh_TW.UTF-8","zh_TW.BIG5"])  #"ja_JP.SJIS",
        self.ChoseWine.addItems(["wine","deepin-wine6-stable","deepin-wine8-stable","deepin-wine10-stable","deepin-wine-staging","deepin-proton9","deepin-ge-proton9","deepin-ge-proton10"])
        
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
        exe , _ = QFileDialog.getOpenFileName(self, "选择exe文件", "","Windows程序 (*.exe)")
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
        if os.path.exists(f"{exedir}/DWLE"):
            pass
        else:
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
        QMessageBox.about(self, "关于", "Deepin-Wine转区工具\n版本：v3.4\nBy 校医软件室\n来保健室玩：https://github.com/kota-rina3/hokeshi")

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = QApplication(sys.argv)
    
    window = dwle()
    window.show()
    sys.exit(app.exec())
    