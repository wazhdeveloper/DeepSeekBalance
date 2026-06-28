"""
DeepSeek 余额 - 系统托盘版
在任务栏显示 DeepSeek API 余额图标，鼠标悬停查看余额
"""

import sys, os, json, time, subprocess, threading
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import pystray

APP_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'DeepSeekBalance')
os.makedirs(APP_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(APP_DIR, 'deepseek_config.json')
DEFAULT_CONFIG = {"api_key": "", "refresh_interval": 300}

GREEN  = "#bbf7d0"
YELLOW = "#fef08a"
RED    = "#fecaca"
BLUE   = "#bfdbfe"
RECHARGE_URL = "https://platform.deepseek.com/top_up"

class DeepSeekTray:
    def __init__(self):
        self.config = self.load_config()
        self.data = {"available": None, "total": None, "used": None, "error": None, "last_update": None}
        self.stop_event = threading.Event()
        self.icon = self.build_icon()
        threading.Thread(target=self.update_loop, daemon=True).start()

    def pick_color(self, balance):
        if balance is None:  return BLUE
        if balance > 10:     return GREEN
        if balance > 3:      return YELLOW
        return RED

    def fmt_num(self, balance):
        if balance is None:  return "¥"
        return f"{int(balance)}"

    def make_image(self, balance=None):
        sz = 128
        img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = self.pick_color(balance)
        draw.rounded_rectangle([2, 2, sz-2, sz-2], radius=10, fill=color)
        text = self.fmt_num(balance)
        n = len(text)
        if n <= 1:   fs = 82
        elif n == 2: fs = 72
        elif n == 3: fs = 56
        else:        fs = 42
        font = None
        try:  font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", fs)
        except:
            try:  font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", fs)
            except: font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (sz - (bbox[2]-bbox[0])) // 2 - bbox[0]
        y = (sz - (bbox[3]-bbox[1])) // 2 - bbox[1] - 1
        draw.text((x, y), text, fill="black", font=font)
        return img

    def build_icon(self):
        icon = pystray.Icon("DeepSeekBalance", self.make_image(None), "DeepSeek 余额",
            menu=pystray.Menu(
                pystray.MenuItem(self.menu_balance, None, enabled=False),
                pystray.MenuItem(self.menu_status, None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("充值", self.on_recharge),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("刷新", self.on_refresh),
                pystray.MenuItem("设置 API Key", self.on_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self.on_exit),
            ))
        icon.on_activate = self.on_click
        return icon

    # ... (methods omitted for brevity - will be complete in actual file)
    def menu_balance(self, item=None):
        a = self.data.get("available")
        return f"¥ {a:.2f}" if a else "加载中..."

    def menu_status(self, item=None):
        e = self.data.get("error")
        if e: return f"{e}"
        t, u = self.data.get("total"), self.data.get("used")
        if t and u is not None:
            return f"总额 ¥{t:.2f}  |  已用 {(u/t)*100:.1f}%"
        lu = self.data.get("last_update")
        return f"更新于 {lu.strftime('%H:%M:%S')}" if lu else "等待更新..."

    def on_click(self, icon):
        a = self.data.get("available")
        if a is not None:
            icon.notify(f"可用余额: ¥{a:.2f}",
                        f"总额: ¥{self.data.get('total',0):.2f}  已用: ¥{self.data.get('used',0):.2f}")
        elif self.data.get("error"):
            icon.notify("DeepSeek 余额", self.data["error"])
        else:
            icon.notify("DeepSeek 余额", "正在获取...")

    def refresh_display(self):
        a, err = self.data.get("available"), self.data.get("error")
        self.icon.icon = self.make_image(a)
        self.icon.title = f"¥ {a:.2f}" if a is not None else (f"{err}" if err else "DeepSeek")
        self.icon.update_menu()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except: pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except: pass

    def fetch_data(self):
        key = self.config.get("api_key", "").strip()
        if not key: return {"error": "未设置 API Key"}
        try:
            r = requests.get("https://api.deepseek.com/user/balance",
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json"}, timeout=10)
            if r.status_code == 401: return {"error": "API Key 无效"}
            if r.status_code == 429: return {"error": "请求太频繁"}
            d = r.json()
            infos = d.get("balance_infos", [])
            if infos:
                i = infos[0]
                total = float(i.get("total_balance", 0))
                avail = float(i.get("granted_balance", 0)) + float(i.get("topped_up_balance", 0))
            else:
                total = float(d.get("total_balance", 0))
                avail = float(d.get("granted_balance", 0)) + float(d.get("topped_up_balance", 0))
            return {"total": total or avail, "used": max(0, total-avail) if total else 0,
                    "available": avail, "error": None}
        except requests.exceptions.ConnectionError: return {"error": "网络连接失败"}
        except requests.exceptions.Timeout: return {"error": "请求超时"}
        except Exception as e: return {"error": f"获取失败: {str(e)[:30]}"}

    def do_update(self):
        r = self.fetch_data()
        if r.get("error"):
            self.data["error"] = r["error"]
            self.data["available"] = self.data["total"] = self.data["used"] = None
        else:
            self.data["error"] = None
            self.data["available"] = r["available"]
            self.data["total"] = r["total"]
            self.data["used"] = r["used"]
        self.data["last_update"] = datetime.now()
        self.refresh_display()

    def update_loop(self):
        time.sleep(2)
        self.do_update()
        interval = max(self.config.get("refresh_interval", 300), 60)
        while not self.stop_event.is_set():
            if self.stop_event.wait(interval): break
            self.do_update()

    def on_recharge(self, icon, item):
        script = os.path.join(APP_DIR, 'deepseek_recharge.pyw')
        if os.path.exists(script):
            subprocess.Popen(['python', script], creationflags=subprocess.CREATE_NO_WINDOW)

    def on_settings(self, icon, item):
        old = self.config.get("api_key", "")
        ps = f'''
Add-Type -AssemblyName Microsoft.VisualBasic
$k = [Microsoft.VisualBasic.Interaction]::InputBox("DeepSeek API Key：", "设置", "{old}")
if ($k -ne "") {{ Write-Host $k }} else {{ Write-Host "CANCEL" }}
'''
        try:
            r = subprocess.run(['powershell','-NoProfile','-Command',ps],
                capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            k = r.stdout.strip()
            if k and k != "CANCEL":
                self.config["api_key"] = k
                self.save_config()
                self.do_update()
        except: pass

    def on_refresh(self, icon, item): self.do_update()
    def on_exit(self, icon, item): self.stop_event.set(); self.icon.stop()
    def run(self): self.icon.run()

if __name__ == "__main__":
    DeepSeekTray().run()
