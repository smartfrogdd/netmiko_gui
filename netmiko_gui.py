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
import sys
import tkinter.scrolledtext as scrolledtext
import queue   
from paramiko.ssh_exception import SSHException
from ttkthemes import ThemedStyle
import logging
from tkinter import messagebox
import time
from PIL import Image, ImageTk
import subprocess


class Netmiko工具:

    def __init__(self, 主窗口):
       
        self.主窗口 = 主窗口
        self.主窗口.title("AutoNetPy")
        self.主窗口.resizable(True, True)
        # 使用 Pillow 加载 PNG 图像
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icon.png")
        icon_image = Image.open(icon_path)
        icon_image = icon_image.resize((64, 64))  # 调整图像大小
        icon_photo = ImageTk.PhotoImage(icon_image)
        主窗口.geometry("800x400")
        主窗口.minsize(800, 400)
        # 设置窗口图标
        self.主窗口.iconphoto(True, icon_photo)
        # 使用 ThemedStyle 设置主题
        self.style = ThemedStyle(self.主窗口)
        self.style.set_theme("plastik")
    
        # 添加日志路径
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

        tk.Label(self.frame_cmd, text="填写用户视图命令：").grid(row=0, column=0, pady=5, sticky=tk.W)
        # 创建用户视图命令文本框
        self.用户视图命令文本 = scrolledtext.ScrolledText(self.frame_cmd, height=4, width=50, wrap=tk.WORD)
        self.用户视图命令文本.grid(row=1, column=0, columnspan=3, pady=5, sticky="nsew")

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
        tk.Label(self.frame_cmd, text="填写配置/系统视图命令：").grid(row=2, column=0, pady=5, sticky=tk.W)
        # 创建配置视图命令文本框
        self.配置视图命令文本 = scrolledtext.ScrolledText(self.frame_cmd, height=4, width=50, wrap=tk.WORD)
        self.配置视图命令文本.grid(row=3, column=0, columnspan=3, pady=5, sticky="nsew")

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
        tk.Button(self.frame_cmd, text="运行用户视图命令", command=self.运行用户视图命令).grid(row=4, column=0, padx=5, pady=5, sticky=tk.W+tk.E)
        tk.Button(self.frame_cmd, text="运行配置视图命令", command=self.运行配置视图命令).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        tk.Button(self.frame_cmd, text="清空执行结果", command=self.清空执行结果).grid(row=4, column=2, padx=5, pady=5, sticky=tk.W+tk.E)
        tk.Button(self.frame_cmd, text="打开日志目录", command=self.打开日志目录).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

        # 创建 notebook 用于显示运行结果
        self.notebook_results = ttk.Notebook(self.frame_cmd)
        self.notebook_results.grid(row=0,rowspan=6, column=5, columnspan=3, pady=5, sticky=tk.W+tk.E)


        self.设备标签页字典 = {}  # 存储每台设备对应的标签页
