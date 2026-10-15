#!/usr/bin/env python3
"""國高中盃 即時查詢伺服器（單一檔案：提供網頁 + 代為讀取即時戰況）
用法：把本檔與 HTML 放同一資料夾 → 雙擊或執行 python live_server.py
      電腦開 http://localhost:8765 ；手機（同一個 Wi-Fi）開畫面上印出的「手機網址」。
"""
import http.server, urllib.request, os, glob, socket, time, threading, webbrowser
API = "http://172.105.210.232/liveresultst/proxy_st.php"
CLOUD = bool(os.environ.get('PORT'))   # 雲端平台會提供 PORT 環境變數
PORT = int(os.environ.get('PORT', 8765))
CACHE_SEC = 8          # 多人同時查詢時，8 秒內共用同一份資料，減輕主辦伺服器負擔
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
_cache = {}; _lock = threading.Lock()

def html_name():
    for n in glob.glob("*.html"):
        if "選手可搜尋明細" in n: return n
    return (glob.glob("*.html") or [None])[0]

def fetch_api(body):
    with _lock:
        hit = _cache.get(body)
        if hit and time.time() - hit[0] < CACHE_SEC: return hit[1]
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "text/plain;charset=UTF-8"})
    data = urllib.request.urlopen(req, timeout=20).read()
    with _lock: _cache[body] = (time.time(), data)
    return data

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path in ("/", ""):
            self.send_response(302); self.send_header("Location", "/" + urllib.request.quote(html_name())); self.end_headers(); return
        super().do_GET()
    def do_POST(self):
        if self.path.split("?")[0] != "/proxy": self.send_error(404); return
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        try:
            data = fetch_api(body)
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data)
        except Exception as e:
            self.send_error(502, str(e))

def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except Exception: return "（查不到，請用 ipconfig 查 IPv4）"
    finally: s.close()

if __name__ == "__main__":
    if not html_name(): raise SystemExit("找不到 HTML，請與本檔放同一資料夾")
    if CLOUD: print(f"cloud mode, port {PORT}")
    else:
        print("=" * 52); print(" 國高中盃 即時查詢 已啟動（關閉此視窗即停止）"); print("=" * 52)
        print(f" 電腦：http://localhost:{PORT}"); print(f" 手機：http://{lan_ip()}:{PORT}   （手機需連同一個 Wi-Fi）")
        print(" 若手機連不上：Windows 防火牆跳出視窗時請按「允許存取」。\n")
        threading.Timer(1, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    http.server.ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
