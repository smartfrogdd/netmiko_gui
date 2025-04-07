![image](https://github.com/user-attachments/assets/bc010e00-e4e6-4786-8b12-c005fd84ab24)

**windows:**

python -m venv venv  
pip install netmiko ttkthemes pillow pyinstaller
打包：
.\venv\Scripts\pyinstaller.exe -noconsole --icon=icon.png --add-data "icon.png;." netmiko_gui.py netmiko_gui.py
.\dist\net

**linux:**
<img width="1150" alt="6de258849c99ea91fca27154dce91e3" src="https://github.com/user-attachments/assets/e7120dec-37ff-4a76-9656-f6a8a01ed136" />

 python -m venv venv
 source venv/bin/activate
 pip install 

 pip install pillow netmiko pyinstaller
 

** fedora:**
 sudo dnf install python3-tkinter

** debian:**
 sudo apt-get install python3-tk

** arch:**
 sudo pacman -S tk


 pip install ttkthemes
 打包：
 venv/bin/pyinstaller --noconsole --icon=icon.png --add-data "icon.png:." --hidden-import=PIL._tkinter_finder netmiko_gui.py

  
