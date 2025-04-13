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
pip install netmiko ttkthemes  pyinstaller pyftpdlib tftpy
```

### Linux
```bash
# 依赖
sudo apt-get install python3-tk  # Debian
sudo dnf install python3-tkinter # Fedora
sudo pacman -S tk                # Arch

# Python包
pip install  netmiko pyinstaller ttkthemes pyftpdlib tftpy
```

## 🚀 打包命令
### Windows
```bash
pyinstaller --noconsole --name "Netmiko_gui_" --icon="icon.ico" --add-data "server_app.py:." netmiko_gui.py
```
### Linux/macOS
```bash
pyinstaller \
--noconsole
--name "Netmiko_gui_" \
--icon="icon.ico" \
--add-data "server_app.py:." \
--hidden-import="tkinter" \
--hidden-import="scrolledtext" \
netmiko_gui.py
```

## 💡 使用说明
1. 打包后执行 `dist/` 下的可执行文件
2. 创建配置文件并导入
3. 输入操作命令
4. 查看返回结果

## 🖼️ 截图
![image](https://github.com/user-attachments/assets/7e3386a1-ab7f-4168-8dd1-028407c5a32a)



