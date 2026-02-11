#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微博 Cookie 获取工具 (GUI版)

严格复用 weibo_cookie_v1.py 的核心逻辑，增加更严格的登录判断。
输出三个值：WEIBO_SUB、WEIBO_SUBP、WEIBO_T_WM
支持将 Cookie 通过 HTTP POST 同步到 weibo-checkin 服务端（会员 Key 鉴权）。

依赖：pip install selenium webdriver-manager
"""

import sys
import json
import os
import time
import threading
import logging
import re
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, Optional, Tuple
import urllib.request as urllib_request
import urllib.error as urllib_error
import requests

# 屏蔽 requests 的 verify=False 警告
requests.packages.urllib3.disable_warnings()

# 全局字体配置
FONT_TITLE = ("微软雅黑", 16, "bold")
FONT_NORMAL = ("微软雅黑", 10)
FONT_BOLD = ("微软雅黑", 10, "bold")
FONT_SMALL = ("微软雅黑", 9)

# 禁用 webdriver-manager 的日志
logging.getLogger("WDM").setLevel(logging.ERROR)

SETTINGS_FILE = Path(__file__).with_name("weibo_cookie_gui_settings.json")
DEFAULT_SERVER_URL = "http://localhost:1234"
DEFAULT_CHECKIN_TIME = "08:00"
DEFAULT_RANDOM_DELAY = 300

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("依赖缺失", "请先安装依赖：\npip install selenium webdriver-manager")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────
# 核心逻辑层 —— 严格复用 v1 流程
# ─────────────────────────────────────────────────────────────────
class WeiboCookieGetter:
    """微博 Cookie 获取器（与 v1 逻辑一致，增强登录判断）"""

    DEFAULT_URL = "https://m.weibo.cn/p/tabbar?containerid=100803_-_recentvisit"
    LOGIN_VERIFY_URL = "https://m.weibo.cn/api/config"
    COOKIE_FIELDS = ["SUB", "SUBP", "_T_WM"]

    def __init__(self):
        self.url = self.DEFAULT_URL
        self.driver = None
        self._initial_sub = None          # 记录访客阶段的 SUB 值

    # ---------- 浏览器初始化 (同 v1) ----------
    def init_driver(self):
        if self.driver:
            return self.driver

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=414,896")

        mobile_ua = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/15.0 Mobile/15E148 Safari/604.1"
        )
        options.add_argument(f"--user-agent={mobile_ua}")

        # 优先尝试系统已有的 chromedriver，避免每次联网下载
        driver_path = None
        try:
            driver_path = ChromeDriverManager().install()
        except Exception:
            pass

        if driver_path:
            service = Service(driver_path)
        else:
            # 兜底：让 Selenium 自动查找系统 PATH 中的 chromedriver
            service = Service()

        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver

    # ---------- 打开页面 ----------
    def open_page(self):
        if self.driver:
            self.driver.get(self.url)
            time.sleep(2)
            # ★ 记录访客阶段的 SUB，后续用来区分是否真正登录
            cookies = self._get_all_cookies()
            self._initial_sub = cookies.get("SUB")

    # ---------- Cookie 读取 (同 v1) ----------
    def _get_all_cookies(self) -> Dict[str, str]:
        if not self.driver:
            return {}
        try:
            return {c["name"]: c["value"] for c in self.driver.get_cookies()}
        except Exception:
            return {}

    def get_target_cookies(self) -> Dict[str, Optional[str]]:
        all_cookies = self._get_all_cookies()
        return {field: all_cookies.get(field) for field in self.COOKIE_FIELDS}

    def _verify_login_by_api(self, all_cookies: Dict[str, str]) -> bool:
        """通过 m.weibo.cn/api/config 二次确认是否真的已登录。"""
        cookie_header = "; ".join(
            f"{k}={v}" for k, v in all_cookies.items() if v
        )
        if not cookie_header:
            return False

        try:
            resp = requests.get(
                self.LOGIN_VERIFY_URL,
                headers={
                    "User-Agent": self.driver.execute_script("return navigator.userAgent") if self.driver else "",
                    "Referer": "https://m.weibo.cn/",
                    "Cookie": cookie_header,
                },
                timeout=8,
                verify=False,
            )
            if resp.status_code != 200:
                return False

            payload = resp.json() if resp.content else {}
            data = (payload or {}).get("data") or {}
            login_flag = data.get("login")
            if isinstance(login_flag, str):
                login_flag = login_flag.lower() in ("1", "true", "yes")

            uid = data.get("uid")
            return bool(login_flag and uid)
        except Exception:
            return False

    def check_login_state(self) -> Tuple[bool, str]:
        """返回 (是否已登录, 状态原因)；用于 GUI 给出更准确提示。"""
        if not self.driver:
            return False, "no_driver"

        try:
            current_url = self.driver.current_url or ""

            if "passport." in current_url or "login." in current_url:
                return False, "in_login_flow"

            all_cookies = self._get_all_cookies()
            sub = all_cookies.get("SUB", "")
            subp = all_cookies.get("SUBP", "")

            if not sub or len(sub) <= 50:
                return False, "sub_invalid"

            if self._initial_sub and sub == self._initial_sub:
                return False, "visitor_cookie"

            if not subp:
                return False, "missing_subp"

            if not self._verify_login_by_api(all_cookies):
                return False, "api_not_confirmed"

            return True, "ok"
        except Exception:
            return False, "check_failed"

    # ---------- 登录检测（增强版 v1 逻辑）----------
    def is_logged_in(self) -> bool:
        """
        严格检测是否已登录（必须三个条件全部满足）：
          1. 当前不在 passport/login 域名上
          2. SUB 存在，长度 > 50，且与访客阶段的 SUB 不同
          3. SUBP 必须存在（这是区分访客和登录用户的核心标志）
        """
        ok, _ = self.check_login_state()
        return ok

    # ---------- 关闭浏览器 (同 v1) ----------
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None


# ─────────────────────────────────────────────────────────────────
# GUI 层
# ─────────────────────────────────────────────────────────────────
# 配色方案
BG_COLOR = "#f0f4f8"
CARD_BG = "#ffffff"
ACCENT = "#1e88e5"
ACCENT_HOVER = "#1565c0"
SUCCESS = "#43a047"
WARNING = "#ef6c00"
TEXT_PRIMARY = "#212121"
TEXT_SECONDARY = "#757575"
BORDER = "#e0e0e0"


class StyledButton(tk.Button):
    """带样式的按钮"""

    def __init__(self, parent, text, command=None, width=16,
                 bg=ACCENT, fg="white", font_size=10, **kwargs):
        super().__init__(
            parent, text=text, command=command,
            font=("微软雅黑", font_size),
            bg=bg, fg=fg, activebackground=ACCENT_HOVER,
            activeforeground="white", relief="flat",
            cursor="hand2", bd=0, padx=14, pady=6,
            width=width, **kwargs
        )
        self._bg = bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        if self["state"] != "disabled":
            darker = ACCENT_HOVER if self._bg == ACCENT else "#388e3c" if self._bg == SUCCESS else "#3949ab"
            self.config(bg=darker)

    def _on_leave(self, _):
        if self["state"] != "disabled":
            self.config(bg=self._bg)

    def set_enabled(self, enabled):
        if enabled:
            self.config(state="normal", bg=self._bg)
        else:
            self.config(state="disabled", bg="#bdbdbd")


class CookieApp:
    """主应用"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("微博 Cookie 提取工具")
        self.root.geometry("860x940")
        self.root.minsize(780, 840)
        self.root.configure(bg=BG_COLOR)
        self._center()

        self.getter = WeiboCookieGetter()
        self.is_checking = False
        self._login_confirm_hits = 0
        self.last_cookies: Dict[str, Optional[str]] = {}
        self.settings = self._load_settings()
        self.is_syncing = False

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- 窗口居中 ----------
    def _center(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _load_settings(self) -> dict:
        try:
            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {
            "server_url": DEFAULT_SERVER_URL,
            "member_key": "",
            "account_name": "",
            "sendkey": "",
            "sync_env": True,
            "schedule_enabled": True,
            "schedule_hour": "08",
            "schedule_minute": "00",
            "schedule_random_delay": DEFAULT_RANDOM_DELAY,
            "apply_schedule": True,
        }

    def _save_settings(self):
        if not hasattr(self, "server_url_var"):
            return
        data = {
            "server_url": self.server_url_var.get().strip(),
            "member_key": self.member_key_var.get().strip(),
            "account_name": self.account_name_var.get().strip(),
            "sendkey": self.sendkey_var.get().strip(),
            "sync_env": bool(self.sync_env_var.get()),
            "schedule_enabled": bool(self.schedule_enabled_var.get()),
            "schedule_hour": self.schedule_hour_var.get(),
            "schedule_minute": self.schedule_minute_var.get(),
            "schedule_random_delay": self.schedule_random_delay_var.get().strip(),
            "apply_schedule": bool(self.apply_schedule_var.get()),
        }
        try:
            SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # 忽略保存配置错误，不影响主流程
            pass

    # ---------- 构建界面 ----------
    def _build_ui(self):
        # 顶部标题栏
        header = tk.Frame(self.root, bg=ACCENT, height=64)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🔑  微博 Cookie 提取工具",
                 font=("微软雅黑", 16, "bold"), bg=ACCENT, fg="white").pack(
            side=tk.LEFT, padx=20, pady=14)

        # 主内容区
        container = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        # ── 使用说明卡片 ──
        info_card = tk.Frame(container, bg=CARD_BG, bd=0,
                             highlightbackground=BORDER, highlightthickness=1)
        info_card.pack(fill=tk.X, pady=(0, 14))

        tk.Label(info_card, text="📋 使用说明", font=("微软雅黑", 11, "bold"),
                 bg=CARD_BG, fg=TEXT_PRIMARY, anchor="w").pack(
            fill=tk.X, padx=16, pady=(12, 4))

        steps = (
            "① 点击下方「启动浏览器」按钮，会自动弹出 Chrome 浏览器\n"
            "② 在浏览器中使用 扫码 或 账号密码 登录微博\n"
            "③ 登录成功后工具会自动检测并提取 Cookie\n"
            "④ 点击对应按钮一键复制所需的值"
        )
        tk.Label(info_card, text=steps, font=("微软雅黑", 9),
                 bg=CARD_BG, fg=TEXT_SECONDARY, justify=tk.LEFT,
                 anchor="w", wraplength=540).pack(fill=tk.X, padx=16, pady=(0, 12))

        # ── 状态行 ──
        status_row = tk.Frame(container, bg=BG_COLOR)
        status_row.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = StyledButton(status_row, text="🚀 启动浏览器",
                                      command=self._start, width=16)
        self.start_btn.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="● 准备就绪")
        self.status_label = tk.Label(status_row, textvariable=self.status_var,
                                     font=("微软雅黑", 10), bg=BG_COLOR,
                                     fg=TEXT_SECONDARY, anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=16, fill=tk.X, expand=True)

        # ── 服务器同步设置卡片 ──
        sync_card = tk.Frame(container, bg=CARD_BG, bd=0,
                             highlightbackground=BORDER, highlightthickness=1)
        sync_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(sync_card, text="🌐 服务器同步设置", font=("微软雅黑", 11, "bold"),
                 bg=CARD_BG, fg=TEXT_PRIMARY, anchor="w").pack(
            fill=tk.X, padx=16, pady=(12, 8))

        form = tk.Frame(sync_card, bg=CARD_BG)
        form.pack(fill=tk.X, padx=16, pady=(0, 8))

        self.server_url_var = tk.StringVar(value=self.settings.get("server_url", DEFAULT_SERVER_URL))
        self.member_key_var = tk.StringVar(value=self.settings.get("member_key", ""))
        self.account_name_var = tk.StringVar(value=self.settings.get("account_name", ""))
        self.sync_env_var = tk.BooleanVar(value=bool(self.settings.get("sync_env", True)))
        self.schedule_enabled_var = tk.BooleanVar(value=bool(self.settings.get("schedule_enabled", True)))
        self.schedule_hour_var = tk.StringVar(value=str(self.settings.get("schedule_hour", "08")))
        self.schedule_minute_var = tk.StringVar(value=str(self.settings.get("schedule_minute", "00")))
        self.schedule_random_delay_var = tk.StringVar(value=str(self.settings.get("schedule_random_delay", DEFAULT_RANDOM_DELAY)))
        self.apply_schedule_var = tk.BooleanVar(value=bool(self.settings.get("apply_schedule", True)))
        self.sendkey_var = tk.StringVar(value=self.settings.get("sendkey", ""))

        self._build_form_row(form, "服务器地址", self.server_url_var, 0, "例如：http://47.253.253.245:1234")
        self._build_form_row(form, "会员 Key", self.member_key_var, 1, "管理员下发给用户脚本的 Key", masked=True)
        self._build_form_row(form, "账号名(首次绑定必填)", self.account_name_var, 2, "例如：user_001")
        self._build_time_select_row(form, "签到时间", self.schedule_hour_var, self.schedule_minute_var, 3)
        self._build_form_row(form, "随机延迟(秒)", self.schedule_random_delay_var, 4, "0-86400，默认 300")
        self._build_sendkey_row(form, "SendKey", self.sendkey_var, 5)

        opt_row = tk.Frame(sync_card, bg=CARD_BG)
        opt_row.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Checkbutton(
            opt_row,
            text="同时同步写入服务器 .env",
            variable=self.sync_env_var,
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            activebackground=CARD_BG,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(0, 12))
        tk.Checkbutton(
            opt_row,
            text="启用定时签到",
            variable=self.schedule_enabled_var,
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            activebackground=CARD_BG,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(0, 12))
        tk.Checkbutton(
            opt_row,
            text="上传后自动应用定时",
            variable=self.apply_schedule_var,
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            activebackground=CARD_BG,
            anchor="w",
        ).pack(side=tk.LEFT)

        sync_btn_row = tk.Frame(sync_card, bg=CARD_BG)
        sync_btn_row.pack(fill=tk.X, padx=16, pady=(0, 12))
        self.verify_key_btn = StyledButton(sync_btn_row, text="验证 Key", command=self._verify_member_key, width=12, bg="#5c6bc0")
        self.verify_key_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.checkin_btn = StyledButton(sync_btn_row, text="立即签到", command=self._trigger_checkin, width=12, bg="#ef6c00")
        self.checkin_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.upload_btn = StyledButton(sync_btn_row, text="上传 Cookie 到服务器", command=self._upload_cookie_to_server, width=20, bg="#3949ab")
        self.upload_btn.pack(side=tk.LEFT)

        tk.Label(
            sync_card,
            text="提示：点击“立即签到”可远程触发服务器执行一次签到并反馈结果。",
            font=("微软雅黑", 8),
            bg=CARD_BG,
            fg="#9e9e9e",
            anchor="w",
        ).pack(fill=tk.X, padx=16, pady=(0, 10))

        # ── Cookie 结果卡片 ──
        result_card = tk.Frame(container, bg=CARD_BG, bd=0,
                               highlightbackground=BORDER, highlightthickness=1)
        result_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Label(result_card, text="📦 Cookie 结果", font=("微软雅黑", 11, "bold"),
                 bg=CARD_BG, fg=TEXT_PRIMARY, anchor="w").pack(
            fill=tk.X, padx=16, pady=(12, 4))

        text_frame = tk.Frame(result_card, bg=CARD_BG)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        self.result_text = tk.Text(text_frame, font=("Consolas", 10),
                                   bg="#fafafa", fg=TEXT_PRIMARY,
                                   relief="flat", bd=0, wrap=tk.WORD,
                                   padx=10, pady=8,
                                   selectbackground=ACCENT,
                                   selectforeground="white")
        self.result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                  command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)

        # 配置文本标签样式
        self.result_text.tag_configure("title", font=("微软雅黑", 11, "bold"),
                                       foreground=ACCENT)
        self.result_text.tag_configure("key", font=("Consolas", 10, "bold"),
                                       foreground="#1565c0")
        self.result_text.tag_configure("value", font=("Consolas", 9),
                                       foreground="#333333")
        self.result_text.tag_configure("sep", foreground="#bdbdbd")
        self.result_text.tag_configure("hint", foreground=TEXT_SECONDARY,
                                       font=("微软雅黑", 9))

        # 默认提示
        self.result_text.insert(tk.END, "等待获取 Cookie …\n\n", "hint")
        self.result_text.insert(tk.END, "请先点击「启动浏览器」按钮，然后在弹出的浏览器中登录微博。", "hint")
        self.result_text.config(state=tk.DISABLED)

        # ── 底部操作按钮 ──
        btn_frame = tk.Frame(container, bg=BG_COLOR)
        btn_frame.pack(fill=tk.X)

        btn_defs = [
            ("复制 WEIBO_SUB", lambda: self._copy("SUB")),
            ("复制 WEIBO_SUBP", lambda: self._copy("SUBP")),
            ("复制 WEIBO_T_WM", lambda: self._copy("_T_WM")),
            ("复制全部 JSON", lambda: self._copy("JSON")),
        ]
        for text, cmd in btn_defs:
            bg = SUCCESS if "全部" not in text else "#5c6bc0"
            StyledButton(btn_frame, text=text, command=cmd,
                         width=14, bg=bg, font_size=9).pack(
                side=tk.LEFT, padx=(0, 8), pady=4)

    def _build_form_row(self, parent, label, var, row, placeholder="", masked=False):
        row_frame = tk.Frame(parent, bg=CARD_BG)
        row_frame.grid(row=row, column=0, sticky="ew", pady=4)
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(
            row_frame,
            text=label,
            font=("微软雅黑", 9),
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            width=16,
            anchor="w",
        ).pack(side=tk.LEFT)

        entry = tk.Entry(
            row_frame,
            textvariable=var,
            font=("Consolas", 10),
            relief="flat",
            bg="#fafafa",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            show="*" if masked else "",
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=4)
        if placeholder:
            hint = tk.Label(row_frame, text=placeholder, font=("微软雅黑", 8), bg=CARD_BG, fg="#9e9e9e", anchor="w")
            hint.pack(side=tk.LEFT, padx=(6, 0))

    def _build_time_select_row(
        self,
        parent: tk.Widget,
        label_text: str,
        hour_var: tk.StringVar,
        minute_var: tk.StringVar,
        row_idx: int,
    ):
        """构建时间选择行 (HH:MM)"""
        row_frame = tk.Frame(parent, bg=CARD_BG)
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=4)

        tk.Label(
            row_frame, text=label_text, font=("微软雅黑", 9),
            bg=CARD_BG, fg=TEXT_SECONDARY, width=16, anchor="w",
        ).pack(side=tk.LEFT)

        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(60)]

        cb_hour = ttk.Combobox(row_frame, textvariable=hour_var, values=hours, width=3, state="readonly", font=FONT_NORMAL)
        cb_hour.pack(side=tk.LEFT, padx=(4, 0))
        tk.Label(row_frame, text=" : ", bg=CARD_BG, font=FONT_NORMAL).pack(side=tk.LEFT)
        cb_minute = ttk.Combobox(row_frame, textvariable=minute_var, values=minutes, width=3, state="readonly", font=FONT_NORMAL)
        cb_minute.pack(side=tk.LEFT)

    def _build_sendkey_row(
        self,
        parent: tk.Widget,
        label_text: str,
        var: tk.StringVar,
        row_idx: int,
        tip: str = "Server酱推送密钥",
    ):
        """构建 SendKey 行，带测试按钮和链接"""
        row_frame = tk.Frame(parent, bg=CARD_BG)
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=4)

        tk.Label(
            row_frame, text=label_text, font=("微软雅黑", 9),
            bg=CARD_BG, fg=TEXT_SECONDARY, width=16, anchor="w",
        ).pack(side=tk.LEFT)

        entry = ttk.Entry(row_frame, textvariable=var, font=FONT_NORMAL)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # 获取链接按钮
        def _open_link():
            webbrowser.open("https://sct.ftqq.com/sendkey")

        link_btn = ttk.Button(row_frame, text="获取 Key", command=_open_link, width=8)
        link_btn.pack(side=tk.LEFT, padx=(5, 0))

        # 测试推送按钮
        test_btn = ttk.Button(row_frame, text="测试推送", command=self._test_push, width=8)
        test_btn.pack(side=tk.LEFT, padx=(5, 0))


    # ---------- 状态更新 ----------
    def _set_status(self, msg: str, color: str = TEXT_SECONDARY):
        self.status_var.set(msg)
        self.status_label.config(fg=color)

    # ---------- 启动流程 ----------
    def _start(self):
        if self.is_checking:
            return
        self.start_btn.set_enabled(False)
        self._clear_result()
        self._set_status("⏳ 正在初始化浏览器…", ACCENT)
        threading.Thread(target=self._open_browser, daemon=True).start()

    def _open_browser(self):
        try:
            self.getter.init_driver()
            self.root.after(0, lambda: self._set_status("⏳ 浏览器已打开，正在加载页面…", ACCENT))
            self.getter.open_page()
            self.is_checking = True
            self._login_confirm_hits = 0
            self._was_in_login_flow = False
            self.root.after(0, lambda: self._set_status(
                "⏳ 等待登录中… 请在浏览器中登录微博", WARNING))
            self.root.after(2000, self._check_login)
        except Exception as e:
            self.root.after(0, lambda: self._handle_error(str(e)))

    # ---------- 登录检测循环（同 v1 的 _wait_for_login 逻辑）----------
    def _check_login(self):
        if not self.is_checking:
            return

        # 检查浏览器是否仍然存活
        try:
            _ = self.getter.driver.title
        except Exception:
            self.is_checking = False
            self._set_status("✗ 浏览器已关闭", "#e53935")
            self.start_btn.set_enabled(True)
            return

        # 检测 URL 是否跳转到了 passport/login（说明用户正在登录操作中）
        current_url = ""
        try:
            current_url = self.getter.driver.current_url or ""
        except Exception:
            pass

        in_login_flow = "passport." in current_url or "login." in current_url

        if in_login_flow:
            self._was_in_login_flow = True
            self._set_status("⏳ 检测到正在登录… 请完成登录操作", WARNING)
            self.root.after(1500, self._check_login)
            return

        # 已不在 passport/login 域名上，执行严格检测
        ok, reason = self.getter.check_login_state()
        if ok:
            self._login_confirm_hits += 1
            if self._login_confirm_hits >= 2:
                self._on_login_success()
                return
            self._set_status("⏳ 登录态已识别，正在二次确认…", ACCENT)
            self.root.after(1200, self._check_login)
            return

        self._login_confirm_hits = 0

        if reason in ("visitor_cookie", "missing_subp", "api_not_confirmed"):
            self._set_status("⏳ 检测到访客态 Cookie，继续等待登录完成…", WARNING)
            self.root.after(1500, self._check_login)
            return

        # 保留原跳转回主站补抓逻辑
        if reason == "sub_invalid" and self._was_in_login_flow:
            # 刚从 passport 域名跳回来，需要导航回目标页面拿 Cookie
            self._was_in_login_flow = False
            self._set_status("⏳ 登录流程完成，正在跳转回微博获取 Cookie…", ACCENT)
            threading.Thread(target=self._navigate_back_and_check, daemon=True).start()
        elif self._was_in_login_flow:
            self._was_in_login_flow = False
            self._set_status("⏳ 登录流程完成，正在跳转回微博获取 Cookie…", ACCENT)
            threading.Thread(target=self._navigate_back_and_check, daemon=True).start()
        else:
            self._set_status("⏳ 等待登录中… 请在浏览器中登录微博", WARNING)
            self.root.after(2000, self._check_login)

    def _navigate_back_and_check(self):
        """登录完成后导航回 m.weibo.cn 页面获取 Cookie"""
        try:
            self.getter.driver.get(self.getter.url)
            time.sleep(3)
            ok, _ = self.getter.check_login_state()
            if ok:
                self.root.after(0, self._on_login_success)
                return
        except Exception:
            pass
        # 仍未检测到 → 继续轮询
        self.root.after(0, lambda: self._resume_check_login())

    def _resume_check_login(self):
        """恢复轮询检测登录"""
        if self.is_checking:
            self.root.after(2000, self._check_login)

    # ---------- 登录成功：刷新 + 取 Cookie（同 v1 的 run 流程）----------
    def _on_login_success(self):
        self.is_checking = False
        self._set_status("✓ 检测到登录成功！正在获取完整 Cookie…", SUCCESS)

        def _fetch():
            try:
                # 确保当前在 m.weibo.cn 域名下
                current_url = self.getter.driver.current_url or ""
                if "m.weibo.cn" not in current_url:
                    self.getter.driver.get(self.getter.url)
                    time.sleep(3)
                
                # 刷新页面确保 Cookie 完整
                self.getter.driver.refresh()
                time.sleep(2)

                cookies = self.getter.get_target_cookies()
                
                # 双重确认：如果 SUBP 为空，再试一次
                if not cookies.get("SUBP"):
                    time.sleep(2)
                    cookies = self.getter.get_target_cookies()

                self.root.after(0, lambda: self._display(cookies))
            except Exception as e:
                self.root.after(0, lambda: self._handle_error(str(e)))

        threading.Thread(target=_fetch, daemon=True).start()

    # ---------- 显示结果 ----------
    def _display(self, cookies: Dict[str, Optional[str]]):
        self.last_cookies = cookies
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)

        mapping = [
            ("WEIBO_SUB", "SUB"),
            ("WEIBO_SUBP", "SUBP"),
            ("WEIBO_T_WM", "_T_WM"),
        ]

        self.result_text.insert(tk.END, "─── 提取结果 ───\n\n", "title")

        all_found = True
        for display_name, key in mapping:
            value = cookies.get(key)
            self.result_text.insert(tk.END, f"  {display_name}\n", "key")
            if value:
                self.result_text.insert(tk.END, f"  {value}\n\n", "value")
            else:
                self.result_text.insert(tk.END, "  (未找到)\n\n", "hint")
                all_found = False

        self.result_text.insert(tk.END, "─" * 40 + "\n", "sep")
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items() if v)
        self.result_text.insert(tk.END, "\n完整 Cookie 字符串:\n", "key")
        self.result_text.insert(tk.END, f"{cookie_str}\n", "value")

        self.result_text.config(state=tk.DISABLED)

        if all_found:
            self._set_status("✓ Cookie 获取成功！可复制或上传到服务器", SUCCESS)
        else:
            self._set_status("⚠ 部分字段未找到，请检查", WARNING)

        self.start_btn.set_enabled(True)

    # ---------- 复制 ----------
    def _copy(self, mode: str):
        if not self.last_cookies:
            messagebox.showwarning("提示", "暂无 Cookie 数据，请先启动浏览器获取。")
            return

        label_map = {"SUB": "WEIBO_SUB", "SUBP": "WEIBO_SUBP", "_T_WM": "WEIBO_T_WM"}

        if mode == "JSON":
            out = {label_map.get(k, k): v for k, v in self.last_cookies.items() if v}
            content = json.dumps(out, indent=2, ensure_ascii=False)
            name = "JSON"
        else:
            content = self.last_cookies.get(mode, "")
            name = label_map.get(mode, mode)
            if not content:
                messagebox.showwarning("提示", f"未找到 {name}")
                return

        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self._set_status(f"✓ 已复制 {name} 到剪贴板", SUCCESS)

    # ---------- 服务器同步 ----------    
    def _set_sync_busy(self, busy: bool):
        self.is_syncing = busy
        if hasattr(self, "verify_key_btn"):
            self.verify_key_btn.set_enabled(not busy)
        if hasattr(self, "checkin_btn"):
            self.checkin_btn.set_enabled(not busy)
        if hasattr(self, "upload_btn"):
            self.upload_btn.set_enabled(not busy)

    def _build_schedule_payload(self) -> Optional[dict]:
        hour = self.schedule_hour_var.get()
        minute = self.schedule_minute_var.get()

        try:
            h = int(hour)
            m = int(minute)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "签到时间格式错误。")
            return None

        raw_delay = (self.schedule_random_delay_var.get() or "").strip()
        if not raw_delay:
            delay = DEFAULT_RANDOM_DELAY
        else:
            try:
                delay = int(raw_delay)
            except ValueError:
                messagebox.showwarning("提示", "随机延迟必须是整数（秒）。")
                return None

        if delay < 0 or delay > 86_400:
            messagebox.showwarning("提示", "随机延迟范围应为 0-86400 秒。")
            return None

        return {
            "enabled": bool(self.schedule_enabled_var.get()),
            "time": f"{h:02d}:{m:02d}",
            "random_delay": delay,
        }

    def _collect_server_options(self, require_account: bool = False, include_schedule: bool = True) -> Optional[dict]:
        server_url = self.server_url_var.get().strip().rstrip("/")
        member_key = self.member_key_var.get().strip()
        account_name = self.account_name_var.get().strip()
        sendkey = self.sendkey_var.get().strip()
        sync_env = bool(self.sync_env_var.get())
        apply_schedule = bool(self.apply_schedule_var.get())
        schedule = None

        if not server_url:
            messagebox.showwarning("提示", "请填写服务器地址。")
            return None
        if not server_url.startswith("http://") and not server_url.startswith("https://"):
            messagebox.showwarning("提示", "服务器地址必须以 http:// 或 https:// 开头。")
            return None
        if not member_key:
            messagebox.showwarning("提示", "请填写会员 Key。")
            return None
        if require_account and not account_name:
            messagebox.showwarning("提示", "首次绑定时请填写账号名。")
            return None

        if include_schedule:
            schedule = self._build_schedule_payload()
            if schedule is None:
                return None

        self._save_settings()
        return {
            "server_url": server_url,
            "member_key": member_key,
            "account_name": account_name,
            "sendkey": sendkey,
            "sync_env": sync_env,
            "apply_schedule": apply_schedule,
            "schedule": schedule,
        }

    def _api_post_json(self, server_url: str, path: str, payload: dict, member_key: str) -> tuple:
        url = f"{server_url}{path}"
        body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        req = urllib_request.Request(
            url=url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Member-Key": member_key,
                "X-Access-Key": member_key,
            },
        )
        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                status_code = int(resp.status)
                text = resp.read().decode("utf-8", errors="replace")
        except urllib_error.HTTPError as http_err:
            status_code = int(getattr(http_err, "code", 500) or 500)
            text = http_err.read().decode("utf-8", errors="replace")
        except urllib_error.URLError as url_err:
            # 处理连接失败（如 WinError 10061, Connection Refused）
            reason = str(url_err.reason)
            if "WinError 10061" in reason or "Connection refused" in reason:
                msg = f"连接被拒绝 (10061)\n请检查服务器是否已启动，且地址 {server_url} 正确。"
            elif "timed out" in reason:
                msg = "连接超时，请检查网络或防火墙设置。"
            else:
                msg = f"无法连接服务器：\n{reason}"
            return False, 0, {"ok": False, "message": msg}
        except Exception as exc:
            return False, 0, {"ok": False, "message": str(exc)}

        try:
            data = json.loads(text) if text else {}
        except Exception:
            data = {"ok": False, "message": text or "Invalid response"}

        ok = 200 <= status_code < 300 and bool(data.get("ok", False))
        return ok, status_code, data

    def _verify_member_key(self):
        if self.is_syncing:
            return
        opts = self._collect_server_options(require_account=False, include_schedule=False)
        if not opts:
            return

        self._set_sync_busy(True)
        self._set_status("⏳ 正在验证会员 Key…", ACCENT)
        threading.Thread(target=self._verify_member_key_worker, args=(opts,), daemon=True).start()

    def _verify_member_key_worker(self, opts: dict):
        ok, status_code, data = self._api_post_json(
            server_url=opts["server_url"],
            path="/api/external/key/verify",
            payload={},
            member_key=opts["member_key"],
        )

        def _finish():
            self._set_sync_busy(False)
            if ok:
                account_name = (data.get("account_name") or "").strip()
                bound_text = account_name if account_name else "未绑定（首次上传请填写账号名）"
                if account_name and not self.account_name_var.get().strip():
                    self.account_name_var.set(account_name)
                    self._save_settings()
                self._set_status("✓ Key 验证通过", SUCCESS)
                messagebox.showinfo("验证成功", f"Key 有效\n绑定账号：{bound_text}")
            else:
                msg = data.get("message") or f"HTTP {status_code}"
                self._set_status("✗ Key 验证失败", "#e53935")
                messagebox.showerror("验证失败", f"Key 无效：{msg}")

        self.root.after(0, _finish)

    # ── 测试推送 ──────────────────────────────────────────────
    def _test_push(self):
        if self.is_syncing:
            return
        sendkey = self.sendkey_var.get().strip()
        if not sendkey:
            messagebox.showwarning("提示", "请先填写 SendKey。")
            return

        self._set_sync_busy(True)
        self._set_status("⏳ 正在测试推送…", ACCENT)
        threading.Thread(target=self._test_push_worker, args=({}, sendkey), daemon=True).start()

    def _test_push_worker(self, opts: dict, sendkey: str):
        """直接调用 Server酱 API 测试推送，无需经过后端服务器"""
        url = f"https://sctapi.ftqq.com/{sendkey}.send"
        payload = {
            "title": "推送测试",
            "desp": "这是一条来自微博自动签到助手的测试消息。\n\n如果您收到此消息，说明 SendKey 配置正确。",
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib_request.Request(
            url=url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                status_code = int(resp.status)
                text = resp.read().decode("utf-8", errors="replace")
        except urllib_error.HTTPError as http_err:
            status_code = int(getattr(http_err, "code", 500) or 500)
            text = http_err.read().decode("utf-8", errors="replace")
        except urllib_error.URLError as url_err:
            status_code = 0
            text = json.dumps({"ok": False, "message": f"网络错误：{url_err.reason}"})
        except Exception as exc:
            status_code = 0
            text = json.dumps({"ok": False, "message": str(exc)})

        try:
            data = json.loads(text) if text else {}
        except Exception:
            data = {"ok": False, "message": text or "Invalid response"}

        # Server酱返回 code=0 表示成功
        ok = status_code == 200 and data.get("code") == 0

        def _finish():
            self._set_sync_busy(False)
            if ok:
                self._set_status("✓ 推送测试成功", SUCCESS)
                messagebox.showinfo("推送测试", "推送消息已发送，请检查您的微信。")
            else:
                errmsg = data.get("message") or data.get("info") or f"HTTP {status_code}"
                self._set_status("✗ 推送测试失败", "#e53935")
                messagebox.showerror("推送测试失败", f"推送失败：{errmsg}")

        self.root.after(0, _finish)

    # ── 一键签到 ──────────────────────────────────────────────
    def _trigger_checkin(self):
        if self.is_syncing:
            return
        opts = self._collect_server_options(require_account=False, include_schedule=False)
        if not opts:
            return

        sendkey = self.sendkey_var.get().strip()
        payload = {}
        if opts.get("account_name"):
            payload["account_name"] = opts["account_name"]
        if sendkey:
            payload["sendkey"] = sendkey

        self._set_sync_busy(True)
        self._set_status("⏳ 正在执行远程签到，可能需要较长时间…", ACCENT)
        threading.Thread(target=self._checkin_worker, args=(opts, payload), daemon=True).start()

    def _checkin_worker(self, opts: dict, payload: dict):
        ok, status_code, data = self._api_post_json(
            server_url=opts["server_url"],
            path="/api/external/checkin/trigger",
            payload=payload,
            member_key=opts["member_key"],
        )

        def _finish():
            self._set_sync_busy(False)
            if ok:
                detail = data.get("detail", "")
                account = data.get("account", "")
                msg = data.get("message", "签到完成")
                self._set_status(f"✓ {msg}", SUCCESS)
                messagebox.showinfo("签到完成", f"账号：{account}\n\n{msg}\n\n{detail}")
            else:
                if status_code == 404:
                    errmsg = (
                        "服务器不支持远程签到功能 (HTTP 404)。\n\n"
                        "请在服务器上更新后端代码并重启容器：\n"
                        "  cd /项目目录 && git pull\n"
                        "  docker compose up -d --build backend"
                    )
                elif status_code == 422:
                    errmsg = f"请求参数错误：{data.get('detail', data.get('message', ''))}"
                else:
                    errmsg = data.get("message") or f"HTTP {status_code}"
                self._set_status("✗ 签到失败", "#e53935")
                messagebox.showerror("签到失败", errmsg)

        self.root.after(0, _finish)

    def _upload_cookie_to_server(self):
        if self.is_syncing:
            return
        if not self.last_cookies or not self.last_cookies.get("SUB"):
            messagebox.showwarning("提示", "请先获取 Cookie，再执行上传。")
            return

        opts = self._collect_server_options(require_account=False, include_schedule=True)
        if not opts:
            return

        payload = {
            "account_name": opts["account_name"],
            "SUB": self.last_cookies.get("SUB", ""),
            "SUBP": self.last_cookies.get("SUBP", ""),
            "_T_WM": self.last_cookies.get("_T_WM", ""),
            "sync_env": opts["sync_env"],
            "schedule": opts["schedule"],
            "apply_schedule": opts["apply_schedule"],
        }

        self._set_sync_busy(True)
        self._set_status("⏳ 正在上传 Cookie 到服务器…", ACCENT)
        threading.Thread(target=self._upload_cookie_worker, args=(opts, payload), daemon=True).start()

    def _upload_cookie_worker(self, opts: dict, payload: dict):
        ok, status_code, data = self._api_post_json(
            server_url=opts["server_url"],
            path="/api/external/cookie/update",
            payload=payload,
            member_key=opts["member_key"],
        )

        def _finish():
            self._set_sync_busy(False)
            if ok:
                account = data.get("account") or opts.get("account_name") or "--"
                notice = data.get("notification", {})
                notice_text = notice.get("message", "通知未发送")
                cron = data.get("cron", {}) if isinstance(data.get("cron"), dict) else {}
                cron_text = cron.get("message", "未执行定时应用")
                self._set_status("✓ Cookie 已上传并写入服务器", SUCCESS)
                messagebox.showinfo(
                    "上传成功",
                    f"账号：{account}\n"
                    f"消息：{data.get('message', 'Cookie 已更新成功')}\n"
                    f"定时：{cron_text}\n"
                    f"Server酱：{notice_text}",
                )
            else:
                msg = data.get("message") or f"HTTP {status_code}"
                self._set_status("✗ Cookie 上传失败", "#e53935")
                messagebox.showerror("上传失败", msg)

        self.root.after(0, _finish)

    # ---------- 工具方法 ----------
    def _clear_result(self):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "正在初始化，请稍候…", "hint")
        self.result_text.config(state=tk.DISABLED)
        self.last_cookies = {}

    def _handle_error(self, msg: str):
        self._set_status("✗ 发生错误", "#e53935")
        self.start_btn.set_enabled(True)
        messagebox.showerror("错误", f"浏览器启动失败：\n{msg}")

    def _on_close(self):
        self.is_checking = False
        self._save_settings()
        self.getter.close()
        self.root.destroy()
        sys.exit(0)


# ─────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    CookieApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
