"""
DeepSeek 余额 + 火山引擎余额 - 系统托盘版
在任务栏显示 DeepSeek API 余额图标，鼠标悬停/点击查看双平台余额
"""

import sys, os, json, time, subprocess, threading
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import pystray

# 火山引擎 SDK（namespace package）
import volcenginesdkcore
import volcenginesdkbilling

APP_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'DeepSeekBalance')
os.makedirs(APP_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(APP_DIR, 'deepseek_config.json')
DEFAULT_CONFIG = {
    "api_key": "",
    "refresh_interval": 300,
    "volcano_ak": "",
    "volcano_sk": "",
    "volcano_region": "cn-beijing",
}

GREEN  = "#bbf7d0"
YELLOW = "#fef08a"
RED    = "#fecaca"
BLUE   = "#bfdbfe"
PURPLE = "#e9d5ff"  # 火山引擎用紫色

DS_RECHARGE_URL = "https://platform.deepseek.com/top_up"



class DeepSeekTray:
    def __init__(self):
        self.config = self.load_config()
        self.data = {
            "ds_available": None, "ds_total": None, "ds_used": None,
            "volcano_available": None,
            "error": None, "last_update": None,
        }
        self.stop_event = threading.Event()
        self.icon = self.build_icon()
        threading.Thread(target=self.update_loop, daemon=True).start()

    # ── 图标相关 ──

    def pick_color(self, balance_ds, balance_vc=None):
        """取较低余额对应的颜色；如果任一为空返回蓝"""
        vals = []
        if balance_ds is not None: vals.append(balance_ds)
        if balance_vc is not None: vals.append(balance_vc)
        if not vals: return BLUE
        b = min(vals)
        if b > 10:  return GREEN
        if b > 3:   return YELLOW
        return RED

    def fmt_num(self, balance):
        if balance is None: return "¥"
        return f"{int(balance)}"

    def make_image(self, balance_ds=None, balance_vc=None):
        sz = 128
        img = Image.new('RGBA', (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = self.pick_color(balance_ds, balance_vc)
        draw.rounded_rectangle([2, 2, sz-2, sz-2], radius=10, fill=color)
        text = self.fmt_num(balance_ds)
        n = len(text)
        if n <= 1:   fs = 96
        elif n == 2: fs = 86
        elif n == 3: fs = 72
        else:        fs = 56
        font = None
        for bold in ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/seguisb.ttf",
                     "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/msyhbd.ttc",
                     "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
            try:
                font = ImageFont.truetype(bold, fs)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (sz - (bbox[2]-bbox[0])) // 2 - bbox[0]
        y = (sz - (bbox[3]-bbox[1])) // 2 - bbox[1] - 1
        draw.text((x, y), text, fill="black", font=font)
        return img

    # ── 菜单 ──

    def build_icon(self):
        icon = pystray.Icon("DeepSeekBalance", self.make_image(None),
                            "DeepSeek + 火山引擎 余额",
            menu=pystray.Menu(
                pystray.MenuItem(self.menu_balance_ds, None, enabled=False),
                pystray.MenuItem(self.menu_balance_volcano, None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("充值", self.on_recharge),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("刷新", self.on_refresh),
                pystray.MenuItem("设置 DeepSeek API Key", self.on_settings_ds),
                pystray.MenuItem("设置 火山引擎 AK/SK", self.on_settings_volcano),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self.on_exit),
            ))
        icon.on_activate = self.on_click
        return icon

    def menu_balance_ds(self, item=None):
        a = self.data.get("ds_available")
        return f"DeepSeek  ¥ {a:.2f}" if a else "DeepSeek  加载中..."

    def menu_balance_volcano(self, item=None):
        a = self.data.get("volcano_available")
        if a is not None:
            return f"火山引擎  ¥ {a:.2f}"
        if self.config.get("volcano_ak"):
            return "火山引擎  加载中..."
        return "火山引擎  未配置 AK/SK"

    def on_click(self, icon):
        ds  = self.data.get("ds_available")
        vc  = self.data.get("volcano_available")
        err = self.data.get("error")

        lines = []
        if ds is not None:
            total = self.data.get("ds_total", 0)
            used  = self.data.get("ds_used", 0)
            lines.append(f"DeepSeek: 可用 ¥{ds:.2f}   总额 ¥{total:.2f}   已用 ¥{used:.2f}")
        else:
            lines.append("DeepSeek: 加载中...")
        if vc is not None:
            lines.append(f"火山引擎: 可用 ¥{vc:.2f}")
        elif self.config.get("volcano_ak"):
            lines.append("火山引擎: 加载中...")
        else:
            lines.append("火山引擎: 未配置")
        if err and not ds:
            lines.append(f"⚠ {err}")
        icon.notify("双平台余额", "\n".join(lines))

    def refresh_display(self):
        ds  = self.data.get("ds_available")
        vc  = self.data.get("volcano_available")
        err = self.data.get("error")

        self.icon.icon = self.make_image(ds, vc)

        parts = []
        if ds is not None:
            parts.append(f"DS ¥{ds:.2f}")
        elif err:
            parts.append(f"DS {err[:10]}")
        else:
            parts.append("DS ...")
        if vc is not None:
            parts.append(f"火山 ¥{vc:.2f}")
        elif self.config.get("volcano_ak"):
            parts.append("火山 ...")
        self.icon.title = "  |  ".join(parts) + "  "
        self.icon.update_menu()

    # ── 配置 ──

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

    # ── 数据获取 ──

    def fetch_deepseek(self):
        """获取 DeepSeek 余额"""
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
        except Exception as e: return {"error": f"DS获取失败: {str(e)[:30]}"}

    # ── 火山引擎 SDK ──

    def fetch_volcano(self):
        """获取火山引擎余额（官方 SDK）"""
        ak = self.config.get("volcano_ak", "").strip()
        sk = self.config.get("volcano_sk", "").strip()
        if not ak or not sk: return None  # 未配置不算错误

        try:
            cfg = volcenginesdkcore.Configuration()
            cfg.ak = ak
            cfg.sk = sk
            cfg.region = self.config.get("volcano_region", "cn-beijing")
            cfg.scheme = "https"

            client = volcenginesdkcore.ApiClient(cfg)
            api = volcenginesdkbilling.api.BILLINGApi(client)
            req = volcenginesdkbilling.models.QueryBalanceAcctRequest()
            resp = api.query_balance_acct(req)
            d = resp.to_dict()

            available = float(d.get("available_balance", 0))
            return {"available": available, "error": None}

        except Exception as e:
            msg = str(e)
            if "401" in msg or "SignatureDoesNotMatch" in msg:
                return {"error": "火山AK/SK无效"}
            if "403" in msg:
                return {"error": "火山无权限"}
            return {"error": f"火山获取失败: {msg[:40]}"}

    # ── 更新 ──

    def do_update(self):
        # DeepSeek
        ds_r = self.fetch_deepseek()
        if ds_r.get("error"):
            self.data["error"] = ds_r["error"]
            self.data["ds_available"] = self.data["ds_total"] = self.data["ds_used"] = None
        else:
            self.data["error"] = None
            self.data["ds_available"] = ds_r["available"]
            self.data["ds_total"] = ds_r["total"]
            self.data["ds_used"] = ds_r["used"]

        # 火山引擎
        vc_r = self.fetch_volcano()
        if vc_r is None:
            # 未配置，不动
            pass
        elif vc_r.get("error"):
            # 火山报错只记在火山字段上，不覆盖全局 error
            self.data["volcano_available"] = None
            # 如果当前没有全局 error，用火山 error
            if not self.data.get("error"):
                self.data["error"] = vc_r["error"]
        else:
            self.data["volcano_available"] = vc_r["available"]
            if not self.data.get("error"):
                self.data["error"] = None

        self.data["last_update"] = datetime.now()
        self.refresh_display()

    def update_loop(self):
        time.sleep(2)
        self.do_update()
        interval = max(self.config.get("refresh_interval", 300), 60)
        while not self.stop_event.is_set():
            if self.stop_event.wait(interval): break
            self.do_update()

    # ── 操作 ──

    def on_recharge(self, icon, item):
        """打开 DeepSeek 充值页面（火山引擎暂时不提供内嵌充值）"""
        import webbrowser
        webbrowser.open(DS_RECHARGE_URL)

    def on_settings_ds(self, icon, item):
        old = self.config.get("api_key", "")
        ps = f'''
Add-Type -AssemblyName Microsoft.VisualBasic
$k = [Microsoft.VisualBasic.Interaction]::InputBox("DeepSeek API Key：", "设置 DeepSeek API Key", "{old}")
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

    def on_settings_volcano(self, icon, item):
        ak_old = self.config.get("volcano_ak", "")
        sk_old = self.config.get("volcano_sk", "")
        ps = f'''
Add-Type -AssemblyName Microsoft.VisualBasic
$ak = [Microsoft.VisualBasic.Interaction]::InputBox("火山引擎 Access Key：", "设置 火山引擎 Access Key", "{ak_old}")
if ($ak -eq "") {{ Write-Host "CANCEL"; exit }}
$sk = [Microsoft.VisualBasic.Interaction]::InputBox("火山引擎 Secret Key：", "设置 火山引擎 Secret Key", "{sk_old}")
if ($sk -eq "") {{ Write-Host "CANCEL"; exit }}
Write-Host "$ak|$sk"
'''
        try:
            r = subprocess.run(['powershell','-NoProfile','-Command',ps],
                capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            out = r.stdout.strip()
            if out and out != "CANCEL" and "|" in out:
                parts = out.split("|", 1)
                self.config["volcano_ak"] = parts[0].strip()
                self.config["volcano_sk"] = parts[1].strip()
                self.save_config()
                self.do_update()
        except: pass

    def on_refresh(self, icon, item):
        self.do_update()

    def on_exit(self, icon, item):
        self.stop_event.set()
        self.icon.stop()

    def run(self):
        self.icon.run()


if __name__ == "__main__":
    DeepSeekTray().run()
