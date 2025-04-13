import concurrent.futures
import os
import csv
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
from ttkthemes import ThemedStyle
from netmiko import SSHDetect, ConnectHandler
import concurrent.futures
import threading
from datetime import datetime
import tkinter.scrolledtext as scrolledtext
import queue   
from paramiko.ssh_exception import SSHException
from ttkthemes import ThemedStyle
import logging
from tkinter import messagebox
import time
import subprocess
from netmiko.ssh_dispatcher import CLASS_MAPPER
from server_app import ServerApp
encoding="utf-8"
class Netmiko工具:

    def __init__(self, 主窗口):
       
        self.主窗口 = 主窗口
        self.主窗口.title("AutoNetPy")
        self.主窗口.resizable(True, True)
        
        

        主窗口.geometry("1280x800")
        主窗口.minsize(1280, 800)
        # 设置窗口图标
        
        # 使用 ThemedStyle 设置主题
        self.style = ThemedStyle(self.主窗口)
        self.style.set_theme("arc")
        default_font = ('Consolas',10)
    
        # 添加日志路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 设置日志目录在脚本所在目录下
        self.log_folder = os.path.join(script_dir, "日志")
        self.检查日志()
        # 创建和布局GUI组件
        self.notebook = ttk.Notebook(self.主窗口)

        # 创建主页面
        self.frame_cmd = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_cmd, text="输入命令")

        # 设置网格布局
        self.frame_cmd.grid_columnconfigure(0, weight=1)
        self.frame_cmd.grid_columnconfigure(1, weight=1)
        self.frame_cmd.grid_columnconfigure(2, weight=1)

        # 禁用 frame_cmd 的自动调整大小
        self.frame_cmd.grid_propagate(False)

        # 设置第 0 行的固定高度
        self.frame_cmd.grid_rowconfigure(0, weight=0, minsize=10)  # 30 是固定的高度，可以根据需要调整

        # 创建 Label 控件，确保顶部对齐
        ttk.Label(
            self.frame_cmd,
            text="填写用户视图命令：",
            style="Uniform.TLabel"  
        ).grid(row=0, column=0, sticky="nw", padx=5, pady=5)  
        # Text 输入框，紧贴 Label，确保只在垂直方向扩展
        self.用户视图命令文本 = scrolledtext.ScrolledText(self.frame_cmd, height=4, width=50, wrap=tk.WORD)
        self.用户视图命令文本.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=0, pady=0)

        # row=1 向下扩展，确保文本框随着窗口增加高度而拉伸
        self.frame_cmd.grid_rowconfigure(1, weight=1)

        # 列宽设置，使文本框可以左右扩展
        self.frame_cmd.grid_columnconfigure(0, weight=1)
        self.frame_cmd.grid_columnconfigure(1, weight=1)
        self.frame_cmd.grid_columnconfigure(2, weight=1)



        # 设置默认文本
        default_text = "可输入单行或多行命令，如：\nshow run\nshow interface"
        self.用户视图命令文本.insert(tk.END, default_text)

        # 设置焦点事件
        def on_entry_click(event):
            if self.用户视图命令文本.get("1.0", "end-1c") == default_text:
                self.用户视图命令文本.delete("1.0", tk.END)
                self.用户视图命令文本.config(fg="black")  # 修改文本颜色为黑色

        # 绑定焦点事件
        self.用户视图命令文本.bind("<FocusIn>", on_entry_click)

        # 设置焦点离开事件
        def on_focus_out(event):
            if not self.用户视图命令文本.get("1.0", "end-1c"):
                self.用户视图命令文本.insert(tk.END, default_text)
                self.用户视图命令文本.config(fg="grey")  # 修改文本颜色为灰色

        # 绑定焦点离开事件
        self.用户视图命令文本.bind("<FocusOut>", on_focus_out)
        ttk.Label(
            self.frame_cmd,
            text="填写配置/系统视图命令：",
            style="Uniform.TLabel"  # 应用统一标签样式
        ).grid(row=2, column=0, pady=5, sticky=tk.W)  # 保持原有布局参数
        # 创建配置视图命令文本框
        # 设置文本框
        self.配置视图命令文本 = scrolledtext.ScrolledText(self.frame_cmd, height=4, width=50, wrap=tk.WORD)
        self.配置视图命令文本.grid(row=3, column=0, columnspan=3, pady=5, sticky="nsew")

        # 允许列扩展
        self.frame_cmd.grid_columnconfigure(0, weight=1)
        self.frame_cmd.grid_columnconfigure(1, weight=1)
        self.frame_cmd.grid_columnconfigure(2, weight=1)

        # 允许第3行扩展
        self.frame_cmd.grid_rowconfigure(3, weight=1)


        # 设置默认文本和焦点事件
        default_text_config_mode = "可输入单行或多行命令，如：\ninterface loopback10\ndescription netmiko"
        self.配置视图命令文本.insert(tk.END, default_text_config_mode)

        def on_entry_click_config_mode(event):
            if self.配置视图命令文本.get("1.0", "end-1c") == default_text_config_mode:
                self.配置视图命令文本.delete("1.0", tk.END)
                self.配置视图命令文本.config(fg="black")  # 修改文本颜色为黑色

        self.配置视图命令文本.bind("<FocusIn>", on_entry_click_config_mode)

        def on_focus_out_config_mode(event):
            if not self.配置视图命令文本.get("1.0", "end-1c"):
                self.配置视图命令文本.insert(tk.END, default_text_config_mode)
                self.配置视图命令文本.config(fg="grey")  # 修改文本颜色为灰色

        self.配置视图命令文本.bind("<FocusOut>", on_focus_out_config_mode)
        # 运行用户视图命令按钮
        ttk.Button(
            self.frame_cmd,
            text="运行用户视图命令",
            command=self.运行用户视图命令,
            style="Uniform.TButton"
        ).grid(row=4, column=0, padx=5, pady=5, sticky=tk.W+tk.E)

        # 运行配置视图命令按钮
        ttk.Button(
            self.frame_cmd,
            text="运行配置视图命令",
            command=self.运行配置视图命令,
            style="Uniform.TButton"
        ).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

        # 清空执行结果按钮
        ttk.Button(
            self.frame_cmd,
            text="清空执行结果",
            command=self.清空执行结果,
            style="Uniform.TButton"
        ).grid(row=4, column=2, padx=5, pady=5, sticky=tk.W+tk.E)

        # 打开日志目录按钮
        ttk.Button(
            self.frame_cmd,
            text="打开日志目录",
            command=self.打开日志目录,
            style="Uniform.TButton"
        ).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

