#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AutoNetPy 网络自动化工具（优化界面效果版）
"""

import os
import csv
import time
import queue
import threading
import subprocess
import concurrent.futures
import logging
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
from PIL import Image, ImageTk
from ttkthemes import ThemedStyle
from netmiko import SSHDetect, ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER
from paramiko.ssh_exception import SSHException

# --------------------- 调试日志处理 ---------------------
class DebugLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        log_entry = self.format(record)
        self.text_widget.insert(tk.END, log_entry + "\n")
        self.text_widget.yview(tk.END)

# --------------------- 日志管理模块 ---------------------
class LogManager:
    def __init__(self, base_dir):
        self.log_folder = os.path.join(base_dir, "日志")
        self.check_log_directory()

    def check_log_directory(self):
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)
            print(f"创建日志文件夹：{self.log_folder}")

    def record_error(self, device_info, error_info):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_log_path = os.path.join(self.log_folder, "error.log")
        with open(error_log_path, "a", encoding="utf-8") as f:
            f.write(f"设备：{device_info['ip']}，报错时间：{current_time}\n")
            f.write(f"详细错误信息：\n{error_info}\n")

# --------------------- 主程序 GUI 模块 ---------------------
class NetmikoToolGUI:
    def __init__(self, master):
        
        self.master = master
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_manager = LogManager(self.script_dir)
        self.device_list = []                # CSV导入的设备列表
        self.result_queue = queue.Queue()    # 存放任务返回结果
        self.global_timeout = 10.0           # 全局连接超时时间
        self.encoding = "utf-8"              # 默认编码
        self.max_tab_count = 5               # 最多显示的设备日志标签数
        self.device_tabs = {}                # 设备对应的日志标签
        self.enable_debug_flag = False       # Debug日志开关

        self.setup_gui()

    # --------------------- 窗口与主题设置 ---------------------
    def setup_gui(self):
        self.master.title("AutoNetPy")
        self.master.geometry("1120x800")
        self.master.minsize(1120, 800)
        self.set_window_icon()

        # 使用 "arc" 主题（ttkthemes内置的现代主题）
        self.style = ThemedStyle(self.master)
        self.style.set_theme("arc")
        # 设置统一字体
        default_font = ('Consolas',10)
        self.master.option_add("*Font", default_font)

        # 主 Notebook
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(padx=10, pady=10, fill="both", expand=True)

        self.create_command_tab()
        self.create_config_tab()
        self.create_connection_test_tab()
        self.create_debug_tab()
        self.create_about_tab()

    def set_window_icon(self):
        icon_path = os.path.join(self.script_dir, "icon.png")
        try:
            icon_image = Image.open(icon_path)
            icon_image = icon_image.resize((64, 64))
            icon_photo = ImageTk.PhotoImage(icon_image)
            self.master.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"无法加载图标: {e}")

    # --------------------- 命令执行页面 ---------------------
    def create_command_tab(self):
        self.frame_cmd = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_cmd, text="输入命令")

        # 用户视图命令
        ttk.Label(self.frame_cmd, text="填写用户视图命令：").grid(
            row=0, column=0, sticky="nw", padx=5, pady=5
        )
        self.user_cmd_text = scrolledtext.ScrolledText(
            self.frame_cmd, height=4, width=50, wrap=tk.WORD
        )
        self.user_cmd_text.grid(
            row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5
        )
        self.default_user_cmd = "可输入单行或多行命令，如：\nshow run\nshow interface"
        self.user_cmd_text.insert(tk.END, self.default_user_cmd)
        self.user_cmd_text.bind("<FocusIn>", self.on_user_cmd_focus_in)
        self.user_cmd_text.bind("<FocusOut>", self.on_user_cmd_focus_out)

        # 配置视图命令
        ttk.Label(self.frame_cmd, text="填写配置/系统视图命令：").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.config_cmd_text = scrolledtext.ScrolledText(
            self.frame_cmd, height=4, width=50, wrap=tk.WORD
        )
        self.config_cmd_text.grid(
            row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5
        )
        self.default_config_cmd = "可输入单行或多行命令，如：\ninterface loopback10\ndescription netmiko"
        self.config_cmd_text.insert(tk.END, self.default_config_cmd)
        self.config_cmd_text.bind("<FocusIn>", self.on_config_cmd_focus_in)
        self.config_cmd_text.bind("<FocusOut>", self.on_config_cmd_focus_out)

        # 操作按钮（统一设置宽度和内边距）
        btn_opts = {"width": 20, "padding": 5}
        ttk.Button(
            self.frame_cmd, text="运行用户视图命令", command=self.run_user_command, **btn_opts
        ).grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(
            self.frame_cmd, text="运行配置视图命令", command=self.run_config_command, **btn_opts
        ).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(
            self.frame_cmd, text="清空执行结果", command=self.clear_execution_results, **btn_opts
        ).grid(row=4, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(
            self.frame_cmd, text="打开日志目录", command=self.open_log_directory, **btn_opts
        ).grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(
            self.frame_cmd, text="开启Debug日志", command=self.toggle_debug_logging, **btn_opts
        ).grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(
            self.frame_cmd, text="清空Debug日志", command=self.clear_debug_log_text, **btn_opts
        ).grid(row=5, column=2, padx=5, pady=5, sticky="ew")

        # Notebook用于显示执行结果和Debug日志
        self.notebook_results = ttk.Notebook(self.frame_cmd)
        self.notebook_results.grid(
            row=0, rowspan=6, column=5, columnspan=3, padx=5, pady=5, sticky="nsew"
        )
        self.device_tabs = {}

        self.debug_tab = ttk.Frame(self.notebook_results)
        self.notebook_results.add(self.debug_tab, text="Debug日志")
        self.debug_log_text = scrolledtext.ScrolledText(
            self.debug_tab, wrap=tk.WORD, bg="black", fg="lightgreen"
        )
        self.debug_log_text.insert(tk.END, "开启debug功能后会在此处显示详细日志。")
        self.debug_log_text.pack(expand=True, fill="both")

        # 配置网格权重
        self.frame_cmd.columnconfigure(0, weight=1)
        self.frame_cmd.columnconfigure(1, weight=1)
        self.frame_cmd.columnconfigure(2, weight=1)
        self.frame_cmd.rowconfigure(1, weight=1)
        self.frame_cmd.rowconfigure(3, weight=1)

    def on_user_cmd_focus_in(self, event):
        if self.user_cmd_text.get("1.0", "end-1c") == self.default_user_cmd:
            self.user_cmd_text.delete("1.0", tk.END)
            self.user_cmd_text.config(fg="black")

    def on_user_cmd_focus_out(self, event):
        if not self.user_cmd_text.get("1.0", "end-1c"):
            self.user_cmd_text.insert(tk.END, self.default_user_cmd)
            self.user_cmd_text.config(fg="grey")

    def on_config_cmd_focus_in(self, event):
        if self.config_cmd_text.get("1.0", "end-1c") == self.default_config_cmd:
            self.config_cmd_text.delete("1.0", tk.END)
            self.config_cmd_text.config(fg="black")

    def on_config_cmd_focus_out(self, event):
        if not self.config_cmd_text.get("1.0", "end-1c"):
            self.config_cmd_text.insert(tk.END, self.default_config_cmd)
            self.config_cmd_text.config(fg="grey")

    # --------------------- 配置文件导入页面 ---------------------
    def create_config_tab(self):
        self.frame_config = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_config, text="导入配置文件")

        ttk.Label(self.frame_config, text="选择配置文件 (CSV格式)：").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Button(
            self.frame_config, text="导入配置文件", command=self.import_config_file, width=20
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(
            self.frame_config, text="创建配置模板", command=self.open_config_template, width=20
        ).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        self.tree_config = ttk.Treeview(self.frame_config, show="headings")
        self.tree_config["columns"] = ("Address", "Username", "Password", "Type", "Secret")
        for col, text in zip(
            ("Address", "Username", "Password", "Type", "Secret"),
            ("地址", "用户名", "密码", "类型", "Enable/Super密码")
        ):
            self.tree_config.heading(col, text=text, anchor=tk.CENTER)
        self.tree_config.column("Address", width=120, anchor=tk.CENTER)
        self.tree_config.column("Username", width=100, anchor=tk.CENTER)
        self.tree_config.column("Password", width=100, anchor=tk.CENTER)
        self.tree_config.column("Type", width=80, anchor=tk.CENTER)
        self.tree_config.column("Secret", width=120, anchor=tk.CENTER)
        self.tree_config.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.frame_config.rowconfigure(3, weight=1)
        self.frame_config.columnconfigure(0, weight=1)
        self.frame_config.columnconfigure(1, weight=1)

    def import_config_file(self):
        file_path = filedialog.askopenfilename(
            title="选择CSV文件", filetypes=[("CSV 文件", "*.csv")]
        )
        if file_path:
            try:
                with open(file_path, newline="", encoding="utf-8") as csvfile:
                    reader = csv.DictReader(csvfile)
                    self.device_list = list(reader)
                if self.validate_csv(self.device_list):
                    self.tree_config.delete(*self.tree_config.get_children())
                    for device in self.device_list:
                        self.tree_config.insert(
                            "",
                            "end",
                            text=f"Device {self.device_list.index(device) + 1}",
                            values=(
                                device["ip"],
                                device["username"],
                                device["password"],
                                device["device_type"],
                                device["secret"],
                            ),
                        )
                else:
                    messagebox.showerror("错误", "CSV文件格式无效，存在空行或参数不完整。")
                    self.device_list = []
            except Exception as e:
                messagebox.showerror("错误", f"导入配置文件时发生错误：{str(e)}")
                self.device_list = []

    def validate_csv(self, device_list):
        if not device_list:
            return False
        required_fields = ["ip", "username", "password", "device_type"]
        for device in device_list:
            if any(not device[field] for field in required_fields):
                return False
        return True

    # --------------------- 连接测试页面 ---------------------
    def create_connection_test_tab(self):
        self.frame_test = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_test, text="连接测试")

        ttk.Button(
            self.frame_test, text="测试连接", command=self.test_connection, width=20
        ).pack(pady=10)
        self.test_result_text = scrolledtext.ScrolledText(self.frame_test, wrap=tk.WORD)
        self.test_result_text.pack(pady=5, expand=True, fill="both")

    def test_connection(self):
        if not self.device_list:
            messagebox.showinfo("提示", "当前未导入配置文件，请先导入符合模板的CSV文件")
            self.import_config_file()
            return
        self.test_result_text.delete("1.0", tk.END)
        self.test_result_text.insert(tk.END, "正在进行测试，请稍候...\n")
        threads = []
        for device in self.device_list:
            t = threading.Thread(target=self.execute_test_connection, args=(device,), daemon=True)
            threads.append(t)
            t.start()
        self.test_result_text.after(100, self.wait_for_test_threads, threads)

    def execute_test_connection(self, device):
        result = self.test_device_connection(device)
        self.result_queue.put((device, result))

    def wait_for_test_threads(self, threads):
        if all(not t.is_alive() for t in threads):
            success_count = 0
            fail_count = 0
            fail_devices = []
            while not self.result_queue.empty():
                device, result = self.result_queue.get()
                if "成功" in result:
                    success_count += 1
                else:
                    fail_count += 1
                    fail_devices.append(device)
            self.test_result_text.insert(tk.END, f"测试完成，共连接成功 {success_count} 台设备，连接失败 {fail_count} 台设备。\n")
            if fail_count > 0:
                self.test_result_text.insert(tk.END, f"错误信息已写入 {self.log_manager.log_folder}/error.log\n")
                self.test_result_text.insert(tk.END, "连接失败的设备列表：\n")
                for device in fail_devices:
                    self.test_result_text.insert(tk.END, f"设备：{device['ip']}\n")
        else:
            self.test_result_text.after(500, self.wait_for_test_threads, threads)

    def test_device_connection(self, device_info):
        try:
            self.test_result_text.insert(tk.END, f"{device_info['ip']}: 正在尝试连接...\n")
            connection = ConnectHandler(**device_info, conn_timeout=self.global_timeout)
            connection.disconnect()
            return "连接成功"
        except SSHException as e:
            error_info = f"SSH 连接失败：{str(e)}"
            self.log_manager.record_error(device_info, error_info)
            return "连接失败"
        except Exception as e:
            error_info = f"连接失败：{str(e)}"
            self.log_manager.record_error(device_info, error_info)
            return "连接失败"

    # --------------------- 调试页面 ---------------------
    def create_debug_tab(self):
        self.frame_debug = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_debug, text="调试页面")

        ttk.Label(self.frame_debug, text="设置全局连接超时时间（秒）：").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.timeout_entry = ttk.Entry(self.frame_debug, width=10)
        self.timeout_entry.insert(tk.END, "10.0")
        self.timeout_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(
            self.frame_debug, text="确认", command=self.confirm_timeout, width=15
        ).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.global_timeout = 10.0

        ttk.Label(self.frame_debug, text="选择编码:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        encoding_list = ["utf-8", "gbk", "gb2312", "big5", "ascii"]
        self.encoding_combo = ttk.Combobox(self.frame_debug, values=encoding_list, width=10)
        self.encoding_combo.current(0)
        self.encoding_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(
            self.frame_debug, text="设置编码", command=self.set_encoding, width=15
        ).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.encoding_label = ttk.Label(self.frame_debug, text="当前编码: utf-8")
        self.encoding_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

    def set_encoding(self):
        self.encoding = self.encoding_combo.get()
        self.encoding_label.config(text=f"当前编码: {self.encoding}")

    def confirm_timeout(self):
        try:
            timeout_value = float(self.timeout_entry.get())
            result = messagebox.askyesno(
                "确认",
                f"您确定要修改全局连接超时时间为 {timeout_value} 秒吗？\n这可能会影响到其他操作。"
            )
            if result:
                self.global_timeout = timeout_value
                messagebox.showinfo("成功", f"全局连接超时时间已设置为 {timeout_value} 秒。")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字作为超时时间。")

    def toggle_debug_logging(self):
        self.enable_debug_flag = not self.enable_debug_flag
        if self.enable_debug_flag:
            response = messagebox.askquestion("确认", "确定开启调试日志吗？请确保配置文件中仅包含一台设备。")
            if response == "yes":
                self.set_debug_button_text("关闭Debug日志")
                self.enable_netmiko_debug_logging()
            else:
                self.enable_debug_flag = not self.enable_debug_flag
                self.set_debug_button_text("开启Debug日志")
        else:
            self.set_debug_button_text("开启Debug日志")
            self.disable_netmiko_debug_logging()

    def set_debug_button_text(self, text):
        # 更新命令页中调试按钮的文字
        for widget in self.frame_cmd.grid_slaves(row=5, column=0):
            if isinstance(widget, ttk.Button):
                widget.config(text=text)

    def enable_netmiko_debug_logging(self):
        logging.getLogger("netmiko").setLevel(logging.DEBUG)
        logging.getLogger("paramiko").addHandler(DebugLogHandler(self.debug_log_text))
        logging.getLogger("netmiko").addHandler(DebugLogHandler(self.debug_log_text))
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("netmiko")
        file_handler = logging.FileHandler(f"{self.log_manager.log_folder}/AutoNetPy_debug.log")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        for log in [logging.getLogger("paramiko")]:
            log.addHandler(file_handler)

    def disable_netmiko_debug_logging(self):
        for handler in logging.getLogger("netmiko").handlers[:]:
            logging.getLogger("netmiko").removeHandler(handler)

    def clear_debug_log_text(self):
        self.debug_log_text.delete("1.0", tk.END)

    # --------------------- 关于页面 ---------------------
    def create_about_tab(self):
        self.frame_info = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.frame_info, text="关于")
        ttk.Label(self.frame_info, text="AutoNetPy", font=("Helvetica", 14, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=10
        )
        ascii_art = """
