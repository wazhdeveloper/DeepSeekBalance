# DeepSeek + 火山引擎 余额桌面组件 🪙

在 Windows 任务栏同时显示 DeepSeek API 余额和火山引擎余额，鼠标悬停/点击查看双平台详情。

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🖥️ **任务栏余额图标** | 图标显示 DeepSeek 余额数字，颜色取两者中较低值 |
| 🔍 **鼠标悬停** | 显示 `DS ¥XX.XX \| 火山 ¥XX.XX` |
| 👆 **左键点击** | 弹出系统通知，显示双平台可用余额、总额、已用 |
| 👉 **右键菜单** | DeepSeek / 火山引擎余额一目了然，可分别设置密钥 |
| 🔄 **自动刷新** | 每 5 分钟自动更新双平台余额 |
| 🎨 **颜色提示** | 基于较低余额变色 |
| 🚀 **开机自启** | 开机自动启动（需手动添加快捷方式到启动文件夹） |

## 📸 预览

```
系统托盘区域（右下角）:
┌──────────────────────────────────┐
│  🔊  🌐  ⌨  26  🔼  16:48       │
│              ↑                   │
│       图标显示 DeepSeek 余额数字   │
│       悬停提示双平台余额           │
└──────────────────────────────────┘
```

### 右键菜单

```
┌─────────────────────────────┐
│ DeepSeek  ¥ 26.46           │  ← 实时余额
│ 火山引擎  ¥ 10.00           │  ← 实时余额
│ ─────────────────           │
│ 充值 (DeepSeek)             │
│ ─────────────────           │
│ 刷新                        │
│ 设置 DeepSeek API Key       │
│ 设置 火山引擎 AK/SK         │
│ ─────────────────           │
│ 退出                        │
└─────────────────────────────┘
```

- **🟢 绿色** = 余额充足（两者均 >10元）
- **🟡 黄色** = 余额偏低（任一 <10元）
- **🔴 红色** = 余额不足（任一 <3元）

## 📦 下载

从 [Releases](../../releases) 页面下载 `DeepSeekBalance.exe`，双击运行即可。

或者自行打包：

```bash
pip install -r requirements.txt
python -m PyInstaller --onefile --noconsole --name "DeepSeekBalance" source/deepseek_widget.py
```

## 🚀 使用

1. 运行 `DeepSeekBalance.exe`（或 `python source/deepseek_widget.py`）
2. 在任务栏找到 ¥ 图标 → **右键** → **设置 DeepSeek API Key**
3. 输入你的 DeepSeek API Key（在 [platform.deepseek.com](https://platform.deepseek.com/api_keys) 创建）
4. 可选：**右键 → 设置 火山引擎 AK/SK**，输入火山引擎 Access Key 和 Secret Key（在[火山引擎控制台](https://console.volcengine.com/iam/keypair/)创建）
5. 保存后自动显示双平台余额 ✅

### 开机自启

将 `DeepSeekBalance.exe` 的快捷方式放入：
- 按 `Win + R`，输入 `shell:startup`
- 把快捷方式粘贴进去

## 🔧 配置文件

配置文件保存在 `%LOCALAPPDATA%\DeepSeekBalance\deepseek_config.json`

```json
{
  "api_key": "sk-xxxxxxxxxxxx",
  "refresh_interval": 300,
  "volcano_ak": "AKLTxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "volcano_sk": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "volcano_region": "cn-beijing"
}
```

- `api_key`: 你的 DeepSeek API Key
- `refresh_interval`: 自动刷新间隔（秒），默认 300（5 分钟），最低 60
- `volcano_ak`: 火山引擎 Access Key（可选）
- `volcano_sk`: 火山引擎 Secret Key（可选）
- `volcano_region`: 火山引擎区域（默认 `cn-beijing`）

## 📋 依赖

- Python 3.8+
- [requests](https://pypi.org/project/requests/) — HTTP 请求
- [Pillow](https://pypi.org/project/Pillow/) — 图标渲染
- [pystray](https://pypi.org/project/pystray/) — 系统托盘
- [volcengine-python-sdk](https://pypi.org/project/volcengine-python-sdk/) — 火山引擎 SDK（查询余额用）
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
