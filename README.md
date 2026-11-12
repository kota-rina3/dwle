# dwle

<img width="128" height="128" alt="dwle" src="https://github.com/user-attachments/assets/57e2e578-f4ea-4ebf-bdcb-1ceeedab82dc" />

Deepin-Wine转区工具（Deepin Wine Locale Emulator），一款区域变量模拟器。用于消除WIne软件乱码恢复正常文本。UI使用[蓝海UI](https://github.com/kota-rina3/wkfl)


<img width="1366" height="768" alt="dwle2" src="https://github.com/user-attachments/assets/cc085391-4a60-4425-894f-ef0a1293a739" />

### 编译

`sudo apt update && sudo apt install pyqt6 patchelf -y`

`pip3 install pyqt6 nuitka==4.0.8 zstandard`

`cd dwle`

`nuitka --onefile --standalone --windows-console-mode=disable --show-progress --lto=yes --jobs=4 --enable-plugins=pyqt6 --include-data-file=./dwle.ico=./dwle.ico --include-data-file=./dwle.ui=./dwle.ui ./dwle.py`