# 创建 notebook 用于显示运行结果
        self.notebook_results = ttk.Notebook(self.frame_cmd)
        self.notebook_results.grid(row=0, rowspan=6, column=5, columnspan=3, pady=5, sticky=tk.N+tk.S+tk.W+tk.E)
        



        self.设备标签页字典 = {}  # 存储每台设备对应的标签页

        # 创建DEBUG开关按钮
        self.debug_button = ttk.Button(
            self.frame_cmd,
            text="开启Debug日志",
            command=self.toggle_debug_logging,
            style="Uniform.TButton"
        )
        self.debug_button.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W+tk.E)

        # 创建子标签页用于展示debug日志输出的内容
        self.debug_log_tab = ttk.Frame(self.notebook_results)

        
        self.notebook_results.add(self.debug_log_tab, text="Debug日志")
        self.debug_log_text = scrolledtext.ScrolledText(self.debug_log_tab, wrap=tk.WORD, bg="black", fg="lightgreen")
        default_debug_text="开启debug功能后会在此处显示详细日志。"
        self.debug_log_text.insert(tk.END, default_debug_text)
        self.debug_log_text.pack(expand=True, fill="both")

        # self.clear_button = tk.Button(self.frame_cmd, text="清空Debug日志", command=self.clear_debug_log_text)
        self.clear_button = ttk.Button(
            self.frame_cmd,
            text="清空Debug日志",
            command=self.clear_debug_log_text,
            style="Uniform.TButton"
        )
        self.clear_button.grid(row=5, column=2, padx=5, pady=5, sticky=tk.W+tk.E)

        # 设置Netmiko的debug日志输出到GUI中
        self.enable_debug_logging = False        
        self.debug_log_text.grid(row=0, column=0, sticky="nsew")

        # 设置Grid布局以使文本框随着窗口大小自动调整
        self.debug_log_tab.grid_rowconfigure(0, weight=1)
        self.debug_log_tab.grid_columnconfigure(0, weight=1)


        # 设置文本框的行和列权重
        self.debug_log_text.grid_rowconfigure(0, weight=1)
        self.debug_log_text.grid_columnconfigure(0, weight=1)
       
