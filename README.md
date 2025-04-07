![image](https://github.com/user-attachments/assets/bc010e00-e4e6-4786-8b12-c005fd84ab24)

windows:

python -m venv venv  
pip install netmiko ttkthemes pillow pyinstaller
打包：
.\venv\Scripts\pyinstaller.exe -noconsole --icon=icon.png --add-data "icon.png;." netmiko_gui.py netmiko_gui.py
.\dist\net

linux:

 python -m venv venv
 source venv/bin/activate
 pip install 

 pip install pillow netmiko pyinstaller
 

 fedora:
 sudo dnf install python3-tkinter

 debian:
 sudo apt-get install python3-tk

 arch:
 sudo pacman -S tk


 pip install ttkthemes
 打包：
 venv/bin/pyinstaller --noconsole --icon=icon.png --add-data "icon.png:." --hidden-import=PIL._tkinter_finder netmiko_gui.py

  