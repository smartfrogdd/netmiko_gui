```markdown
# Netmiko GUI 工具  
**跨平台网络设备管理工具**  


## 📦 安装指南
### 所有平台通用
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

### Windows
```batch
pip install netmiko ttkthemes pillow pyinstaller
```

### Linux
```bash
# 依赖
sudo apt-get install python3-tk  # Debian
sudo dnf install python3-tkinter # Fedora
sudo pacman -S tk                # Arch

# Python包
pip install pillow netmiko pyinstaller ttkthemes
```

## 🚀 打包命令
### Windows
```batch
.\venv\Scripts\pyinstaller.exe -noconsole --icon=icon.png --add-data "icon.png;." netmiko_gui.py
```

### Linux/macOS
```bash
venv/bin/pyinstaller --noconsole --icon=icon.png --add-data "icon.png:." --hidden-import=PIL._tkinter_finder netmiko_gui.py
```

## 💡 使用说明
1. 打包后执行 `dist/` 下的可执行文件
2. 创建配置文件并导入
3. 输入操作命令
4. 查看返回结果

## 🖼️ 截图
![image](https://github.com/user-attachments/assets/7e3386a1-ab7f-4168-8dd1-028407c5a32a)
![图片](https://github.com/user-attachments/assets/413ad3d3-61af-439f-86e5-0e165ab0d1e9)
![图片](https://github.com/user-attachments/assets/fea264ce-f2b5-4a54-a638-8348ad9001af)




