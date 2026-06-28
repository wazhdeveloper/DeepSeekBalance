# DeepSeek 余额桌面组件 🪙

在 Windows 任务栏显示 DeepSeek API 余额，鼠标悬停查看，左键点击查看详情，内置充值入口。

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🖥️ **任务栏余额图标** | 图标直接显示当前余额数字，颜色随余额变化 |
| 🔍 **鼠标悬停** | 显示精确余额 `¥ 26.46` |
| 👆 **左键点击** | 弹出系统通知，显示可用余额、总额、已用 |
| 👉 **右键菜单** | 刷新 / 充值 / 设置 API Key / 退出 |
| 💳 **内嵌充值** | 在软件内打开 DeepSeek 充值页面，支持支付宝/微信支付 |
| 🔄 **自动刷新** | 每 5 分钟自动更新余额 |
| 🚀 **开机自启** | 开机自动启动（需手动添加快捷方式到启动文件夹） |

## 📸 预览

```
系统托盘区域（右下角）:
┌──────────────────────────┐
│  🔊  🌐  ⌨  26  🔼  16:48 │
│              ↑            │
│       图标显示余额数字      │
└──────────────────────────┘
```

- **🟢 绿色** = 余额充足（>10元）
- **🟡 黄色** = 余额不多（>3元）
- **🔴 红色** = 余额不足（<3元）

## 📦 下载

从 [Releases](../../releases) 页面下载 `DeepSeekBalance.exe`，双击运行即可。

或者自行打包：

```bash
pip install -r requirements.txt
python -m PyInstaller --onefile --noconsole --name "DeepSeekBalance" source/deepseek_widget.py
```

## 🚀 使用

1. 运行 `DeepSeekBalance.exe`（或 `python source/deepseek_widget.py`）
2. 在任务栏找到 ¥ 图标 → **右键** → **设置 API Key**
3. 输入你的 DeepSeek API Key（在 [platform.deepseek.com](https://platform.deepseek.com/api_keys) 创建）
4. 保存后自动显示余额 ✅

### 开机自启

将 `DeepSeekBalance.exe` 的快捷方式放入：
- 按 `Win + R`，输入 `shell:startup`
- 把快捷方式粘贴进去

## 🔧 配置文件

配置文件保存在 `%LOCALAPPDATA%\DeepSeekBalance\deepseek_config.json`

```json
{
  "api_key": "sk-xxxxxxxxxxxx",
  "refresh_interval": 300
}
```

- `api_key`: 你的 DeepSeek API Key
- `refresh_interval`: 自动刷新间隔（秒），默认 300（5 分钟），最低 60

## 📋 依赖

- Python 3.8+
- [requests](https://pypi.org/project/requests/) — HTTP 请求
- [Pillow](https://pypi.org/project/Pillow/) — 图标渲染
- [pystray](https://pypi.org/project/pystray/) — 系统托盘
- [pywebview](https://pypi.org/project/pywebview/) — 内嵌充值浏览器（可选，仅充值功能需要）

## 🏗️ 项目结构

```
DeepSeekBalance/
├── README.md
├── .gitignore
├── requirements.txt
├── source/
│   ├── deepseek_widget.py      # 主程序
│   └── deepseek_recharge.pyw   # 充值浏览器窗口
└── dist/
    └── DeepSeekBalance.exe     # 编译好的可执行文件
```

## 📄 许可证

MIT License