#
        #使用说明页
        self.notebook.pack(padx=10, pady=10, fill="both", expand=True)
        
        global 使用说明 
        self.frame_detail = ttk.Frame(self.notebook)
        # 添加标签页到末尾
        self.notebook.add(self.frame_detail, text="使用说明", state="hidden")
        self.使用说明文本框 = scrolledtext.ScrolledText(self.frame_detail, wrap=tk.WORD)
        self.使用说明文本框.pack(pady=5, expand=True, fill="both")
        
        使用说明 = """这是一个基于 Python 的 Netmiko 库开发的网络自动化工具，支持批量管理和运维网络设备。
1. 配置文件格式

请将设备配置信息保存为 CSV 文件，格式如下：
ip,username,password,device_type,secret
192.168.1.1,admin,admin,cisco_ios,secret
192.168.1.2,user,password,juniper_junos,secret
192.168.1.3,admin,123456,cisco_ios,secret
* 如果某些字段没有值，请留空。
* 确保文件格式正确，否则可能导致导入失败

2. 支持的设备类型

工具支持以下设备类型（但不限于）：
- cisco_ios: Cisco IOS设备
- juniper_junos: Juniper Junos设备
- arista_eos: Arista EOS设备
- huawei: Huawei设备
- hpe: HPE Comware设备
- hp_comware: H3C设备
- ruijie_os: 锐捷设备
- zte_zxros:中兴设备
- linux: 普通linux设备
* 注意：请在配置文件的 device_type 列中填写上述设备类型。如果需要使用 Telnet 连接，请在设备类型后添加 _telnet，例如：cisco_ios_telnet。

3. 功能说明

* 批量命令执行：支持用户视图命令和配置视图命令的批量执行。
* 日志记录：自动保存每台设备的执行日志，便于后续查看。
* Debug 模式：开启后可实时查看工具与设备的交互过程。

4. 常见问题

* 配置文件格式错误：请确保 CSV 文件格式正确，字段完整。
* SSH 认证超时：如果设备响应较慢，可在设置页面调整全局超时时间。

5. 注意事项

* 默认使用 SSH 连接。
* 执行配置命令前请仔细核对，操作不可撤销。"""


        self.使用说明文本框.insert(tk.END,使用说明)
        self.使用说明文本框.config(state=tk.DISABLED)


        
        # 创建导入配置页面
        self.frame_config = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_config, text="导入配置文件")

        ttk.Label(
            self.frame_config,
            text="选择配置文件 (CSV格式)：",
            style="Uniform.TLabel"  # 使用统一的标签样式
        ).grid(row=1, column=0, pady=10, sticky="e")  # 添加sticky="w"保持左对齐

        ttk.Button(
            self.frame_config,
            text="导入配置文件",
            command=self.导入配置文件,
            style="Uniform.TButton",
            width=20
        ).grid(row=1, column=1, pady=10)
        self.btn_generate_template = ttk.Button(
            self.frame_config,
            text="创建配置模板",
            command=self.打开配置模板目录,
            style="Uniform.TButton",
            width=20  # 保持与其他按钮相同的宽度
        )
        self.btn_generate_template.grid(row=2, column=1, pady=10)

        # 创建Treeview来展示导入的配置信息
        self.tree_config = ttk.Treeview(self.frame_config, show="headings")
        self.tree_config["columns"] = ("Address", "Username", "Password", "Type", "Secret")
        self.tree_config.heading("Address", text="地址", anchor=tk.CENTER)
        self.tree_config.heading("Username", text="用户名", anchor=tk.CENTER)
        self.tree_config.heading("Password", text="密码", anchor=tk.CENTER)
        self.tree_config.heading("Type", text="类型", anchor=tk.CENTER)
        self.tree_config.heading("Secret", text="Enable/Super密码", anchor=tk.CENTER)
        # 设置列的宽度和对齐方式
        self.tree_config.column("Address", width=120, anchor=tk.CENTER)
        self.tree_config.column("Username", width=100, anchor=tk.CENTER)
        self.tree_config.column("Password", width=100, anchor=tk.CENTER)
        self.tree_config.column("Type", width=80, anchor=tk.CENTER)
        self.tree_config.column("Secret", width=120, anchor=tk.CENTER)
        self.tree_config.grid(row=3, column=0, pady=5, columnspan=2, sticky="nsew")

        # 设置行和列的权重
        self.frame_config.rowconfigure(3, weight=1)  # 第三行
        self.frame_config.columnconfigure(0, weight=1)  # 第一列
        self.frame_config.columnconfigure(1, weight=1)  # 第二列
        # 创建滚动条
        self.notebook.pack(padx=10, pady=10, fill="both", expand=True)
        self.max_tab_count = 5



        # ---------------------新增测试页------------------------------
         # 初始化设备列表
        self.设备列表 = []
        self.frame_test = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_test, text="连接测试")

        # 添加按钮
        ttk.Button(
            self.frame_test, 
            text="测试连接", 
            command=self.测试连接,
            style="Uniform.TButton"
        ).pack(pady=10)

        # 创建显示连接测试结果的文本框
        self.连接测试结果文本 = scrolledtext.ScrolledText(self.frame_test, wrap=tk.WORD)
        self.连接测试结果文本.pack(pady=5, expand=True, fill="both")
        self.连接测试队列 = queue.Queue()
        self.result_queue = queue.Queue()  # 初始化result_queue



        # ---------------------新增调试页------------------------------
        self.frame_debug = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_debug, text="调试页面")

        # 创建统一样式
        style = ThemedStyle(self.frame_debug)
        style.configure("Uniform.TLabel", font=("Arial", 10))
        style.configure("Uniform.TEntry", font=("Arial", 10, "italic"), foreground="grey")
        style.configure("Uniform.TButton", font=("Arial", 10))

        pad_opts = {"padx": 5, "pady": 5, "sticky": tk.W}

        # ---------- 全局超时设置 ----------
        ttk.Label(self.frame_debug, text="全局超时（秒）:", style="Uniform.TLabel").grid(row=0, column=0, **pad_opts)

        
        timeout_options = ["5", "10", "15", "20", "30", "60"]
        self.timeout_combobox = ttk.Combobox(self.frame_debug, values=timeout_options, state="readonly", style="Uniform.TEntry")
        self.timeout_combobox.current(1)  # 默认选中 "10"
        self.timeout_combobox.grid(row=0, column=1, **pad_opts)

        ttk.Button(
            self.frame_debug,
            text="确认",
            command=self.confirm_timeout,
            style="Uniform.TButton"
        ).grid(row=0, column=2, **pad_opts)

        self.global_timeout = 10.0  # 默认全局连接超时

        # ---------- 编码选择 ----------
        ttk.Label(self.frame_debug, text="选择编码：", style="Uniform.TLabel").grid(row=1, column=0, **pad_opts)

        self.编码下拉框 = ttk.Combobox(self.frame_debug, values=["utf-8", "gbk", "gb2312", "big5", "ascii"], state="readonly", style="Uniform.TEntry")
        self.编码下拉框.current(0)
        self.编码下拉框.grid(row=1, column=1, **pad_opts)

        ttk.Button(
            self.frame_debug,
            text="确认",
            command=self.set_encoding,
            style="Uniform.TButton"
        ).grid(row=1, column=2, **pad_opts)

        # ---------- 当前编码显示 ----------
        self.label_result = ttk.Label(self.frame_debug, text="当前编码： utf-8", style="Uniform.TLabel")
        self.label_result.grid(row=2, column=0, columnspan=3, **pad_opts)






    #-----------------------工具页面------------------------------------------

        
        self.frame_info = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.frame_info, text="工具")

        # 配置网格布局权重
        self.frame_info.columnconfigure(0, weight=1)
        self.frame_info.rowconfigure(1, weight=1)  # 主要内容区可扩展

        # ==================== 标题部分 ====================
        header_frame = ttk.Frame(self.frame_info)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))




        # ==================== 主要内容区 ====================
        content_frame = ttk.Frame(self.frame_info)
        content_frame.grid(row=1, column=0, sticky="nsew")





     



        # ==================== 居中垂直按钮栏 ====================
        button_frame = ttk.Frame(self.frame_info)
        button_frame.grid(row=1, column=0, sticky="nsew", pady=20)  # 使用中间行，增加垂直间距

        # 配置网格权重使内容居中
        self.frame_info.rowconfigure(1, weight=1)  # 使中间行可扩展
        self.frame_info.columnconfigure(0, weight=1)

        # 统一按钮样式
        button_style = ttk.Style()
        button_style.configure("Vertical.TButton", 
            padding=10,
            font=("Segoe UI", 10, "bold"),
            width=25,
            anchor="center",
            relief="raised"
        )

        # 按钮交互效果
        button_style.map("Vertical.TButton",
            foreground=[('pressed', 'lightblue'), ('active', 'lightblue')],
            background=[('pressed', '#2c3e50'), ('active', '#3498db')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
        )

        # 按钮容器 - 垂直排列
        btn_container = ttk.Frame(button_frame)
        btn_container.pack(expand=True, pady=20)

        # 查看设备按钮
        btn_show_table = ttk.Button(
            btn_container,
            text="查看支持的设备类型",
            command=self.show_device_table,
            style="Vertical.TButton"
        )
        btn_show_table.pack(pady=10, ipady=5, fill=tk.X)  # 填充X方向，增加垂直间距

        # 服务工具按钮
        self.open_server_btn = ttk.Button(
            btn_container,
            text="本地服务工具",
            command=self.open_server_app,
            style="Vertical.TButton"
        )
        self.open_server_btn.pack(pady=10, ipady=5, fill=tk.X)
        # 用于保存 ServerApp 窗口的引用
        self.server_app_window = None
        self.server_app = None


        self.notebook.select(1)  # 默认选中第二个标签页


    def open_server_app(self):
        # 如果窗口已经存在，则将其提到前面
        if hasattr(self, 'server_app_window') and self.server_app_window:
            try:
                self.server_app_window.lift()
                return
            except tk.TclError:
                # 如果窗口已被关闭，则继续创建新窗口
                pass
        
        # 创建一个新的 Toplevel 窗口
        self.server_app_window = tk.Toplevel(self.主窗口)
        self.server_app_window.title("本地服务工具")
        
        # 创建 ServerApp 实例
        self.server_app = ServerApp(self.server_app_window)
        
        # 当 ServerApp 窗口关闭时清除引用
        self.server_app_window.protocol("WM_DELETE_WINDOW", self.on_server_app_close)
    
    def on_server_app_close(self):
        # 关闭 ServerApp 并清除引用
        if self.server_app:
            self.server_app.on_close()
        self.server_app_window.destroy()
        self.server_app_window = None
        self.server_app = None








    def show_device_table(self):
        # 获取 Netmiko 的设备类型数据
        device_types = []
        for device in CLASS_MAPPER.keys():
            device_info = device.split('_')
            # 确保设备信息包含至少 3 个部分，避免多余的列
            if len(device_info) == 3:
                device_types.append((device, *device_info))

        # 创建新窗口
        window = tk.Toplevel(self.主窗口)
        window.title("设备类型表格")
        window.geometry("700x400")
        
        # 创建搜索框和按钮
        search_label = tk.Label(window, text="搜索:")
        search_label.pack(padx=10, pady=5, anchor=tk.W)

        search_entry = tk.Entry(window)
        search_entry.pack(padx=10, pady=5, fill=tk.X)

        def search():
            search_query = search_entry.get().lower()

            # 清空当前显示的所有行
            for row in tree.get_children():
                tree.delete(row)

            # 插入匹配搜索内容的行
            for device in device_types:
                # 判断该行是否匹配搜索条件
                if any(search_query in str(value).lower() for value in device):
                    tree.insert("", "end", values=device)

        search_button = tk.Button(window, text="搜索", command=search)
        search_button.pack(padx=10, pady=5)

        # 创建Treeview控件并添加滚动条
        tree_frame = ttk.Frame(window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        tree = ttk.Treeview(tree_frame, columns=("设备类型", "厂商", "类别", "连接方式"), show="headings", yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        # 设置列标题
        tree.heading("设备类型", text="设备类型")
        tree.heading("厂商", text="厂商")
        tree.heading("类别", text="类别")
        tree.heading("连接方式", text="连接方式")
        
        # 设置列宽度
        tree.column("设备类型", width=200)
        tree.column("厂商", width=150)
        tree.column("类别", width=150)
        tree.column("连接方式", width=150)
        
        # 插入数据到Treeview
        for device in device_types:
            tree.insert("", "end", values=device)
        
        # 放置Treeview控件并配置滚动条
        tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)

    def set_encoding(self):
        global encoding
        encoding = self.编码下拉框.get()  # 获取下拉框的内容
        self.label_result.config(text=f"当前编码: {encoding}")
    
    # 确认用户输入的超时时间的函数
    def confirm_timeout(self):
        try:
            # 获取用户输入的超时时间
            timeout_value = float(self.timeout_combobox.get())

            # 弹出确认对话框
            confirm_result = messagebox.askyesno("确认", f"您确定要修改全局连接超时时间为 {timeout_value} 秒吗？\n这可能会影响到其他操作。")

            if confirm_result:
                # 存储全局连接超时时间
                self.global_timeout = timeout_value

                messagebox.showinfo("成功", f"全局连接超时时间已设置为 {timeout_value} 秒。")
            else:
                return

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字作为超时时间。")

  
    def clear_debug_log_text(self):
        # 清空文本框内容
        self.debug_log_text.delete(1.0, tk.END)
    # 新增一个方法，用于切换Netmiko的debug日志输出状态
    
    
    def toggle_debug_logging(self):
    # 切换调试日志的状态
        self.enable_debug_logging = not self.enable_debug_logging
        
        # 根据状态设置按钮文本，并调用相应的方法
        if self.enable_debug_logging:
            # 弹窗提示用户确认
            response = messagebox.askquestion("确认", "您确定要开启调试日志吗？请确保配置文件中只有一台设备。")
            
            # 根据用户的选择进行处理
            if response == 'yes':
                self.debug_button.config(text="关闭Debug日志")
                self.enable_netmiko_debug_logging()
            else:
                # 如果用户选择不开启调试日志，恢复按钮状态
                self.enable_debug_logging = not self.enable_debug_logging
                self.debug_button.config(text="开启Debug日志")
        else:
            # 关闭调试日志
            self.debug_button.config(text="开启Debug日志")
            self.disable_netmiko_debug_logging()


    # 新增一个方法，用于开启并处理Netmiko的debug日志输出
    def enable_netmiko_debug_logging(self):
        # 设置Netmiko的debug日志输出级别为DEBUG
        logging.getLogger("netmiko").setLevel(logging.DEBUG)
        # 将Netmiko的debug日志输出到GUI中
        logging.getLogger("paramiko").addHandler(self.DebugLogHandler(self.debug_log_text))
        # logging.getLogger("paramiko.transport").addHandler(self.DebugLogHandler(self.debug_log_text))
        # logging.getLogger("paramiko.transport.sftp").addHandler(self.DebugLogHandler(self.debug_log_text))
        logging.getLogger("netmiko").addHandler(self.DebugLogHandler(self.debug_log_text))
        # 将Netmiko的debug日志输出到终端中
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("netmiko")
        # 创建一个文件处理程序，将日志写入到指定的文件中
        file_handler = logging.FileHandler(f"{self.log_folder}/AutoNetPy_debug.log")

        # 设置文件处理程序的日志级别为DEBUG
        file_handler.setLevel(logging.DEBUG)

        # 创建一个格式化程序，定义日志的输出格式
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # 将文件处理程序添加到logger对象中
        logger.addHandler(file_handler)
        other_loggers = [
            logging.getLogger("paramiko"),

        ]

        for logger in other_loggers:
            logger.addHandler(file_handler)
    # 新增一个方法，用于关闭Netmiko的debug日志输出
    def disable_netmiko_debug_logging(self):
        # 移除Netmiko的debug日志处理器
        handlers = logging.getLogger("netmiko").handlers[:]
        for handler in handlers:
            logging.getLogger("netmiko").removeHandler(handler)

    # 新增一个内部类，用于处理Netmiko的debug日志输出
    class DebugLogHandler(logging.Handler):
        def __init__(self, text_widget):
            super().__init__()
            self.text_widget = text_widget
        def emit(self, record):
            log_entry = self.format(record)
                
            self.text_widget.insert(tk.END, log_entry + "\n")
            self.text_widget.yview(tk.END)
    #新增一个方法，打开日志目录
    def 打开日志目录(self):
     # 检查日志是否存在，如果不存在则创建
        self.检查日志()
        日志目录=self.log_folder
        if os.name == "nt":  # Windows
            subprocess.Popen(f'explorer {日志目录}')
        elif os.name == "posix":  # macOS, Linux
            subprocess.Popen(["xdg-open", 日志目录])
        else:
            tk.messagebox.showinfo("提示", "打开文件管理器失败，未知的操作系统类型")
            return

    def 清除连接测试结果(self):
        self.连接测试结果文本.delete("1.0", tk.END)

    def 显示连接测试结果(self, 设备, 结果):
        self.连接测试结果文本.insert(tk.END, f"设备：{设备['ip']} - {结果}\n")        
    def 测试连接(self):
        if self.设备列表 == []:
            tk.messagebox.showinfo("提示", "当前未导入配置文件，请选择符合模板的.csv文件作为配置文件")
            self.导入配置文件()
        self.清除连接测试结果()
        self.连接测试结果文本.insert(tk.END, "正在进行测试，请稍候...\n")

        # 创建子线程，每个线程处理一个设备
        threads = [threading.Thread(target=self.执行测试连接, args=(设备,), daemon=True) for 设备 in self.设备列表]

        # 启动所有子线程
        for thread in threads:
            thread.start()

        # 直接返回，主线程不会被阻塞
        self.连接测试结果文本.after(100, self.等待子线程完成, threads)

        return threads
        

    def 执行测试连接(self, 设备):
        结果 = self.测试设备连接(设备)
        # 将测试结果放入队列
        self.result_queue.put((设备, 结果))
    def 等待子线程完成(self, threads):
        # 等待一段时间以确保所有子线程都有足够的时间完成
        self.连接测试结果文本.after(500, self.检查子线程完成, threads)
            
    def 检查子线程完成(self, threads):
        # 检查所有子线程是否完成
        if all(not thread.is_alive() for thread in threads):
            # 所有子线程完成后，在主线程中更新 GUI
            成功设备数 = 0
            失败设备数 = 0
            失败设备列表 = []  # 新增一个列表用于存储失败设备

            while not self.result_queue.empty():
                设备, 结果 = self.result_queue.get()
                if "成功" in 结果:
                    成功设备数 += 1
                elif "失败" in 结果:
                    失败设备数 += 1
                    失败设备列表.append(设备)  # 将失败设备添加到列表中

            # 输出测试结果
            self.连接测试结果文本.insert(tk.END, f"测试完成，共连接成功 {成功设备数} 台设备，连接失败 {失败设备数} 台设备。\n")

            # 如果存在失败设备，输出失败设备列表
            if 失败设备数 > 0:
                self.连接测试结果文本.insert(tk.END, f"连接失败原因已经写入{self.log_folder}/error.log\n")
                self.连接测试结果文本.insert(tk.END, "连接失败的设备列表：\n")
                for 设备 in 失败设备列表:
                    self.连接测试结果文本.insert(tk.END, f"设备：{设备['ip']}\n")

            # 执行其他操作（如果有的话）
        else:
            # 如果还有子线程未完成，继续等待
            self.连接测试结果文本.after(500, self.检查子线程完成, threads)

    def 监听连接测试队列(self, threads):
        for thread in threads:
            thread.join()  # 等待每个子线程结束

        # 所有子线程已结束，从队列中获取结果并更新到GUI
        try:
            while True:
                设备, 结果 = self.连接测试队列.get_nowait()
                self.显示连接测试结果(设备, 结果)
        except queue.Empty:
            pass
        
    def 测试设备连接(self, 设备信息):
        try:
            self.连接测试结果文本.insert(tk.END, f"{设备信息['ip']}:正在尝试连接...\n")
            # 尝试连接
            connection = ConnectHandler(**设备信息,conn_timeout=self.global_timeout)
            connection.disconnect()
            return "连接成功"
        except SSHException as e:
            错误信息 = f"SSH 连接失败：{str(e)}"
            self.记录错误信息(设备信息, 错误信息)
            return "连接失败"  # 连接失败时返回简要信息
        except Exception as e:
            错误信息 = f"连接失败：{str(e)}"
            self.记录错误信息(设备信息, 错误信息)
            return "连接失败"  # 连接失败时返回简要信息
    def 显示连接测试结果(self, 设备信息, 结果):
        self.连接测试结果文本.insert(tk.END, f"设备：{设备信息['ip']} - {结果}\n")
    def 记录错误信息(self, 设备信息, 错误信息):
        # 获取当前日期时间
        当前时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构造错误日志文件的完整路径
        错误日志文件路径 = os.path.join(self.log_folder, "error.log")

        # 将详细错误信息、设备IP和时间写入错误日志文件
        with open(错误日志文件路径, "a",encoding="utf-8") as error_log:
            error_log.write(f"设备：{设备信息['ip']}，报错时间：{当前时间}\n")
            error_log.write(f"详细错误信息：\n{错误信息}\n")
    
    def 检查日志(self):
        # 检查日志是否存在，如果不存在则创建
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)
            print(f"创建日志文件夹：{self.log_folder}")
 
    def 清空执行结果(self):
        # 遍历字典中的标签页
        for ip, 标签页 in list(self.设备标签页字典.items()):
            # 清空文本框内容
            标签页['text_widget'].delete("1.0", tk.END)



        
    def 打开配置模板目录(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 生成配置模板
        template_content = "ip,username,password,device_type,secret\n192.168.1.1,admin,admin,cisco_ios,enable_pwd"
        template_path = os.path.join(script_dir, "配置模板.csv")
        with open(template_path, "w") as template_file:
            template_file.write(template_content)
        

        # 提示生成成功
        messagebox.showinfo("提示", f"配置模板已创建，请检查路径{script_dir}")
   
    def 运行工具(self, 用户视图命令, 配置视图命令):
        print(f"线程ID: {threading.get_ident()} ")
        # 创建进度条弹窗
        进度条提示框 = tk.Toplevel(self.主窗口)
        进度条提示框.title("任务执行中")
        
        # 设置窗口位置居中
        window_width, window_height = 300, 120
        x_pos = (进度条提示框.winfo_screenwidth() - window_width) // 2
        y_pos = (进度条提示框.winfo_screenheight() - window_height) // 2
        进度条提示框.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
        进度条提示框.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # 添加控件
        ttk.Label(进度条提示框, text="正在执行，请稍候...").pack(pady=5)
        self.任务计数器 = ttk.Label(进度条提示框, text="0/0 已完成")
        self.任务计数器.pack()
        
        # 创建进度条
        bar = ttk.Progressbar(进度条提示框, orient="horizontal", length=200, mode="determinate")
        bar.pack(pady=5)
        进度条提示框.update_idletasks()
        
        # 平滑动画相关变量
        self.当前显示进度 = 0  # 当前显示的值
        self.目标进度 = 0     # 实际应该达到的值
        self.动画进行中 = False
        
        result_queue = queue.Queue()
        total_devices = len(self.设备列表)
        completed = 0
        self.任务计数器.config(text=f"0/{total_devices} 已完成")
        
        def 更新进度动画():
            if self.当前显示进度 < self.目标进度:
                # 计算增量 - 使用缓动函数使动画更自然
                增量 = max(1, (self.目标进度 - self.当前显示进度) * 0.3)  # 0.3是平滑系数，可调整
                self.当前显示进度 = min(self.当前显示进度 + 增量, self.目标进度)
                bar["value"] = self.当前显示进度
                进度条提示框.update_idletasks()
                进度条提示框.after(30, 更新进度动画)  # 每30毫秒更新一次
            else:
                self.动画进行中 = False
        
        def 设置新进度(新值):
            self.目标进度 = 新值
            if not self.动画进行中:
                self.动画进行中 = True
                更新进度动画()
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(
                        self.执行命令, 
                        设备, 
                        用户视图命令, 
                        配置视图命令, 
                        result_queue
                    ): 设备 for 设备 in self.设备列表
                }
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        设备信息, 输出结果 = future.result()
                        self.显示运行结果(设备信息, 输出结果)
                    except Exception as e:
                        设备 = futures[future]
                        self.显示运行结果(设备, f"执行出错: {str(e)}")
                    
                    completed += 1
                    # 计算实际进度百分比
                    实际进度 = int((completed / total_devices) * 100)
                    self.任务计数器.config(text=f"{completed}/{total_devices} ")
                    设置新进度(实际进度)  # 使用平滑动画更新进度
        
            # 等待最后的动画完成
            while self.动画进行中:
                进度条提示框.update()
                time.sleep(0.03)
        
        except Exception as e:
            messagebox.showerror("错误", f"执行过程中发生错误: {str(e)}")
        finally:
            进度条提示框.destroy()
            messagebox.showinfo("任务完成", f"任务执行完毕，共完成 {completed}/{total_devices} 个设备，详细日志请查看{self.log_folder}")
    def 运行用户视图命令(self):
        
        if self.设备列表 == []:
            tk.messagebox.showinfo("提示", "当前未导入配置文件")
            self.导入配置文件()
        用户视图命令 = self.用户视图命令文本.get("1.0", tk.END).strip()
        if "可输入单行或多行命令，如：" in 用户视图命令:
            用户视图命令 =""
        配置视图命令 = ""
        if 用户视图命令 == "":
            tk.messagebox.showinfo("提示", "请在对应输入框输入命令")
            return
            
        self.清空执行结果()

        # 在主线程中监听队列
        threading.Thread(target=self.监听结果队列, args=(self.result_queue,)).start()

        # 启动执行工具的子线程
        threading.Thread(target=self.运行工具, args=(用户视图命令, 配置视图命令)).start()

    def 运行配置视图命令(self):
        
        配置视图命令 = self.配置视图命令文本.get("1.0", tk.END).strip()
        if "可输入单行或多行命令，如：" in 配置视图命令:
            配置视图命令 =""
            if 配置视图命令 == "":
                tk.messagebox.showinfo("提示", "请在对应输入框输入命令")
                return
        
        result = messagebox.askyesno("确认", f"核对命令：\n{配置视图命令}\n开始执行后无法回退，是否继续操作？")
        if result:
            if self.设备列表 == []:
                tk.messagebox.showinfo("提示", "当前未导入配置文件")
                self.导入配置文件()
            用户视图命令 = ""

            self.清空执行结果()

            # 在主线程中监听队列
            threading.Thread(target=self.监听结果队列, args=(self.result_queue,)).start()

            # 启动执行工具的子线程
            threading.Thread(target=self.运行工具, args=(用户视图命令, 配置视图命令)).start()
        else:
            return      






    def 执行工具定时器(self, 设备索引, 用户视图命令, 配置视图命令):
        if 设备索引 < len(self.设备列表):
            设备 = self.设备列表[设备索引]
            结果 = self.执行命令(设备, 用户视图命令, 配置视图命令)
            self.显示运行结果(设备, 结果)
            self.主窗口.after(100, self.执行工具定时器, 设备索引 + 1, 用户视图命令, 配置视图命令)

    def 执行工具(self, 用户视图命令, 配置视图命令):
        for 设备 in self.设备列表:
            结果 = self.执行命令(设备, 用户视图命令, 配置视图命令)
            self.显示运行结果(设备, 结果)

    def 导入配置文件(self):
        文件路径 = filedialog.askopenfilename(title="选择CSV文件", filetypes=[("./CSV 文件", "*.csv")])
        if 文件路径:
            try:
                with open(文件路径, newline='') as csv文件:
                    # 在DictReader中添加fieldnames参数
                    读者 = csv.DictReader(csv文件)
                    self.设备列表 = list(读者)
                
                # 校验CSV文件是否存在空行和参数完整性
                if self.检查CSV文件有效性(self.设备列表):
                    # 清空现有的表格数据
                    self.tree_config.delete(*self.tree_config.get_children())

                    # 读取CSV文件，并将数据显示在表格中
                    for 设备 in self.设备列表:
                        self.tree_config.insert("", "end", text=f"Device {self.设备列表.index(设备) + 1}",
                                                values=(设备['ip'], 设备['username'], 设备['password'], 设备['device_type'], 设备['secret']))

                else:
                    tk.messagebox.showerror("错误", "CSV文件格式无效，存在空行或参数不完整。请检查文件格式。")
                    self.设备列表 = []  # 清空设备列表
            except Exception as e:
                tk.messagebox.showerror("错误", f"导入配置文件时发生错误：{str(e)}")
                self.设备列表 = []  # 清空设备列表

    def 检查CSV文件有效性(self, 设备列表):
        if not 设备列表:
            return False

        required_fields = ['ip', 'username', 'password', 'device_type']
        for 设备 in 设备列表:
            if any(not 设备[field] for field in required_fields):
                return False  # 存在参数不完整的情况

        return True  # CSV文件格式有效
    def 执行命令(self, 设备信息, 用户视图命令, 配置视图命令, result_queue):
        start_time = time.time()
        输出结果 = ""  # 在函数开头初始化输出变量
    # 获取线程信息
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 精确到毫秒
        
        # 详细日志输出
        log_msg = (
            f"[{timestamp}]\n[线程ID: {thread_id}]\n[线程名: {thread_name}]\n"
            f"▶ 开始执行任务: {设备信息['ip']}\n"
            f"▶ 当前编码：{encoding}\n"
            "----------------------------------------\n"
        )
        print(log_msg)
        输出结果 += log_msg

                
        try:
            # 设备类型自动检测
            if 设备信息.get('device_type') == 'autodetect':
                连接探测器 = SSHDetect(**设备信息, conn_timeout=self.global_timeout)
                设备类型 = 连接探测器.autodetect()
                
                if not 设备类型:
                    return 设备信息, f"无法检测到设备类型，设备：{设备信息['ip']}"
                
                设备信息['device_type'] = 设备类型

            # 连接设备
            连接 = ConnectHandler(**设备信息, conn_timeout=self.global_timeout, global_delay_factor=2,encoding=encoding)
            
            # 处理用户视图命令
            if 用户视图命令:
                # 输出结果 += f"用户视图命令：\n----------------------------------------\n{用户视图命令}\n----------------------------------------\n"
                
                # H3C设备特殊处理
                if 设备信息['device_type'] == "hp_comware":
                    输出结果 = self.h3c_superpwd(设备信息, 连接, 输出结果)
                
                输出结果 += 连接.send_command_timing(用户视图命令, delay_factor=2) + "\n"
                
                end_time = time.time()
                total_time = end_time - start_time
                输出结果 += f"\n----------------------------------------\n▶{设备信息['ip']}：任务执行完成,耗时:" + str(total_time)

            # 处理配置视图命令
            if 配置视图命令:
                # 输出结果 += f"配置视图命令：\n----------------------------------------\n{配置视图命令}\n----------------------------------------\n"
                
                # H3C设备特殊处理
                if 设备信息['device_type'] == "hp_comware":
                    输出结果 = self.h3c_superpwd(设备信息, 连接, 输出结果)
                    # H3C设备需要进入system-view
                    连接.send_command_timing("system-view", delay_factor=2)
                
                输出结果 += 连接.send_config_set(配置视图命令) + "\n"
                
                # 保存配置
                save_output = 连接.save_config()
                输出结果 += save_output + "\n"
                
                end_time = time.time()
                total_time = end_time - start_time
                输出结果 += f"\n----------------------------------------\n▶{设备信息['ip']}：任务执行完成,已自动对远端设备进行保存操作,耗时:" + str(total_time)

            # 日志记录
            current_date = datetime.now().strftime("%Y%m%d_%H")
            datetime_Day = datetime.now().strftime("%Y%m%d")
            log_filename = f"{设备信息['ip']}-{current_date}.txt"
            结果_路径 = os.path.join(self.log_folder, datetime_Day)
            log_filepath = os.path.join(self.log_folder, datetime_Day, log_filename)
            
            if not os.path.exists(结果_路径):
                os.makedirs(结果_路径, exist_ok=True)   
                
            precise_date = datetime.now().strftime("%Y%m%d--%H:%M:%S")
            with open(log_filepath, "a", encoding="utf-8") as log_file:
                log_file.write(f"设备：{设备信息['ip']}\n")
                log_file.write(f"执行时间：{precise_date}\n")
                log_file.write(f"{输出结果}\n")

            # 将结果放入队列
            if result_queue is not None:
                result_queue.put((设备信息, 输出结果))
                
            return 设备信息, 输出结果

        except Exception as e:
            error_msg = f"错误：{str(e)}"
            if result_queue is not None:
                result_queue.put((设备信息, error_msg))
            return 设备信息, error_msg
        finally:
            if '连接' in locals():
                连接.disconnect()

    def h3c_superpwd(self, 设备信息, 连接, 输出结果):
        """H3C设备提权处理"""
        if 设备信息.get("secret"):
            连接.write_channel("super\n")
            time.sleep(0.5)
            连接.write_channel(f"{设备信息['secret']}\n")
            time.sleep(1)  # 等待密码生效
            
            # 读取回显判断是否成功
            output = 连接.read_channel()
            if "Password has not been set" in output:
                输出结果 += "设备没有设置super密码，请检查配置文件是否错误\n"
            elif "Permission denied" in output:
                输出结果 += "super密码错误，提权失败\n"
            else:
                输出结果 += "提权成功\n"
                # 检查是否进入特权模式
                prompt = 连接.find_prompt()
                if ">" in prompt or "]" in prompt:
                    输出结果 += f"当前提示符：{prompt}\n"
                    连接.send_command_timing("screen-length disable", delay_factor=2)
                else:
                    输出结果 += "未能进入特权模式\n"
        
        return 输出结果
       

    def 监听结果队列(self, result_queue):
        # 在主线程中监听队列，获取结果并更新GUI
        while True:
            try:
                设备信息, 输出结果 = result_queue.get_nowait()
                self.显示运行结果(设备信息, 输出结果)
            except queue.Empty:
                break



    def 显示运行结果(self, 设备, 结果):
        if 设备['ip'] not in self.设备标签页字典:
            if len(self.设备标签页字典) >= self.max_tab_count:
               
                return  # 不创建新标签页
 
            # 添加新标签页
            标签页 = ttk.Frame(self.notebook_results)
            self.notebook_results.add(标签页, text=f"{设备['ip']} 日志")
            self.设备标签页字典[设备['ip']] = {'text_widget': scrolledtext.ScrolledText(标签页, wrap=tk.WORD, bg="black", fg="lightgreen")}
            
            self.设备标签页字典[设备['ip']]['text_widget'].pack(expand=True, fill="both")


        self.设备标签页字典[设备['ip']]['text_widget'].insert(tk.END, f"设备：{设备['ip']}\n")
        self.设备标签页字典[设备['ip']]['text_widget'].insert(tk.END, 结果 + "\n\n")


def update_progress(进度条提示框, progress, bar, label):
    # 更新进度条和百分比文本
    bar["value"] = progress
    label.config(text=f"{progress}%")
    进度条提示框.update_idletasks()


     
if __name__ == "__main__":

    # 创建主窗口并启动
    主窗口 = tk.Tk()
        # 初始化Netmiko的debug日志输出
    # logging.getLogger("netmiko").setLevel(logging.DEBUG)
    # logging.getLogger("netmiko").addHandler(Netmiko工具.DebugLogHandler(scrolledtext.ScrolledText(主窗口, wrap=tk.WORD)))

    app = Netmiko工具(主窗口)
    主窗口.mainloop()
