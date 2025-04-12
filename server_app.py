import os
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from datetime import datetime
from tftpy import TftpServer
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("服务工具")
        self.root.geometry("800x750")
        self.root.minsize(800, 750)
        self.root.configure(bg="#f8f8f8")

        self.tftp_thread = None
        self.ftp_thread = None
        self.ftp_server = None
        self.tftp_started = False
        self.ftp_started = False
        self.log_lock = threading.Lock()
        
        # 默认目录设置为当前工作目录
        self.tftp_dir = os.getcwd()
        self.ftp_dir = os.getcwd()

        self.build_ui()

    def build_ui(self):
        
        # 主框架
        main_frame = tk.Frame(self.root, bg="#f8f8f8")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- TFTP 区域 ---
        tftp_frame = tk.LabelFrame(main_frame, text="TFTP 设置", padx=10, pady=10, bg="#f8f8f8")
        tftp_frame.pack(fill="x", pady=5)

        # 第一行：端口设置
        port_row = tk.Frame(tftp_frame, bg="#f8f8f8")
        port_row.pack(anchor="w", pady=5)
        
        tk.Label(port_row, text="端口:", bg="#f8f8f8").pack(side="left")
        self.tftp_port_entry = tk.Entry(port_row, width=8, validate="key")
        self.tftp_port_entry['validatecommand'] = (self.tftp_port_entry.register(self.validate_port), '%P')
        self.tftp_port_entry.insert(0, "1069")
        self.tftp_port_entry.pack(side="left", padx=5)

        # 第二行：目录选择和状态
        dir_row = tk.Frame(tftp_frame, bg="#f8f8f8")
        dir_row.pack(anchor="w", pady=5)
        
        tk.Label(dir_row, text="目录:", bg="#f8f8f8").pack(side="left")
        self.tftp_dir_label = tk.Label(dir_row, text=self.tftp_dir, bg="#f8f8f8", width=40, anchor="w", relief="sunken", padx=5)
        self.tftp_dir_label.pack(side="left", padx=5)
        tk.Button(dir_row, text="浏览...", command=self.select_tftp_dir).pack(side="left")

        # 第三行：控制按钮
        ctrl_row = tk.Frame(tftp_frame, bg="#f8f8f8")
        ctrl_row.pack(anchor="w", pady=5)
        
        self.tftp_btn = tk.Button(ctrl_row, text="启动 TFTP 服务", command=self.toggle_tftp, width=15)
        self.tftp_btn.pack(side="left", padx=5)
        
        
        

        # --- FTP 区域 ---
        ftp_frame = tk.LabelFrame(main_frame, text="FTP 设置", padx=10, pady=10, bg="#f8f8f8")
        ftp_frame.pack(fill="x", pady=5)

        # 第一行：端口和认证
        auth_row = tk.Frame(ftp_frame, bg="#f8f8f8")
        auth_row.pack(anchor="w", pady=5)
        
        tk.Label(auth_row, text="端口:", bg="#f8f8f8").pack(side="left")
        self.ftp_port_entry = tk.Entry(auth_row, width=8, validate="key")
        self.ftp_port_entry['validatecommand'] = (self.ftp_port_entry.register(self.validate_port), '%P')
        self.ftp_port_entry.insert(0, "2121")
        self.ftp_port_entry.pack(side="left", padx=5)

        tk.Label(auth_row, text="用户名:", bg="#f8f8f8").pack(side="left", padx=(10,0))
        self.username_entry = tk.Entry(auth_row, width=10)
        self.username_entry.insert(0, "ftp")
        self.username_entry.pack(side="left", padx=5)

        tk.Label(auth_row, text="密码:", bg="#f8f8f8").pack(side="left", padx=(10,0))
        self.password_entry = tk.Entry(auth_row, width=10, show="*")
        self.password_entry.insert(0, "ftp")
        self.password_entry.pack(side="left", padx=5)

        # 第二行：目录选择
        ftp_dir_row = tk.Frame(ftp_frame, bg="#f8f8f8")
        ftp_dir_row.pack(anchor="w", pady=5)
        
        tk.Label(ftp_dir_row, text="目录:", bg="#f8f8f8").pack(side="left")
        self.ftp_dir_label = tk.Label(ftp_dir_row, text=self.ftp_dir, bg="#f8f8f8", width=40, anchor="w", relief="sunken", padx=5)
        self.ftp_dir_label.pack(side="left", padx=5)
        tk.Button(ftp_dir_row, text="浏览...", command=self.select_ftp_dir).pack(side="left")

        # 第三行：控制按钮
        ftp_ctrl_row = tk.Frame(ftp_frame, bg="#f8f8f8")
        ftp_ctrl_row.pack(anchor="w", pady=5)
        
        self.ftp_btn = tk.Button(ftp_ctrl_row, text="启动 FTP 服务", command=self.toggle_ftp, width=15)
        self.ftp_btn.pack(side="left", padx=5)
        
        self.ftp_status_btn = tk.Label(ftp_ctrl_row, text="🔴 未运行", bg="red", fg="white", width=12, relief="sunken")
        self.ftp_status_btn.pack(side="left", padx=5)

        # --- 日志窗口 ---
        log_frame = tk.LabelFrame(main_frame, text="日志输出", padx=10, pady=5, bg="#f8f8f8")
        log_frame.pack(fill="both", expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=10, 
            state="disabled", 
            bg="#fdfdfd",
            wrap=tk.WORD
        )
        self.log_text.pack(fill="both", expand=True)

        # 底部状态栏
        status_bar = tk.Frame(self.root, bg="#e0e0e0", height=20)
        status_bar.pack(fill="x", side="bottom")
        self.status_label = tk.Label(status_bar, text="就绪", bg="#e0e0e0", anchor="w")
        self.status_label.pack(fill="x", padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def validate_port(self, port_str):
        if not port_str:
            return True
        if port_str.isdigit():
            port = int(port_str)
            return 1 <= port <= 65535
        return False

    def select_tftp_dir(self):
        dir_path = filedialog.askdirectory(initialdir=self.tftp_dir)
        if dir_path:
            self.tftp_dir = dir_path
            self.tftp_dir_label.config(text=dir_path)
            self.log(f"TFTP 目录设置为: {dir_path}")

    def select_ftp_dir(self):
        dir_path = filedialog.askdirectory(initialdir=self.ftp_dir)
        if dir_path:
            self.ftp_dir = dir_path
            self.ftp_dir_label.config(text=dir_path)
            self.log(f"FTP 目录设置为: {dir_path}")

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        with self.log_lock:
            self.log_text.config(state="normal")
            
            # 根据日志级别设置不同颜色
            if level == "error":
                self.log_text.tag_config("error", foreground="red")
                self.log_text.insert("end", f"[{timestamp}] ", "error")
                self.log_text.insert("end", f"{message}\n", "error")
            elif level == "warning":
                self.log_text.tag_config("warning", foreground="orange")
                self.log_text.insert("end", f"[{timestamp}] ", "warning")
                self.log_text.insert("end", f"{message}\n", "warning")
            else:
                self.log_text.insert("end", f"[{timestamp}] {message}\n")
            
            self.log_text.see("end")
            self.log_text.config(state="disabled")

    def toggle_tftp(self):
            if not self.validate_port(self.tftp_port_entry.get()):
                messagebox.showerror("错误", "请输入有效的端口号(1-65535)")
                return
            self.start_tftp()
    def start_tftp(self):
        try:
            port = int(self.tftp_port_entry.get())
            self.log(f"正在启动 TFTP 服务，端口: {port}，目录: {self.tftp_dir}")
            
            def run_tftp_server():
            
                try:
                    server = TftpServer(self.tftp_dir)
                    server.listen("0.0.0.0", port)
                except PermissionError:
                    self.log(f"权限不足，不能监听端口 {port}", "error")
                except Exception as e:
                    self.log(f"TFTP 启动失败: {e}", "error")

                finally:
                    self.tftp_started = False
                    self.update_tftp_status()

            self.tftp_thread = threading.Thread(target=run_tftp_server, daemon=True)
            self.tftp_thread.start()
            self.tftp_started = True
            self.update_tftp_status()
            self.log("TFTP 服务已启动", "info")
        except Exception as e:
            self.log(f"启动 TFTP 服务时出错: {e}", "error")

    def stop_tftp(self):
        self.log("tftp无法手动停止，请关闭程序")


    def update_tftp_status(self):
        if self.tftp_started:
            
            self.tftp_btn.config(text="已启动")
        else:
            
            self.tftp_btn.config(text="启动 TFTP 服务")

    def toggle_ftp(self):
        if self.ftp_started:
            self.stop_ftp()
        else:
            if not self.validate_port(self.ftp_port_entry.get()):
                messagebox.showerror("错误", "请输入有效的端口号(1-65535)")
                return
            if not self.username_entry.get() or not self.password_entry.get():
                messagebox.showerror("错误", "用户名和密码不能为空")
                return
            self.start_ftp()

    def start_ftp(self):
        try:
            port = int(self.ftp_port_entry.get())
            user = self.username_entry.get()
            password = self.password_entry.get()
            
            self.log(f"正在启动 FTP 服务，端口: {port}，账号: {user}，目录: {self.ftp_dir}")

            def run_ftp():
                try:
                    authorizer = DummyAuthorizer()
                    authorizer.add_user(user, password, self.ftp_dir, perm="elradfmw")
                    
                    handler = FTPHandler
                    handler.authorizer = authorizer
                    handler.banner = "PyFTPd 服务器已就绪"
                    
                    self.ftp_server = FTPServer(("0.0.0.0", port), handler)
                    self.ftp_server.serve_forever()
                except OSError as e:
                    self.log(f"FTP 启动失败: {e}", "error")
                except Exception as e:
                    self.log(f"FTP 运行时错误: {e}", "error")
                finally:
                    self.ftp_started = False
                    self.update_ftp_status()

            self.ftp_thread = threading.Thread(target=run_ftp, daemon=True)
            self.ftp_thread.start()
            self.ftp_started = True
            self.update_ftp_status()
            self.log("FTP 服务已启动", "info")
        except Exception as e:
            self.log(f"启动 FTP 服务时出错: {e}", "error")

    def stop_ftp(self):
        self.log("正在停止 FTP 服务...")
        if self.ftp_server:
            self.ftp_server.close_all()
        self.ftp_started = False
        self.update_ftp_status()
        self.log("FTP 服务已停止")

    def update_ftp_status(self):
        if self.ftp_started:
            self.ftp_status_btn.config(text="🟢 运行中", bg="green")
            self.ftp_btn.config(text="停止 FTP 服务")
        else:
            self.ftp_status_btn.config(text="🔴 未运行", bg="red")
            self.ftp_btn.config(text="启动 FTP 服务")

    def on_close(self):
        self.log("正在关闭服务器...")
        if self.tftp_started:
            self.stop_tftp()
        if self.ftp_started:
            self.stop_ftp()
        self.log("程序已退出")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()