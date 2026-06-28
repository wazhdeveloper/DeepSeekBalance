"""DeepSeek 充值 - 独立内嵌浏览器窗口"""
import sys, os
try:
    import webview
    webview.create_window("DeepSeek 充值", "https://platform.deepseek.com/top_up",
                          width=520, height=720, resizable=True)
    webview.start()
except:
    os._exit(1)