　    ∧＿ ∧
　  (   ´  ∀ ` )
　  (　　     )
　  ｜   ｜ ｜
　  (_＿  )＿)
"""
        ttk.Label(self.frame_info, text=ascii_art, font=("Consolas", 12)).grid(
            row=4, column=0, sticky="w", padx=5, pady=10
        )
        self.create_device_table(self.frame_info)

    def create_device_table(self, frame):
        btn = ttk.Button(frame, text="查看工具支持的设备类型", command=self.show_device_table, width=25)
        btn.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def show_device_table(self):
        device_types = []
        for device in CLASS_MAPPER.keys():
            parts = device.split("_")
            if len(parts) == 3:
                device_types.append((device, *parts))
        window = tk.Toplevel(self.master)
        window.title("设备类型表格")
        window.geometry("700x400")
        ttk.Label(window, text="搜索:", font=("Helvetica", 10)).pack(padx=10, pady=5, anchor="w")
        search_entry = ttk.Entry(window, width=30)
        search_entry.pack(padx=10, pady=5, fill="x")

        def search():
            query = search_entry.get().lower()
            for row in tree.get_children():
                tree.delete(row)
            for dev in device_types:
                if any(query in str(val).lower() for val in dev):
                    tree.insert("", "end", values=dev)

        ttk.Button(window, text="搜索", command=search, width=10).pack(padx=10, pady=5)
        tree_frame = ttk.Frame(window)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")
        tree = ttk.Treeview(
            tree_frame,
            columns=("设备类型", "厂商", "类别", "连接方式"),
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )
        for col, title in zip(("设备类型", "厂商", "类别", "连接方式"), ("设备类型", "厂商", "类别", "连接方式")):
            tree.heading(col, text=title)
        tree.column("设备类型", width=200)
        tree.column("厂商", width=150)
        tree.column("类别", width=150)
        tree.column("连接方式", width=150)
        for dev in device_types:
            tree.insert("", "end", values=dev)
        tree.pack(fill="both", expand=True)
        y_scroll.config(command=tree.yview)
        x_scroll.config(command=tree.xview)

    # --------------------- 命令执行及工具逻辑 ---------------------
    def run_user_command(self):
        if not self.device_list:
            messagebox.showinfo("提示", "当前未导入配置文件")
            self.import_config_file()
            return
        user_cmd = self.user_cmd_text.get("1.0", tk.END).strip()
        if "可输入单行或多行命令，如：" in user_cmd:
            user_cmd = ""
        if not user_cmd:
            messagebox.showinfo("提示", "请在用户视图命令输入框中输入命令")
            return
        config_cmd = ""
        self.clear_execution_results()
        threading.Thread(target=self.listen_result_queue, args=(self.result_queue,), daemon=True).start()
        threading.Thread(target=self.run_tool, args=(user_cmd, config_cmd), daemon=True).start()

    def run_config_command(self):
        config_cmd = self.config_cmd_text.get("1.0", tk.END).strip()
        if "可输入单行或多行命令，如：" in config_cmd:
            config_cmd = ""
        if not config_cmd:
            messagebox.showinfo("提示", "请在配置视图命令输入框中输入命令")
            return
        result = messagebox.askyesno("确认", f"核对命令：\n{config_cmd}\n执行后无法回退，是否继续？")
        if result:
            if not self.device_list:
                messagebox.showinfo("提示", "当前未导入配置文件")
                self.import_config_file()
                return
            user_cmd = ""
            self.clear_execution_results()
            threading.Thread(target=self.listen_result_queue, args=(self.result_queue,), daemon=True).start()
            threading.Thread(target=self.run_tool, args=(user_cmd, config_cmd), daemon=True).start()
        else:
            return

    def run_tool(self, user_cmd, config_cmd):
        # 显示带有进度条的弹窗
        progress_win = tk.Toplevel(self.master)
        progress_win.title("任务执行中")
        progress_win.geometry("300x100")
        ttk.Label(progress_win, text="正在执行，请稍候...").pack(pady=5)
        bar = ttk.Progressbar(progress_win, orient="horizontal", length=200, mode="determinate")
        bar.pack(pady=5)
        for i in range(101):
            bar["value"] = i
            progress_win.update_idletasks()
            time.sleep(0.01)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.execute_command, device, user_cmd, config_cmd, self.result_queue)
                for device in self.device_list
            ]
            for future in concurrent.futures.as_completed(futures):
                device_info, output = future.result()
                self.display_execution_result(device_info, output)
        progress_win.destroy()
        messagebox.showinfo("任务完成", f"任务执行完毕，详细日志请查看 {self.log_manager.log_folder}")

    def execute_command(self, device_info, user_cmd, config_cmd, result_queue):
        start_time = time.time()
        output = ""
        try:
            if device_info.get("device_type") == "autodetect":
                detector = SSHDetect(**device_info, conn_timeout=self.global_timeout)
                detected_type = detector.autodetect()
                if not detected_type:
                    return device_info, f"无法检测到设备类型，设备：{device_info['ip']}"
                device_info["device_type"] = detected_type

            connection = ConnectHandler(
                **device_info, conn_timeout=self.global_timeout, global_delay_factor=2, encoding=self.encoding
            )
            if user_cmd:
                output += f"用户视图命令：\n---------------------\n{user_cmd}\n---------------------\n"
                output += f"\n当前编码：{self.encoding}\n---------------------\n"
                if device_info["device_type"] == "hp_comware":
                    output = self.h3c_superpwd(device_info, connection, output)
                output += connection.send_command_timing(user_cmd, delay_factor=2) + "\n"
                elapsed = time.time() - start_time
                output += f"\n---------------------\n{device_info['ip']}：执行完成,耗时: {elapsed:.2f} 秒"
            if config_cmd:
                output += f"配置视图命令：\n---------------------\n{config_cmd}\n---------------------\n"
                if device_info["device_type"] == "hp_comware":
                    output = self.h3c_superpwd(device_info, connection, output)
                    connection.send_command_timing("system-view", delay_factor=2)
                output += connection.send_config_set(config_cmd) + "\n"
                save_out = connection.save_config()
                output += save_out + "\n"
                elapsed = time.time() - start_time
                output += f"\n---------------------\n{device_info['ip']}：执行完成,保存操作耗时: {elapsed:.2f} 秒"
            current_date = datetime.now().strftime("%Y%m%d_%H")
            day_str = datetime.now().strftime("%Y%m%d")
            log_filename = f"{device_info['ip']}-{current_date}.txt"
            result_dir = os.path.join(self.log_manager.log_folder, day_str)
            if not os.path.exists(result_dir):
                os.makedirs(result_dir, exist_ok=True)
            precise_time = datetime.now().strftime("%Y%m%d--%H:%M:%S")
            log_filepath = os.path.join(result_dir, log_filename)
            with open(log_filepath, "a", encoding="utf-8") as log_file:
                log_file.write(f"设备：{device_info['ip']}\n")
                log_file.write(f"执行时间：{precise_time}\n")
                log_file.write(f"{output}\n")
            if result_queue is not None:
                result_queue.put((device_info, output))
            return device_info, output
        except Exception as e:
            error_msg = f"错误：{str(e)}"
            if result_queue is not None:
                result_queue.put((device_info, error_msg))
            return device_info, error_msg
        finally:
            if "connection" in locals():
                connection.disconnect()

    def h3c_superpwd(self, device_info, connection, output):
        if device_info.get("secret"):
            connection.write_channel("super\n")
            time.sleep(0.5)
            connection.write_channel(f"{device_info['secret']}\n")
            time.sleep(1)
            chan_out = connection.read_channel()
            if "Password has not been set" in chan_out:
                output += "设备未设置super密码，请检查配置文件\n"
            elif "Permission denied" in chan_out:
                output += "super密码错误，提权失败\n"
            else:
                output += "提权成功\n"
                prompt = connection.find_prompt()
                if ">" in prompt or "]" in prompt:
                    output += f"当前提示符：{prompt}\n"
                    connection.send_command_timing("screen-length disable", delay_factor=2)
                else:
                    output += "未能进入特权模式\n"
        return output

    def listen_result_queue(self, result_queue):
        while True:
            try:
                device_info, output = result_queue.get_nowait()
                self.display_execution_result(device_info, output)
            except queue.Empty:
                break

    def display_execution_result(self, device_info, output):
        ip = device_info["ip"]
        if ip not in self.device_tabs:
            if len(self.device_tabs) >= self.max_tab_count:
                return
            tab = ttk.Frame(self.notebook_results)
            self.notebook_results.add(tab, text=f"{ip} 日志")
            text_widget = scrolledtext.ScrolledText(tab, wrap=tk.WORD, bg="black", fg="lightgreen")
            text_widget.pack(expand=True, fill="both")
            self.device_tabs[ip] = {"text_widget": text_widget}
        widget = self.device_tabs[ip]["text_widget"]
        widget.insert(tk.END, f"设备：{ip}\n")
        widget.insert(tk.END, output + "\n\n")

    def clear_execution_results(self):
        for ip, tab in list(self.device_tabs.items()):
            tab["text_widget"].delete("1.0", tk.END)

    def open_config_template(self):
        template_content = "ip,username,password,device_type,secret\n192.168.1.1,admin,admin,cisco_ios,enable_pwd"
        template_path = os.path.join(self.script_dir, "配置模板.csv")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)
        messagebox.showinfo("提示", f"配置模板已创建，请检查路径 {self.script_dir}")

    def open_log_directory(self):
        self.log_manager.check_log_directory()
        log_dir = self.log_manager.log_folder
        if os.name == "nt":
            subprocess.Popen(f'explorer "{log_dir}"')
        elif os.name == "posix":
            subprocess.Popen(["xdg-open", log_dir])
        else:
            messagebox.showinfo("提示", "无法打开文件管理器，未知的操作系统类型")

# --------------------- 主程序入口 ---------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = NetmikoToolGUI(root)
    root.mainloop()