#
        #使用说明页
        self.notebook.pack(padx=10, pady=10, fill="both", expand=True)
        
        global 使用说明 
        self.frame_detail = ttk.Frame(self.notebook)
        # 添加标签页到末尾
        self.notebook.add(self.frame_detail, text="使用说明", state="hidden")
        self.使用说明文本框 = scrolledtext.ScrolledText(self.frame_detail, wrap=tk.WORD)
        self.使用说明文本框.pack(pady=5, expand=True, fill="both")
        
        使用说明 = """这是一个基于python的netmiko库制作的网络自动化工具，可以实现网络设备批量自动化运维的基本功能。
使用说明：
1.请将设备配置信息保存为CSV文件，格式如下：
ip,username,password,device_type,secret
192.168.1.1,admin,admin,cisco_ios,,secret
192.168.1.2,user,password,juniper_junos,secret\n192.168.1.3,admin,123456,cisco,secret
(如有关键字未设置请在表格中留空)
2.在导入配置文件时，出现错误提示大概率是配置文件格式问题。
3.可用的设备类型包括：
- cisco_ios: Cisco IOS设备
- cisco_xe: Cisco IOS XE设备
- cisco_xr: Cisco IOS XR设备
- juniper_junos: Juniper Junos设备
- arista_eos: Arista EOS设备
- huawei: Huawei设备
- hpe: HPE Comware设备
- vyos: VyOS设备
- hp_comware: H3C设备
- linux: 普通linux设备
[请在配置文件的device_type 列中选择上述设备类型之一填写。]
4.在填写配置文件时，请注意区分设备类型，确保与实际设备一致。
5.默认使用SSH连接。如需使用Telnet连接，在设备类型后增加"_telnet"，如：cisco_ios_telnet。
6.使用debug功能可以实时看到工具执行命令时后台与所有设备的所有交互过程
7.遇到ssh认证时间较长的设备，可以在设置页调整整体超时时间，否则可能会因为ssh认证超时导致连接失败"""
        self.使用说明文本框.insert(tk.END,使用说明)
        self.使用说明文本框.config(state=tk.DISABLED)


        
        # 创建导入配置页面
        self.frame_config = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_config, text="导入配置文件")

        tk.Label(self.frame_config, text="选择配置文件 (CSV格式)：").grid(row=1, column=0, pady=10)

        tk.Button(self.frame_config, text="导入配置文件", command=self.导入配置文件).grid(row=1, column=1, pady=10)
        self.btn_generate_template = tk.Button(self.frame_config, text="创建配置模板", command=self.打开配置模板目录)
        self.btn_generate_template.grid(row=2, column=1, pady=10)

        # 创建Treeview来展示导入的配置信息
        self.tree_config = ttk.Treeview(self.frame_config, show="headings")
        self.tree_config["columns"] = ("Address", "Username", "Password", "Type", "Secret")
        self.tree_config.heading("Address", text="地址", anchor=tk.CENTER)
        self.tree_config.heading("Username", text="用户名", anchor=tk.CENTER)
        self.tree_config.heading("Password", text="密码", anchor=tk.CENTER)
        self.tree_config.heading("Type", text="类型", anchor=tk.CENTER)
        self.tree_config.heading("Secret", text="Enable密码", anchor=tk.CENTER)
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
       

        



        self.notebook.pack(padx=10, pady=10, fill="both", expand=True)
        self.max_tab_count = 5
        # 初始化设备列表
        self.设备列表 = []
        # 新增标签页
        self.frame_test = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_test, text="连接测试")

        # 添加按钮
        tk.Button(self.frame_test, text="测试连接", command=self.测试连接).pack(pady=10)

        # 创建显示连接测试结果的文本框
        self.连接测试结果文本 = scrolledtext.ScrolledText(self.frame_test, wrap=tk.WORD)
        self.连接测试结果文本.pack(pady=5, expand=True, fill="both")
        self.连接测试队列 = queue.Queue()
        self.result_queue = queue.Queue()  # 初始化result_queue


        # 创建开关按钮
        self.debug_button = tk.Button(self.frame_cmd, text="开启Debug日志", command=self.toggle_debug_logging)
        self.debug_button.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W+tk.E)

        # 创建子标签页用于展示debug日志输出的内容
        self.debug_log_tab = ttk.Frame(self.notebook_results)

        
        self.notebook_results.add(self.debug_log_tab, text="Debug日志")
        self.debug_log_text = scrolledtext.ScrolledText(self.debug_log_tab, wrap=tk.WORD)
        self.debug_log_text.pack(expand=True, fill="both")
        self.clear_button = tk.Button(self.frame_cmd, text="清空Debug日志", command=self.clear_debug_log_text)
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
       
       
        # 创建调试页面的新标签页
        self.frame_debug = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_debug, text="调试页面")

        # 添加用于设置全局连接超时时间的标签和输入框
        tk.Label(self.frame_debug, text="设置全局连接超时时间（秒）：").grid(row=0, column=0, pady=5, sticky=tk.W)

        # 使用 ttk.Entry，并设置默认值为10秒
        self.timeout_entry = ttk.Entry(self.frame_debug)
        self.timeout_entry.insert(tk.END, "10.0")  # 设置默认值为10秒
        self.timeout_entry.grid(row=0, column=1, pady=5)

        # 使用 Style 对象配置样式，设置为斜体灰色
        style = ThemedStyle(self.frame_debug)
        style.configure("TEntry.Default.TEntry", font=("Arial", 10, "italic"), foreground="grey")

        # 添加确认用户输入超时时间的按钮
        tk.Button(self.frame_debug, text="确认超时时间", command=self.confirm_timeout).grid(row=1, column=0, columnspan=1, pady=1)
        self.global_timeout = 10.0  # 默认全局连接超时时间为10秒



       # 添加关于页面的内容
        self.frame_info = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_info, text="关于")

        
        tk.Label(self.frame_info, text="Netmiko工具 v1.0").grid(row=0, column=0, pady=10, sticky=tk.W)


        # ASCII图片
        ascii_art = """
　    ∧＿ ∧
　  (   ´  ∀ ` )
　  (　　     )
　  ｜   ｜ ｜
　  (_＿  )＿)


"""

        tk.Label(self.frame_info, text=ascii_art).grid(row=4, column=0, pady=10, sticky=tk.W)

        self.notebook.select(1) 
        self.ftp_server_lock = threading.Lock()
    
    
    
    # 确认用户输入的超时时间的函数
    def confirm_timeout(self):
        try:
            # 获取用户输入的超时时间
            timeout_value = float(self.timeout_entry.get())

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
        for 标签页 in self.设备标签页字典.values():
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
        # def update_label():
        #     current_text = label.cget("text")
        #     if current_text.endswith("...."):
        #         new_text = "命令正在并发执行中，请稍等"
        #     else:
        #         new_text = current_text + "."
        #     label.config(text=new_text)
        #     new_window.after(500, update_label)  # 500毫秒后再次更新

        # new_window = tk.Toplevel()
        # new_window.title("提示")
        # new_window.geometry("400x200")

        # label = tk.Label(new_window, text="命令执行中，请稍等")
        # label.pack(padx=20, pady=20)

        # update_label()
        进度条提示框 = tk.Tk()
        进度条提示框.title("正在并发执行任务")
        进度条提示框.geometry("300x100")

        label = tk.Label(进度条提示框, text="0%", font=("Helvetica", 12))
        label.pack(pady=10)

        bar = ttk.Progressbar(进度条提示框, orient="horizontal", length=200, mode="determinate")
        bar.pack(pady=10)

        # 计算每个更新所需的时间
        total_time = 1  # 秒
        update_interval = total_time / 100  # 每个百分比的时间
        start_time = time.time()

        # 模拟进度更新
        for i in range(100):
            elapsed_time = time.time() - start_time
            remaining_time = max(0, total_time - elapsed_time)
            update_progress(进度条提示框, i, bar, label)
            进度条提示框.after(int(update_interval * 1000))  # 将秒转换为毫秒
        
        # 使用队列来保存每个子线程的结果
        result_queue = queue.Queue()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 使用 executor.submit() 提交每个任务
            futures = [executor.submit(self.执行命令, 设备, 用户视图命令, 配置视图命令, result_queue) for 设备 in self.设备列表]

            # 使用 as_completed 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                设备信息, 输出结果 = future.result()
                self.显示运行结果(设备信息, 输出结果)
        # new_window.destroy()
        进度条提示框.destroy() 
        messagebox.showinfo("任务完成", f"所有任务已完成，工具最多支持5个标签展示执行回显.\n更多设备详情请查看路径{self.log_folder}")


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
        try:
            if 设备信息.get('device_type') == 'autodetect':
                连接探测器 = SSHDetect(**设备信息,conn_timeout=self.global_timeout)
                设备类型 = 连接探测器.autodetect()

                if not 设备类型:
                    return 设备信息, f"无法检测到设备类型，设备：{设备信息['ip']}"

                设备信息['device_type'] = 设备类型

            连接 = ConnectHandler(**设备信息,conn_timeout=self.global_timeout)
           
            输出结果 = ""
            
            if 用户视图命令:
                输出结果 += f"用户视图命令：{用户视图命令}\n"
                     
                输出结果 += 连接.send_command(用户视图命令) + "\n"

 
                # 输出结果 += 连接.send_command(用户视图命令, expect_string='Y/N'and"<"and">") + "\n"
           



                end_time = time.time()
                total_time = end_time - start_time
                输出结果 += f"\n{设备信息['ip']}：执行完成,耗时:"+ str(total_time)
                

            if 配置视图命令:
                输出结果 += f"配置视图命令：{配置视图命令}\n"
                输出结果 += 连接.send_config_set(配置视图命令) + "\n"
                save_output = 连接.save_config()
                end_time = time.time()
                total_time = end_time - start_time
                输出结果 += f"{设备信息['ip']}：执行完成,已自动对远端设备进行保存操作,耗时:"+ str(total_time)
            
          
            
            
            
            # 获取当前日期作为文件名的一部分
            # 将当前日期时间格式化为"年月日_时"
            current_date = datetime.now().strftime("%Y%m%d_%H")
            datetime_Day = datetime.now().strftime("%Y%m%d")
            
            
            # 构造日志文件名，格式为 设备ip-日期.txt
            log_filename = f"{设备信息['ip']}-{current_date}.txt"
            # 构造结果存放目录，格式为当天日期
            结果_路径 = os.path.join(self.log_folder, datetime_Day)
            # 构造日志文件的完整路径
            log_filepath = os.path.join(self.log_folder, datetime_Day,log_filename)
            
            
            
            
            
            if not os.path.exists(结果_路径):
                os.makedirs(结果_路径, exist_ok=True)   
                
            precise_date = datetime.now().strftime("%Y%m%d--%H:%M:%S")
            # 保存结果到日志文件
            with open(log_filepath, "a",encoding="utf-8") as log_file:
                log_file.write(f"设备：{设备信息['ip']}\n")
                log_file.write(f"执行时间：{precise_date}\n")
                log_file.write(f"{输出结果}\n")

            return 设备信息, 输出结果
            # 将结果放入队列
            result_queue.put((设备信息, 输出结果))            
        except Exception as 错误:
            return 设备信息, f"错误：{错误}"

       

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
            self.设备标签页字典[设备['ip']] = {'text_widget': scrolledtext.ScrolledText(标签页, wrap=tk.WORD)}
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