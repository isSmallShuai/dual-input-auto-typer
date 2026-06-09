import tkinter as tk
from tkinter import ttk  # 引入 ttk 组件用于下拉菜单
from tkinter import messagebox
import threading
import time
import pyautogui
import pyperclip
from pynput import mouse, keyboard
import random


class AutoChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("双窗口连发工具 (自定义热键版)")
        self.root.geometry("400x580")  # 稍微增加一点高度容纳新选项
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        self.coords = []
        self.is_running = False
        self.listener_mouse = None
        self.kb_listener = None

        self.setup_ui()

    def setup_ui(self):
        # --- 参数设置区 ---
        frame_settings = tk.LabelFrame(self.root, text="参数设置 (支持用 '|' 分割随机发送)", padx=10, pady=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_settings, text="页面1 内容:").grid(row=0, column=0, sticky="e", pady=5)
        self.entry_msg1 = tk.Entry(frame_settings, width=30)
        self.entry_msg1.grid(row=0, column=1, pady=5)
        self.entry_msg1.insert(0, "666|支持一下|太棒了")

        tk.Label(frame_settings, text="页面2 内容:").grid(row=1, column=0, sticky="e", pady=5)
        self.entry_msg2 = tk.Entry(frame_settings, width=30)
        self.entry_msg2.grid(row=1, column=1, pady=5)
        self.entry_msg2.insert(0, "打卡|点赞|学习了")

        tk.Label(frame_settings, text="互发次数:").grid(row=2, column=0, sticky="e", pady=5)
        self.entry_rounds = tk.Entry(frame_settings, width=10)
        self.entry_rounds.grid(row=2, column=1, sticky="w", pady=5)
        self.entry_rounds.insert(0, "10")

        tk.Label(frame_settings, text="基础间隔(秒):").grid(row=3, column=0, sticky="e", pady=5)
        self.entry_interval = tk.Entry(frame_settings, width=10)
        self.entry_interval.grid(row=3, column=1, sticky="w", pady=5)
        self.entry_interval.insert(0, "2.0")

        tk.Label(frame_settings, text="随机波动(秒):").grid(row=4, column=0, sticky="e", pady=5)
        self.entry_random = tk.Entry(frame_settings, width=10)
        self.entry_random.grid(row=4, column=1, sticky="w", pady=5)
        self.entry_random.insert(0, "0.5")

        # 新增：下拉菜单选择热键
        tk.Label(frame_settings, text="停止热键:").grid(row=5, column=0, sticky="e", pady=5)
        self.combo_hotkey = ttk.Combobox(frame_settings, values=["ESC", "F1", "F2", "F3", "F4", "F8", "F12", "space"],
                                         width=8, state="readonly")
        self.combo_hotkey.grid(row=5, column=1, sticky="w", pady=5)
        self.combo_hotkey.current(0)  # 默认选中第一个 (ESC)

        # --- 坐标录制区 ---
        frame_coords = tk.LabelFrame(self.root, text="坐标录制", padx=10, pady=10)
        frame_coords.pack(fill="x", padx=10, pady=5)

        self.btn_record = tk.Button(frame_coords, text="1. 点击开始录制坐标 (延迟2秒生效)",
                                    command=self.start_recording)
        self.btn_record.pack(fill="x", pady=5)

        self.lbl_status = tk.Label(frame_coords, text="状态: 等待录制...", fg="blue", font=("Arial", 10, "bold"))
        self.lbl_status.pack(pady=5)

        # --- 执行控制区 ---
        frame_action = tk.Frame(self.root, padx=10, pady=10)
        frame_action.pack(fill="x")

        self.btn_start = tk.Button(frame_action, text="2. 开始发送", bg="#4CAF50", fg="white",
                                   font=("Arial", 11, "bold"), command=self.start_task, state="disabled")
        self.btn_start.pack(side="left", fill="x", expand=True, padx=5, ipady=5)

        self.btn_stop = tk.Button(frame_action, text="紧急停止", bg="#f44336", fg="white", font=("Arial", 11, "bold"),
                                  command=self.stop_task, state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=5, ipady=5)

        self.lbl_tip = tk.Label(self.root, text="紧急停止：1. 按设定的热键  2. 鼠标甩到左上角", fg="#ff5722",
                                font=("微软雅黑", 9))
        self.lbl_tip.pack(side="bottom", pady=10)

    def start_recording(self):
        self.coords = []
        self.btn_record.config(state="disabled")
        self.btn_start.config(state="disabled")
        self.lbl_status.config(text="请准备... 2秒后开始监听", fg="orange")
        self.root.after(2000, self.activate_mouse_listener)

    def activate_mouse_listener(self):
        self.lbl_status.config(text="[1/2] 请点击: 页面1 【输入框】", fg="red")
        self.listener_mouse = mouse.Listener(on_click=self.on_click)
        self.listener_mouse.start()

    def on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            self.coords.append((x, y))
            step = len(self.coords)
            if step == 1:
                self.root.after(0, lambda: self.lbl_status.config(text="[2/2] 请点击: 页面2 【输入框】"))
            elif step == 2:
                self.root.after(0, self.finish_recording)
                return False

    def finish_recording(self):
        self.lbl_status.config(text="坐标录制完成！", fg="green")
        self.btn_record.config(state="normal", text="重新录制")
        self.btn_start.config(state="normal")

    def start_task(self):
        try:
            self.rounds = int(self.entry_rounds.get())
            self.base_interval = float(self.entry_interval.get())
            self.random_interval = float(self.entry_random.get())
            self.msg1_list = self.entry_msg1.get().split('|')
            self.msg2_list = self.entry_msg2.get().split('|')
        except ValueError:
            messagebox.showerror("错误", "参数请输入有效数字！")
            return

        if len(self.coords) < 2:
            messagebox.showwarning("警告", "请先录制 2 个坐标！")
            return

        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_record.config(state="disabled")
        self.btn_stop.config(state="normal")

        # 动态更新按钮和状态文本，显示当前选择的热键
        current_hotkey = self.combo_hotkey.get().upper()
        self.btn_stop.config(text=f"停止 ({current_hotkey})")
        self.lbl_status.config(text=f"任务运行中... (按 {current_hotkey} 停止)", fg="green")

        self.start_keyboard_listener()
        threading.Thread(target=self.sending_loop, daemon=True).start()

    def start_keyboard_listener(self):
        if self.kb_listener:
            self.kb_listener.stop()

        # 获取下拉菜单的值，并拼接成 pynput 识别的格式，例如 "<esc>", "<f1>"
        selected_key = self.combo_hotkey.get().lower()
        hotkey_str = f"<{selected_key}>"

        self.kb_listener = keyboard.GlobalHotKeys({
            hotkey_str: self.stop_task
        })
        self.kb_listener.start()

    def stop_task(self):
        self.is_running = False
        if self.kb_listener:
            self.kb_listener.stop()
            self.kb_listener = None

        self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.lbl_status.config(text="任务已停止。", fg="blue")
        self.btn_start.config(state="normal")
        self.btn_record.config(state="normal")
        self.btn_stop.config(state="disabled", text="紧急停止")

    def send_single_message(self, input_coord, message_list):
        if not self.is_running: return
        msg_to_send = random.choice(message_list)
        pyautogui.click(input_coord[0], input_coord[1])
        time.sleep(0.1)
        pyperclip.copy(msg_to_send)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
        pyautogui.press('enter')

    def sending_loop(self):
        for i in range(self.rounds):
            if not self.is_running: break
            self.root.after(0, lambda i=i: self.lbl_status.config(text=f"发送中: 第 {i + 1}/{self.rounds} 次",
                                                                  fg="purple"))

            self.send_single_message(self.coords[0], self.msg1_list)
            if not self.is_running: break
            time.sleep(self.base_interval + random.uniform(0, self.random_interval))

            self.send_single_message(self.coords[1], self.msg2_list)
            if not self.is_running: break
            time.sleep(self.base_interval + random.uniform(0, self.random_interval))

        self.is_running = False
        self.root.after(0, self.stop_task)


if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    root = tk.Tk()
    app = AutoChatApp(root)
    root.mainloop()
