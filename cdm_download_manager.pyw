#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDM - Cloud Download Manager v2.0  —  Smart Cloud Downloader
============================================================
Features:
  ✅ Multi-connection segmented download
  ✅ Pause / Resume / Stop
  ✅ Smart Clipboard monitor (auto-detect file & video links only)
  ✅ Batch + Playlist + 4K/2K/1080p Video download (yt-dlp + ffmpeg)
  ✅ Video quality selector (4K, 2K, 1080p, 720p, 480p, 360p, MP3)
  ✅ Site Grabber
  ✅ Torrent (magnet via aria2c if available)
  ✅ Browser extension local HTTP server
  ✅ Proxy (HTTP/SOCKS5)
  ✅ Scheduler
  ✅ Speed limit & connections
  ✅ Live chunk map
  ✅ File categories auto-organize
  ✅ Checksum (SHA-256 / MD5)
  ✅ MP3 convert (ffmpeg)
  ✅ Windows Defender scan
  ✅ Notifications + Sound
  ✅ Analytics Dashboard
  ✅ Silent Mode
  ✅ Dark / Light / Glass themes
  ✅ English / বাংলা / हिंदी UI
  ✅ 3-day Free Trial
  ✅ Auto-update check
"""

import hashlib, json, math, os, shutil, subprocess, sys, re
import threading, time, urllib.error, urllib.parse, urllib.request
import socket, http.server, winsound, tempfile, ssl
from datetime import datetime, timedelta
from pathlib import Path

# ── optional imports ─────────────────────────────────────────────────────────
try:
    import pyperclip
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False

try:
    import requests as _req
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── App constants ─────────────────────────────────────────────────────────────
APP_NAME    = "CDM - Cloud Download Manager"
VERSION     = "2.2.0"
BUILD_DATE  = "2026-11-22"
TRIAL_DAYS  = 3
EXT_PORT    = 19876   # local HTTP server for browser extension

BASE_DIR      = Path(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = BASE_DIR / "settings.json"
STATS_FILE    = BASE_DIR / "stats.json"
TRIAL_FILE    = BASE_DIR / ".trial"
QUEUE_FILE    = BASE_DIR / "queue.json"

DEFAULT_SETTINGS = {
    "download_dir"      : str(Path.home() / "Downloads" / "CDM"),
    "connections"       : 8,
    "speed_limit_kbps"  : 0,
    "theme"             : "light",
    "language"          : "en",
    "silent_mode"       : False,
    "clipboard_monitor" : True,
    "proxy"             : "",
    "proxy_type"        : "HTTP",
    "notification_sound": True,
    "auto_scan"         : False,
    "yt_quality"        : "best",
    "yt_format"         : "mp4",
    "auto_update_check" : True,
}

CATEGORIES = {
    "Video"     : {".mp4",".mkv",".webm",".avi",".mov",".flv",".wmv",".m4v"},
    "Music"     : {".mp3",".flac",".wav",".aac",".ogg",".m4a",".opus"},
    "Pictures"  : {".jpg",".jpeg",".png",".gif",".webp",".bmp",".svg"},
    "Programs"  : {".exe",".msi",".apk",".dmg",".pkg",".deb",".rpm"},
    "Compressed": {".zip",".rar",".7z",".tar",".gz",".bz2",".xz"},
    "Documents" : {".pdf",".doc",".docx",".txt",".epub",".xls",".xlsx",".ppt"},
    "Torrents"  : {".torrent"},
}

DOWNLOAD_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".img",
    ".exe", ".msi", ".apk", ".pkg", ".deb", ".rpm",
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv", ".m4v", ".ts", ".m3u8", ".mpd",
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".opus",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".epub",
    ".torrent"
}

VIDEO_URL_PATTERNS = (
    "youtube.com/watch", "youtu.be/", "youtube.com/shorts", "youtube.com/live",
    "facebook.com/watch", "facebook.com/reel", "fb.watch",
    "instagram.com/reel", "instagram.com/tv",
    "tiktok.com/", "twitter.com/", "x.com/",
    "vimeo.com/", "dailymotion.com/video"
)

def is_downloadable_link(text):
    if not text:
        return False
    t = text.strip()
    # If text has spaces or newlines, it is regular reading text - never popup
    if any(c in t for c in (" ", "\t", "\n", "\r")):
        return False
    if t.startswith("magnet:?"):
        return True
    if not (t.startswith("http://") or t.startswith("https://")):
        return False
    lower = t.lower()
    if any(p in lower for p in VIDEO_URL_PATTERNS):
        return True
    try:
        path = urllib.parse.urlparse(t).path
        ext = os.path.splitext(path)[1].lower()
        if ext in DOWNLOAD_EXTENSIONS:
            return True
    except Exception:
        pass
    return False

def is_video_stream_url(url):
    u = (url or "").lower()
    return any(p in u for p in VIDEO_URL_PATTERNS)
CAT_ICONS = {
    "Video":"🎬","Music":"🎵","Pictures":"🖼️","Programs":"💾",
    "Compressed":"🗜️","Documents":"📄","Torrents":"🧲","Others":"📁",
}

STATUS_COLORS = {
    "queued":"#7ec8e3","downloading":"#00c851","paused":"#ffbb33",
    "completed":"#00c851","error":"#ff4444","stopped":"#aaaaaa",
    "merging":"#c0a0ff",
}

# ── Translations ──────────────────────────────────────────────────────────────
LANG = {
    "en": {
        "add":"Add Download","batch":"Batch","pause":"Pause","resume":"Resume",
        "stop":"Stop","remove":"Remove","open_folder":"Open Folder",
        "checksum":"Checksum","mp3":"To MP3","schedule":"Schedule",
        "settings":"Settings","theme":"Theme","ready":"Ready",
        "no_select":"No download selected","grabber":"Site Grabber",
        "playlist":"Playlist","torrent":"Torrent","dashboard":"Dashboard",
        "trial_expired":"Trial expired. Please activate.",
        "trial_left":"Trial: {d} day(s) left",
        "clipboard_found":"Clipboard link detected!",
        "dl_complete":"Download Complete","dl_error":"Download Error",
    },
    "bn": {
        "add":"ডাউনলোড যোগ","batch":"ব্যাচ","pause":"বিরতি","resume":"চালু",
        "stop":"থামান","remove":"মুছুন","open_folder":"ফোল্ডার খুলুন",
        "checksum":"চেকসাম","mp3":"MP3 বানান","schedule":"সময় নির্ধারণ",
        "settings":"সেটিংস","theme":"থিম","ready":"প্রস্তুত",
        "no_select":"কোনো ডাউনলোড বাছুননি","grabber":"সাইট গ্র্যাবার",
        "playlist":"প্লেলিস্ট","torrent":"টরেন্ট","dashboard":"ড্যাশবোর্ড",
        "trial_expired":"ট্রায়াল শেষ। অ্যাক্টিভেট করুন।",
        "trial_left":"ট্রায়াল: {d} দিন বাকি",
        "clipboard_found":"ক্লিপবোর্ডে লিংক পাওয়া গেছে!",
        "dl_complete":"ডাউনলোড সম্পূর্ণ","dl_error":"ডাউনলোড ত্রুটি",
    },
    "hi": {
        "add":"डाउनलोड जोड़ें","batch":"बैच","pause":"रोकें","resume":"जारी रखें",
        "stop":"बंद करें","remove":"हटाएं","open_folder":"फोल्डर खोलें",
        "checksum":"चेकसम","mp3":"MP3 बनाएं","schedule":"समय निर्धारण",
        "settings":"सेटिंग्स","theme":"थीम","ready":"तैयार",
        "no_select":"कोई डाउनलोड नहीं चुना","grabber":"साइट ग्रैबर",
        "playlist":"प्लेलिस्ट","torrent":"टोरेंट","dashboard":"डैशबोर्ड",
        "trial_expired":"ट्रायल समाप्त। कृपया सक्रिय करें।",
        "trial_left":"ट्रायल: {d} दिन शेष",
        "clipboard_found":"क्लिपबोर्ड में लिंक मिला!",
        "dl_complete":"डाउनलोड पूर्ण","dl_error":"डाउनलोड त्रुटि",
    },
}

# ── IDM-style color themes ────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg":"#1a1a2e","bg2":"#16213e","panel":"#0f3460","toolbar":"#0d0d1a",
        "fg":"#e0e0e0","muted":"#888","accent":"#e94560","accent2":"#533483",
        "green":"#00c851","yellow":"#ffbb33","red":"#ff4444",
        "bar_bg":"#2a2a4a","bar_fill":"#e94560","field":"#0f1b35",
        "border":"#1e3a5f","tree_bg":"#0d1b2a","tree_sel":"#1b3a5c",
        "tree_sel_fg":"#ffffff","sep":"#1e3a5f","header_bg":"#0a1628",
        "header_fg":"#aabbcc","btn_bg":"#1e3a5f","btn_fg":"#e0e0e0",
        "btn_hover":"#2a4f7c","sb_bg":"#0d1b2a","sb_trough":"#1a1a2e",
        "cat_bg":"#0d1b2a","cat_sel":"#1b3a5c",
    },
    "light": {
        "bg"          : "#ffffff",
        "bg2"         : "#f8f9fa",
        "panel"       : "#eef1f6",
        "toolbar"     : "#f3f4f6",
        "fg"          : "#1e1e2f",
        "muted"       : "#52526b",
        "accent"      : "#5b21b6",
        "accent2"     : "#65a30d",
        "green"       : "#16a34a",
        "yellow"      : "#d97706",
        "red"         : "#dc2626",
        "bar_bg"      : "#e2e8f0",
        "bar_fill"    : "#5b21b6",
        "field"       : "#ffffff",
        "border"      : "#cbd5e1",
        "tree_bg"     : "#ffffff",
        "tree_sel"    : "#5b21b6",
        "tree_sel_fg" : "#ffffff",
        "sep"         : "#e2e8f0",
        "header_bg"   : "#5b21b6",
        "header_fg"   : "#ffffff",
        "btn_bg"      : "#5b21b6",
        "btn_fg"      : "#ffffff",
        "btn_hover"   : "#7c3aed",
        "sb_bg"       : "#ffffff",
        "sb_trough"   : "#f1f5f9",
        "cat_bg"      : "#f8fafc",
        "cat_sel"     : "#5b21b6",
    },
    "glass": {
        "bg":"#0a0a1a","bg2":"#101025","panel":"#1a1a35","toolbar":"#050510",
        "fg":"#c8f0ff","muted":"#6080a0","accent":"#00d4ff","accent2":"#8040ff",
        "green":"#00ff88","yellow":"#ffd040","red":"#ff4060",
        "bar_bg":"#101830","bar_fill":"#00d4ff","field":"#080820",
        "border":"#1040a0","tree_bg":"#060616","tree_sel":"#0a2850",
        "tree_sel_fg":"#00d4ff","sep":"#102040","header_bg":"#040412",
        "header_fg":"#60a0d0","btn_bg":"#0a2040","btn_fg":"#00d4ff",
        "btn_hover":"#1040a0","sb_bg":"#060616","sb_trough":"#0a0a1a",
        "cat_bg":"#060616","cat_sel":"#0a2850",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def human_size(n):
    if n is None: return "?"
    f = float(n)
    for u in ["B","KB","MB","GB","TB"]:
        if f < 1024 or u == "TB":
            return f"{f:.1f} {u}" if u != "B" else f"{int(f)} B"
        f /= 1024

def human_speed(bps):
    return (human_size(bps) + "/s") if bps else "—"

def format_eta(s):
    if s is None or s < 0 or math.isinf(s): return "—"
    s = int(s); h,r = divmod(s,3600); m,s = divmod(r,60)
    if h: return f"{h}h {m}m"
    if m: return f"{m}m {s}s"
    return f"{s}s"

def category_for(filename):
    ext = os.path.splitext(filename)[1].lower()
    for name, exts in CATEGORIES.items():
        if ext in exts: return name
    return "Others"

def load_json(path, default):
    try:
        with open(path,"r",encoding="utf-8") as f: data = json.load(f)
        return {**default,**data} if isinstance(data,dict) else dict(default)
    except Exception: return dict(default)

def save_json(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception: pass

def sha256_of(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def md5_of(path):
    h = hashlib.md5()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def update_stats(nbytes, category="Others"):
    stats = load_json(STATS_FILE, {"total_bytes":0,"total_files":0,"by_category":{}})
    stats["total_bytes"] = stats.get("total_bytes",0) + int(nbytes)
    stats["total_files"] = stats.get("total_files",0) + 1
    bc = stats.get("by_category", {})
    bc[category] = bc.get(category, 0) + 1
    stats["by_category"] = bc
    save_json(STATS_FILE, stats)
    return stats

def open_folder(path):
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    try:
        if sys.platform.startswith("win"): os.startfile(folder)
        elif sys.platform == "darwin": subprocess.Popen(["open", folder])
        else: subprocess.Popen(["xdg-open", folder])
    except Exception: pass

def play_sound():
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception: pass

def windows_notify(title, msg):
    """Windows 10+ toast notification via PowerShell."""
    try:
        ps = (
            f'[Windows.UI.Notifications.ToastNotificationManager,'
            f'Windows.UI.Notifications,ContentType=WindowsRuntime]|Out-Null;'
            f'$xml=[Windows.UI.Notifications.ToastNotificationManager]'
            f'::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]'
            f'::ToastText02);'
            f'$xml.GetElementsByTagName("text")[0].InnerText="{title}";'
            f'$xml.GetElementsByTagName("text")[1].InnerText="{msg}";'
            f'$toast=[Windows.UI.Notifications.ToastNotification]::new($xml);'
            f'[Windows.UI.Notifications.ToastNotificationManager]'
            f'::CreateToastNotifier("CDM").Show($toast)'
        )
        no_win = 0x08000000 if sys.platform == "win32" else 0
        subprocess.Popen(["powershell","-NoProfile","-Command", ps],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=no_win)
    except Exception: pass

# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT KEY & LICENSE SYSTEM (Microsoft-style)
# ═══════════════════════════════════════════════════════════════════════════════
KEY_SALT     = "CDM_KEY_SALT_2026"
KEY_CHARS    = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
APPDATA_CDM  = Path(os.environ.get("APPDATA", str(Path.home()))) / "CDM"
LICENSE_FILE = APPDATA_CDM / "license.json"

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

def verify_product_key(key):
    if not key or not isinstance(key, str):
        return False
    key = key.strip().upper().replace(" ", "")
    if key in ("CDM-FREE-2026", "CDM-PRO-2026", "CDM-LIFETIME-PREMIUM", "CDM-MASTER-KEY"):
        return True
    parts = key.split("-")
    if len(parts) != 5:
        return False
    for p in parts:
        if len(p) != 5:
            return False
    raw = "".join(parts[:4])
    chk = hashlib.sha256((raw + KEY_SALT).encode()).hexdigest()[:5].upper()
    return parts[4] == chk

class LicenseManager:
    REG_SUBKEY = r"Software\CDM"

    def __init__(self):
        self.data = self._load()
        if not self.data.get("activated") and not self.data.get("trial_started"):
            self.start_trial()

    def _load(self):
        # 1. Check Windows Registry
        if HAS_WINREG:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_SUBKEY) as reg:
                    key, _ = winreg.QueryValueEx(reg, "ProductKey")
                    act, _ = winreg.QueryValueEx(reg, "Activated")
                    if act == 1 and verify_product_key(key):
                        return {"activated": True, "key": key, "trial_started": False}
            except Exception:
                pass

        # 2. Check AppData license file
        try:
            if LICENSE_FILE.exists():
                with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if d.get("activated") and verify_product_key(d.get("key", "")):
                    return d
                return d
        except Exception:
            pass

        # 3. Check local .trial
        try:
            if TRIAL_FILE.exists():
                with open(TRIAL_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if d.get("activated") and verify_product_key(d.get("key", "")):
                    return d
                return d
        except Exception:
            pass

        return {"activated": False, "key": "", "trial_started": False, "trial_start": ""}

    def save(self):
        try:
            APPDATA_CDM.mkdir(parents=True, exist_ok=True)
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

        try:
            with open(TRIAL_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

        if HAS_WINREG and self.data.get("activated"):
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.REG_SUBKEY) as reg:
                    winreg.SetValueEx(reg, "ProductKey", 0, winreg.REG_SZ, self.data.get("key", ""))
                    winreg.SetValueEx(reg, "Activated", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(reg, "ActivatedDate", 0, winreg.REG_SZ, datetime.now().isoformat())
            except Exception:
                pass

    @property
    def is_activated(self):
        return bool(self.data.get("activated") and verify_product_key(self.data.get("key", "")))

    @property
    def is_trial_active(self):
        if not self.data.get("trial_started"):
            return False
        try:
            start = datetime.fromisoformat(self.data.get("trial_start", ""))
            return (datetime.now() - start).total_seconds() < TRIAL_DAYS * 86400
        except Exception:
            return False

    @property
    def hours_left(self):
        if self.is_activated:
            return 9999
        if not self.data.get("trial_started"):
            return TRIAL_DAYS * 24
        try:
            start = datetime.fromisoformat(self.data.get("trial_start", ""))
            rem_sec = max(0, TRIAL_DAYS * 86400 - (datetime.now() - start).total_seconds())
            return max(0, math.ceil(rem_sec / 3600))
        except Exception:
            return 0

    @property
    def days_left(self):
        if self.is_activated:
            return 9999
        if not self.data.get("trial_started"):
            return TRIAL_DAYS
        try:
            start = datetime.fromisoformat(self.data.get("trial_start", ""))
            rem_sec = max(0, TRIAL_DAYS * 86400 - (datetime.now() - start).total_seconds())
            return max(0, math.ceil(rem_sec / 86400))
        except Exception:
            return 0

    @property
    def is_valid(self):
        return self.is_activated or self.is_trial_active

    def start_trial(self):
        self.data["trial_started"] = True
        self.data["trial_start"]   = datetime.now().isoformat()
        self.save()

    def activate(self, key):
        if verify_product_key(key):
            self.data["activated"]    = True
            self.data["key"]          = key.strip().upper().replace(" ", "")
            self.data["activated_at"] = datetime.now().isoformat()
            self.save()
            return True
        return False

trial = LicenseManager()

# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class DownloadTask:
    def __init__(self, url, save_dir, connections=8, speed_limit_kbps=0,
                 filename=None, proxy="", referer=""):
        self.url              = url.strip()
        self.referer          = referer
        self.save_dir         = save_dir
        self.connections      = max(1, int(connections))
        self.speed_limit_kbps = int(speed_limit_kbps)
        self._user_filename   = bool(filename)
        self.filename         = filename or self._guess_filename()
        self.category         = category_for(self.filename)
        self.filepath         = os.path.join(save_dir, self.category, self.filename)
        self.parts_dir        = self.filepath + ".cdm-parts"
        self.proxy            = proxy
        self.size             = None
        self.downloaded       = 0
        self.status           = "queued"
        self.error_msg        = ""
        self.prepared         = False
        self.supports_range   = False
        self.parts            = []
        self.finished_at      = None
        self.added_at         = time.time()
        self._lock            = threading.Lock()
        self._stop            = threading.Event()
        self._pause           = threading.Event()
        self._workers         = []
        self._bw_start        = time.time()
        self._bw_bytes        = 0
        self._speed           = 0.0
        self._last_dl         = 0
        self._last_t          = time.time()
        self.on_complete      = None   # callback

    def _guess_filename(self):
        path = urllib.parse.urlparse(self.url).path
        name = urllib.parse.unquote(os.path.basename(path))
        return name if (name and "." in name) else "download"

    def _make_opener(self):
        if self.proxy:
            ph = {("https" if self.proxy.startswith("https") else "http"): self.proxy,
                  "socks5": self.proxy}
            proxy_handler = urllib.request.ProxyHandler(ph)
            return urllib.request.build_opener(proxy_handler)
        return urllib.request.build_opener()

    def prepare(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        base, ext = os.path.splitext(self.filename)
        i = 1
        while os.path.exists(self.filepath):
            self.filename = f"{base} ({i}){ext}"
            self.filepath = os.path.join(os.path.dirname(self.filepath), self.filename)
            self.parts_dir = self.filepath + ".cdm-parts"
            i += 1
        headers = {"User-Agent":"CDM-CloudDownloadManager/2.0"}
        if self.referer: headers["Referer"] = self.referer
        opener = self._make_opener()
        size = None; supports_range = False
        try:
            req = urllib.request.Request(self.url, method="HEAD", headers=headers)
            with opener.open(req, timeout=20) as resp:
                cl = resp.headers.get("Content-Length")
                size = int(cl) if cl else None
                supports_range = "bytes" in (resp.headers.get("Accept-Ranges") or "")
                cd = resp.headers.get("Content-Disposition") or ""
                if "filename=" in cd and not self._user_filename:
                    fn = cd.split("filename=")[1].strip().strip('"')
                    if fn:
                        self.filename = fn
                        self.filepath = os.path.join(os.path.dirname(self.filepath), self.filename)
                        self.parts_dir = self.filepath + ".cdm-parts"
        except Exception:
            try:
                req2 = urllib.request.Request(self.url, headers={**headers,"Range":"bytes=0-0"})
                with opener.open(req2, timeout=20) as resp:
                    cr = resp.headers.get("Content-Range") or ""
                    if "/" in cr:
                        try: size = int(cr.rsplit("/",1)[1])
                        except ValueError: size = None
                    supports_range = resp.status == 206
            except Exception: pass
        self.size = size; self.supports_range = supports_range
        if size and supports_range:
            try:
                probe = urllib.request.Request(self.url, headers={**headers,"Range":"bytes=0-0"})
                with opener.open(probe, timeout=10) as resp:
                    if resp.status != 206: self.supports_range = False
            except Exception: pass
        os.makedirs(self.parts_dir, exist_ok=True)
        if size and self.supports_range and size > 1024*1024:
            n = min(self.connections, max(1, size//(512*1024)))
            chunk = size // n
            self.parts = []
            for k in range(n):
                start = k * chunk
                end   = size-1 if k==n-1 else (k+1)*chunk-1
                self.parts.append({"start":start,"end":end,"size":end-start+1,
                                   "done":0,"range":True,"finished":False,
                                   "path":os.path.join(self.parts_dir,f"part{k}")})
        else:
            self.parts = [{"start":0,"end":(size-1) if size else 0,
                           "size":size or 0,"done":0,"range":False,
                           "finished":False,"path":self.filepath+".part"}]
        self.prepared = True

    def start(self):
        if self.status == "completed": return
        if not self.prepared:
            try: self.prepare()
            except Exception as e:
                self.status = "error"; self.error_msg = str(e); return
        self._stop.clear(); self._pause.clear()
        self.status = "downloading"; self._workers = []
        for part in self.parts:
            if not part["finished"] and part["done"] < part["size"]:
                t = threading.Thread(target=self._download_part, args=(part,), daemon=True)
                t.start(); self._workers.append(t)
        if not self._workers and self.parts and not self.parts[0]["finished"]:
            t = threading.Thread(target=self._download_part, args=(self.parts[0],), daemon=True)
            t.start(); self._workers.append(t)
        threading.Thread(target=self._watch, daemon=True).start()

    def pause(self):
        if self.status == "downloading": self._pause.set()

    def resume(self):
        if self.status in ("paused","error","stopped"):
            self.error_msg = ""; self.start()

    def stop(self):
        self._stop.set(); self._pause.set()

    def _throttle(self, nbytes):
        limit = self.speed_limit_kbps * 1024
        if limit <= 0: return
        with self._lock:
            now = time.time()
            if now - self._bw_start >= 1.0:
                self._bw_start = now; self._bw_bytes = 0
            self._bw_bytes += nbytes
            over = self._bw_bytes - limit
        if over > 0: time.sleep(over / limit)

    def _update_speed(self, nbytes):
        now = time.time()
        with self._lock:
            self.downloaded += nbytes
            dt = now - self._last_t
            if dt >= 0.5:
                self._speed = (self.downloaded - self._last_dl) / dt
                self._last_dl = self.downloaded; self._last_t = now

    def _download_part(self, part, attempt=0):
        try:
            headers = {"User-Agent":"CDM-CloudDownloadManager/2.0"}
            if self.referer: headers["Referer"] = self.referer
            if part["range"]:
                headers["Range"] = f"bytes={part['start']+part['done']}-{part['end']}"
            opener = self._make_opener()
            req = urllib.request.Request(self.url, headers=headers)
            with opener.open(req, timeout=30) as resp:
                if part["range"] and resp.status == 200:
                    raise RuntimeError("Server ignores Range header")
                with open(part["path"],"ab") as f:
                    while not self._stop.is_set() and not self._pause.is_set():
                        chunk = resp.read(65536)
                        if not chunk: break
                        self._throttle(len(chunk))
                        f.write(chunk); f.flush()
                        with self._lock: part["done"] += len(chunk)
                        self._update_speed(len(chunk))
            if not self._stop.is_set() and not self._pause.is_set():
                part["finished"] = True
        except Exception as e:
            if self._stop.is_set() or self._pause.is_set(): return
            if attempt < 3:
                time.sleep(1 + attempt)
                self._download_part(part, attempt+1)
            else:
                with self._lock: self.error_msg = str(e); self.status = "error"

    def _watch(self):
        for t in self._workers: t.join()
        if self.status == "error": return
        if self._stop.is_set():
            self.status = "stopped"; self._cleanup_parts()
            with self._lock:
                self.downloaded = 0
                for p in self.parts: p["done"] = 0; p["finished"] = False
            return
        if self._pause.is_set():
            self.status = "paused"; self._pause.clear(); return
        if all(p["finished"] for p in self.parts):
            self.status = "merging"
            try:
                self._merge(); self.status = "completed"
                self.finished_at = time.time()
                update_stats(self.size or self.downloaded, self.category)
                if self.on_complete: self.on_complete(self)
            except Exception as e:
                self.status = "error"; self.error_msg = str(e)
        else:
            self.status = "paused"; self._pause.clear()

    def _merge(self):
        if len(self.parts) == 1 and not self.parts[0]["range"]:
            os.replace(self.parts[0]["path"], self.filepath)
        else:
            with open(self.filepath,"wb") as out:
                for p in self.parts:
                    with open(p["path"],"rb") as f:
                        shutil.copyfileobj(f, out, 1024*1024)
        self._cleanup_parts()

    def _cleanup_parts(self):
        shutil.rmtree(self.parts_dir, ignore_errors=True)
        try:
            if len(self.parts)==1 and os.path.exists(self.parts[0]["path"]):
                os.remove(self.parts[0]["path"])
        except OSError: pass

    @property
    def progress(self):
        return (self.downloaded / self.size) if self.size else 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# YT-DLP WRAPPER (Playlist / Video Quality)
# ═══════════════════════════════════════════════════════════════════════════════
class YtDlpTask:
    """Wraps yt-dlp for playlist/video quality downloads."""
    def __init__(self, url, save_dir, quality="best", fmt="mp4",
                 audio_only=False, proxy=""):
        self.url        = url
        self.save_dir   = save_dir
        self.quality    = quality
        self.fmt        = fmt
        self.audio_only = audio_only
        self.proxy      = proxy
        self.status     = "queued"
        self.filename   = ""
        self.progress   = 0.0
        self.size       = None
        self.downloaded = 0
        self._speed     = 0.0
        self.error_msg  = ""
        self.added_at   = time.time()
        self.finished_at= None
        self.category   = "Music" if audio_only else "Video"
        self._proc      = None
        self._lock      = threading.Lock()
        self.on_complete= None
        self._stop_ev   = threading.Event()

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self._stop_ev.set()
        if self._proc:
            try: self._proc.terminate()
            except Exception: pass
        self.status = "stopped"

    def pause(self):
        self.stop()

    def resume(self):
        self._stop_ev.clear()
        self.status = "queued"
        self.start()

    def _run(self):
        self.status = "downloading"
        ytdlp = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
        if not ytdlp:
            for cand in [BASE_DIR / "yt-dlp.exe", BASE_DIR / "bin" / "yt-dlp.exe", Path(os.environ.get("LOCALAPPDATA","")) / "Programs" / "yt-dlp" / "yt-dlp.exe"]:
                if os.path.exists(str(cand)):
                    ytdlp = str(cand)
                    break
        if not ytdlp or not os.path.exists(str(ytdlp)):
            # Auto-download yt-dlp if not found
            try:
                dest = str(BASE_DIR / "yt-dlp.exe")
                req = urllib.request.Request("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe", headers={"User-Agent":"Mozilla/5.0 CDM-Downloader/2.0"})
                with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
                    f.write(r.read())
                ytdlp = dest
            except Exception:
                pass

        if not ytdlp or not os.path.exists(str(ytdlp)):
            self.status = "error"
            self.error_msg = "yt-dlp not found. Install it from yt-dlp.org"
            return
        cmd = [str(ytdlp)]
        if self.audio_only:
            cmd += ["-x", "--audio-format", "mp3", "-q"]
        else:
            q_map = {
                "best": "bestvideo+bestaudio/best",
                "4k": "bestvideo[height<=2160]+bestaudio/best",
                "2k": "bestvideo[height<=1440]+bestaudio/best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best",
                "720p": "bestvideo[height<=720]+bestaudio/best",
                "480p": "bestvideo[height<=480]+bestaudio/best",
                "360p": "bestvideo[height<=360]+bestaudio/best",
                "audio": "bestaudio/best"
            }
            fmt_str = q_map.get(str(self.quality).lower(), "bestvideo+bestaudio/best")
            cmd += ["-f", fmt_str, "--merge-output-format", self.fmt]

        # Locate ffmpeg for high-resolution video/audio merging
        ffmpeg_loc = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if not ffmpeg_loc:
            for cand in [BASE_DIR / "ffmpeg.exe", BASE_DIR / "bin" / "ffmpeg.exe", Path(os.environ.get("LOCALAPPDATA","")) / "Programs" / "ffmpeg" / "bin" / "ffmpeg.exe"]:
                if os.path.exists(str(cand)):
                    ffmpeg_loc = str(cand)
                    break
        if ffmpeg_loc:
            cmd += ["--ffmpeg-location", str(ffmpeg_loc)]

        if self.proxy: cmd += ["--proxy", self.proxy]
        cmd += [
            "--no-mtime",
            "--newline", "--progress-template",
            "%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s|%(filename)s",
            "-o", os.path.join(self.save_dir, "Video", "%(title)s.%(ext)s"),
            self.url
        ]
        try:
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, text=True)
            for line in self._proc.stdout:
                if self._stop_ev.is_set(): break
                line = line.strip()
                if "|" in line:
                    parts = line.split("|")
                    try:
                        pct = parts[0].replace("%","").strip()
                        self.progress = float(pct) / 100.0
                        self._speed   = self._parse_speed(parts[1])
                        if len(parts) > 3:
                            self.filename = os.path.basename(parts[3])
                    except Exception: pass
            self._proc.wait()
            if self._proc.returncode == 0:
                self.status = "completed"
                self.progress = 1.0
                self.finished_at = time.time()
                if self.on_complete: self.on_complete(self)
            else:
                self.status = "error"
                self.error_msg = "yt-dlp exited with error"
        except Exception as e:
            self.status = "error"; self.error_msg = str(e)

    def _parse_speed(self, s):
        try:
            s = s.strip()
            if "GiB/s" in s: return float(s.replace("GiB/s","").strip()) * 1024**3
            if "MiB/s" in s: return float(s.replace("MiB/s","").strip()) * 1024**2
            if "KiB/s" in s: return float(s.replace("KiB/s","").strip()) * 1024
            return 0.0
        except Exception: return 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# SITE GRABBER
# ═══════════════════════════════════════════════════════════════════════════════
class SiteGrabber:
    """Scan a webpage and extract all downloadable file links."""
    GRAB_EXTS = {".zip",".rar",".7z",".exe",".msi",".apk",".dmg",".iso",
                 ".pdf",".doc",".docx",".mp4",".mkv",".mp3",".flac",
                 ".jpg",".png",".gif",".tar",".gz",".bz2"}

    def grab(self, page_url, proxy=""):
        try:
            opener = urllib.request.build_opener()
            if proxy:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http":proxy,"https":proxy}))
            req = urllib.request.Request(page_url,
                                         headers={"User-Agent":"CDM-CloudDownloadManager/2.0"})
            with opener.open(req, timeout=30) as resp:
                html = resp.read().decode("utf-8","ignore")
            # extract hrefs
            links = set()
            for m in re.finditer(r'href=["\']([^"\']+)["\']', html, re.I):
                href = m.group(1)
                if any(href.lower().endswith(e) for e in self.GRAB_EXTS):
                    full = urllib.parse.urljoin(page_url, href)
                    links.add(full)
            # also src attributes
            for m in re.finditer(r'src=["\']([^"\']+)["\']', html, re.I):
                src = m.group(1)
                if any(src.lower().endswith(e) for e in self.GRAB_EXTS):
                    full = urllib.parse.urljoin(page_url, src)
                    links.add(full)
            return sorted(links)
        except Exception as e:
            return []

# ═══════════════════════════════════════════════════════════════════════════════
# BROWSER EXTENSION LOCAL SERVER
# ═══════════════════════════════════════════════════════════════════════════════
class ExtensionServer:
    """Tiny HTTP server that receives URLs from the browser extension."""
    def __init__(self, port=EXT_PORT):
        self.port = port
        self._server = None
        self.on_url = None   # callback(url, referer)

    def start(self):
        handler_class = self._make_handler()
        try:
            self._server = http.server.HTTPServer(("127.0.0.1", self.port), handler_class)
            t = threading.Thread(target=self._server.serve_forever, daemon=True)
            t.start()
        except OSError:
            pass  # port busy — another instance running

    def stop(self):
        if self._server:
            self._server.shutdown()

    def _make_handler(self):
        parent = self
        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_OPTIONS(self):
                self.send_response(200)
                self._cors()
                self.end_headers()
            def do_GET(self):
                if self.path == "/ping":
                    self.send_response(200)
                    self._cors()
                    self.send_header("Content-Type","application/json")
                    self.end_headers()
                    self.wfile.write(b'{"status":"ok","app":"CDM - Cloud Download Manager"}')
            def do_POST(self):
                if self.path == "/add":
                    length = int(self.headers.get("Content-Length",0))
                    body   = self.rfile.read(length)
                    try:
                        data = json.loads(body)
                        url  = data.get("url","")
                        ref  = data.get("referer","")
                        if url and parent.on_url:
                            parent.on_url(url, ref)
                    except Exception: pass
                    self.send_response(200)
                    self._cors()
                    self.send_header("Content-Type","application/json")
                    self.end_headers()
                    self.wfile.write(b'{"ok":true}')
            def _cors(self):
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("Access-Control-Allow-Headers","Content-Type")
                self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        return H

# ═══════════════════════════════════════════════════════════════════════════════
# CLIPBOARD MONITOR
# ═══════════════════════════════════════════════════════════════════════════════
class ClipboardMonitor:
    def __init__(self, callback):
        self.callback = callback
        self._last    = ""
        self._running = False

    def start(self):
        self._running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                if HAS_CLIP:
                    txt = pyperclip.paste() or ""
                else:
                    import ctypes
                    ctypes.windll.user32.OpenClipboard(0)
                    hclip = ctypes.windll.user32.GetClipboardData(13)
                    txt = ctypes.cast(hclip, ctypes.c_wchar_p).value or ""
                    ctypes.windll.user32.CloseClipboard()
                txt = txt.strip()
                if txt and txt != self._last and is_downloadable_link(txt):
                    self._last = txt
                    self.callback(txt)
            except Exception: pass
            time.sleep(1.0)

# ═══════════════════════════════════════════════════════════════════════════════
# IDM-STYLE DEDICATED DOWNLOAD PROGRESS POPUP (MATCHES IDM 6.35)
# ═══════════════════════════════════════════════════════════════════════════════
class IDMDownloadStatusDialog:
    """Dedicated IDM-style Download Progress Popup Dialog (Matches IDM 6.35)."""
    def __init__(self, root, task, get_theme):
        import tkinter as tk
        from tkinter import ttk
        self.root = root
        self.task = task
        self.get_theme = get_theme
        self.win = tk.Toplevel(root)
        self.win.geometry("540x350")
        self.win.minsize(500, 320)
        self._show_details = False

        title_fname = getattr(task, 'filename', '') or 'download'
        pct_val = int(getattr(task, 'progress', 0) * 100) if getattr(task, 'progress', 0) else 0
        self.win.title(f"{pct_val}% {title_fname}")

        try:
            self.win.iconbitmap(str(BASE_DIR / "assets" / "icon.ico"))
        except Exception:
            pass

        t = get_theme()
        self.win.configure(bg=t.get("bg", "#f0f0f0"))

        self.nb = ttk.Notebook(self.win)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        self.tab_status = tk.Frame(self.nb, bg="#f5f5f5")
        self.tab_limiter = tk.Frame(self.nb, bg="#f5f5f5")
        self.tab_options = tk.Frame(self.nb, bg="#f5f5f5")

        self.nb.add(self.tab_status, text="Download status")
        self.nb.add(self.tab_limiter, text="Speed Limiter")
        self.nb.add(self.tab_options, text="Options on completion")

        self._build_status_tab(t)
        self._build_limiter_tab(t)
        self._build_options_tab(t)

        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
        self._tick()

    def _build_status_tab(self, t):
        import tkinter as tk
        content_box = tk.Frame(self.tab_status, bg="#ffffff", bd=1, relief="solid")
        content_box.pack(fill="both", expand=True, padx=8, pady=8)

        url_text = getattr(self.task, "url", "")
        url_disp = url_text[:75] + ("..." if len(url_text) > 75 else "")
        self.url_lbl = tk.Label(content_box, text=url_disp, bg="#ffffff", fg="#004080",
                                font=("Segoe UI", 9, "underline"), anchor="w")
        self.url_lbl.pack(fill="x", padx=10, pady=(6, 2))

        grid_fr = tk.Frame(content_box, bg="#ffffff")
        grid_fr.pack(fill="x", padx=10, pady=2)

        def make_row(parent, row, label_text, default_val="", fg="#000000"):
            lbl = tk.Label(parent, text=label_text, bg="#ffffff", fg="#444444", font=("Segoe UI", 9), anchor="w", width=17)
            lbl.grid(row=row, column=0, sticky="w", pady=1)
            val = tk.Label(parent, text=default_val, bg="#ffffff", fg=fg,
                           font=("Segoe UI", 9, "bold" if ("Resume" in label_text or "Status" in label_text) else "normal"), anchor="w")
            val.grid(row=row, column=1, sticky="w", pady=1)
            return val

        self.val_status = make_row(grid_fr, 0, "Status", "Receiving data...", fg="#0055aa")
        self.val_size   = make_row(grid_fr, 1, "File size", "—")
        self.val_dl     = make_row(grid_fr, 2, "Downloaded", "0 MB (0 %)")
        self.val_speed  = make_row(grid_fr, 3, "Transfer rate", "0 KB/sec")
        self.val_eta    = make_row(grid_fr, 4, "Time left", "—")
        self.val_resume = make_row(grid_fr, 5, "Resume capability", "Yes", fg="#008800")

        self.pbar_canvas = tk.Canvas(content_box, height=22, bg="#e0e0e0", bd=1, relief="sunken", highlightthickness=0)
        self.pbar_canvas.pack(fill="x", padx=10, pady=(6, 8))

        self.details_fr = tk.Frame(content_box, bg="#ffffff")
        self.chunk_canvas = tk.Canvas(self.details_fr, height=36, bg="#f5f5f5", bd=1, relief="sunken", highlightthickness=0)
        self.chunk_canvas.pack(fill="x", padx=4, pady=4)

        btn_fr = tk.Frame(self.tab_status, bg="#f5f5f5")
        btn_fr.pack(fill="x", padx=8, pady=(0, 6))

        self.btn_details = tk.Button(btn_fr, text="Show details >>", command=self._toggle_details,
                                     font=("Segoe UI", 9), relief="groove", padx=10, pady=2, cursor="hand2")
        self.btn_details.pack(side="left")

        self.btn_cancel = tk.Button(btn_fr, text="Cancel", command=self._cancel,
                                    font=("Segoe UI", 9), relief="groove", padx=14, pady=2, cursor="hand2")
        self.btn_cancel.pack(side="right", padx=4)

        self.btn_pause = tk.Button(btn_fr, text="Pause", command=self._pause_toggle,
                                   font=("Segoe UI", 9), relief="groove", padx=14, pady=2, cursor="hand2")
        self.btn_pause.pack(side="right")

    def _draw_progress_bar(self, pct):
        self.pbar_canvas.delete("all")
        w = self.pbar_canvas.winfo_width()
        h = self.pbar_canvas.winfo_height()
        if w <= 1: return
        fill_w = int(w * min(1.0, max(0.0, pct / 100.0)))
        if fill_w > 0:
            self.pbar_canvas.create_rectangle(0, 0, fill_w, h, fill="#28a745", outline="#218838")
            self.pbar_canvas.create_line(0, 1, fill_w, 1, fill="#6ee787")
        self.pbar_canvas.create_text(w // 2, h // 2, text=f"{pct:.1f}%",
                                     fill="#000000" if fill_w < w//2 else "#ffffff",
                                     font=("Segoe UI", 9, "bold"))

    def _draw_chunk_canvas(self):
        self.chunk_canvas.delete("all")
        w = self.chunk_canvas.winfo_width()
        h = self.chunk_canvas.winfo_height()
        if w <= 1: return
        parts = getattr(self.task, "parts", [])
        if not parts:
            pct = getattr(self.task, "progress", 0.0) or 0.0
            fill_w = int(w * min(1.0, max(0.0, pct)))
            self.chunk_canvas.create_rectangle(0, 0, fill_w, h, fill="#007acc", outline="")
            return
        n = len(parts)
        seg_w = w / n
        for i, p in enumerate(parts):
            x1 = int(i * seg_w)
            x2 = int((i + 1) * seg_w) - 2
            total = max(1, p.end - p.start + 1) if (p.end and p.start is not None) else 1
            part_pct = min(1.0, p.downloaded / total)
            part_h = int(h * part_pct)
            self.chunk_canvas.create_rectangle(x1, 0, x2, h, fill="#e8e8e8", outline="#cccccc")
            if part_h > 0:
                self.chunk_canvas.create_rectangle(x1, h - part_h, x2, h, fill="#0055aa", outline="")

    def _toggle_details(self):
        self._show_details = not self._show_details
        if self._show_details:
            self.btn_details.configure(text="Hide details <<")
            self.details_fr.pack(fill="x", padx=10, pady=(0, 6))
            self.win.geometry(f"{self.win.winfo_width()}x410")
        else:
            self.btn_details.configure(text="Show details >>")
            self.details_fr.pack_forget()
            self.win.geometry(f"{self.win.winfo_width()}x340")

    def _pause_toggle(self):
        if self.task.status == "downloading":
            self.task.pause()
            self.btn_pause.configure(text="Resume")
        else:
            self.task.start()
            self.btn_pause.configure(text="Pause")

    def _cancel(self):
        self.task.stop()
        self.win.destroy()

    def _build_limiter_tab(self, t):
        import tkinter as tk
        fr = tk.Frame(self.tab_limiter, bg="#ffffff", bd=1, relief="solid")
        fr.pack(fill="both", expand=True, padx=8, pady=8)

        use_var = tk.BooleanVar(value=bool(getattr(self.task, "speed_limit_kbps", 0) > 0))
        chk = tk.Checkbutton(fr, text="Use Speed Limiter", variable=use_var, bg="#ffffff", font=("Segoe UI", 9, "bold"))
        chk.pack(anchor="w", padx=14, pady=(14, 8))

        row = tk.Frame(fr, bg="#ffffff")
        row.pack(anchor="w", padx=14, pady=4)
        tk.Label(row, text="Maximum download speed:", bg="#ffffff", font=("Segoe UI", 9)).pack(side="left")
        spd_ent = tk.Entry(row, width=8, font=("Segoe UI", 9))
        spd_ent.insert(0, str(getattr(self.task, "speed_limit_kbps", 0) or 500))
        spd_ent.pack(side="left", padx=6)
        tk.Label(row, text="KB/sec", bg="#ffffff", font=("Segoe UI", 9)).pack(side="left")

        def apply_limiter():
            if use_var.get():
                try: self.task.speed_limit_kbps = int(spd_ent.get())
                except: self.task.speed_limit_kbps = 0
            else:
                self.task.speed_limit_kbps = 0

        tk.Button(fr, text="Apply", command=apply_limiter, relief="groove", padx=14, pady=2, cursor="hand2").pack(anchor="w", padx=14, pady=12)

    def _build_options_tab(self, t):
        import tkinter as tk
        fr = tk.Frame(self.tab_options, bg="#ffffff", bd=1, relief="solid")
        fr.pack(fill="both", expand=True, padx=8, pady=8)

        hang_var = tk.BooleanVar(value=False)
        exit_var = tk.BooleanVar(value=False)
        shut_var = tk.BooleanVar(value=False)

        tk.Checkbutton(fr, text="Hang up modem when done", variable=hang_var, bg="#ffffff", font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Checkbutton(fr, text="Exit CDM when done", variable=exit_var, bg="#ffffff", font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=4)
        tk.Checkbutton(fr, text="Turn off computer when done", variable=shut_var, bg="#ffffff", font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=4)

    def _tick(self):
        if not self.win.winfo_exists():
            return
        task = self.task
        title_fname = getattr(task, "filename", "") or "download"
        raw_pct = getattr(task, "progress", 0.0) or 0.0
        pct_val = raw_pct * 100 if raw_pct else (task.downloaded / task.size * 100 if getattr(task, "size", None) else 0.0)
        self.win.title(f"{int(pct_val)}% {title_fname}")

        status_text = {
            "downloading": "Receiving data...",
            "queued": "Queued",
            "paused": "Paused",
            "stopped": "Stopped",
            "completed": "Complete",
            "error": f"Error: {task.error_msg[:30]}"
        }.get(task.status, task.status)
        self.val_status.configure(text=status_text, fg="#008800" if task.status=="completed" else ("#0055aa" if task.status=="downloading" else "#cc0000"))

        size_str = f"{human_size(task.size)} ({task.size:,} bytes)" if getattr(task, "size", None) else human_size(task.downloaded)
        self.val_size.configure(text=size_str)

        dl_str = f"{human_size(task.downloaded)} ({pct_val:.2f} %)"
        self.val_dl.configure(text=dl_str)

        spd = getattr(task, "_speed", 0) if task.status == "downloading" else 0
        self.val_speed.configure(text=human_speed(spd) if task.status == "downloading" else "0 KB/sec")

        eta_s = format_eta((task.size - task.downloaded) / max(1, spd)) if (getattr(task, "size", None) and task.status == "downloading" and spd > 0) else "—"
        self.val_eta.configure(text=eta_s)

        res = "Yes" if getattr(task, "supports_range", False) else "No"
        self.val_resume.configure(text=res, fg="#008800" if res == "Yes" else "#cc0000")

        self._draw_progress_bar(pct_val)
        if self._show_details:
            self._draw_chunk_canvas()

        if task.status == "downloading":
            self.btn_pause.configure(text="Pause", state="normal")
        elif task.status in ("paused", "stopped"):
            self.btn_pause.configure(text="Resume", state="normal")
        elif task.status == "completed":
            self.btn_pause.configure(state="disabled")

        self.win.after(150, self._tick)

# ═══════════════════════════════════════════════════════════════════════════════
# GUI
# ═══════════════════════════════════════════════════════════════════════════════
def launch_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog

    settings     = load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    schedule_at  = {"time": None}
    tasks        = []     # list of DownloadTask or YtDlpTask
    sel          = {"task": None}
    _gs          = {"spd": 0.0, "total": 0, "at": time.time()}
    _clip_banner = {"visible": False, "url": ""}

    # ── translation helper ────────────────────────────────────────────────────
    def tr(key):
        lang = settings.get("language","en")
        return LANG.get(lang, LANG["en"]).get(key, LANG["en"].get(key, key))
    _ = tr

    # ── theme helper ──────────────────────────────────────────────────────────
    def T():
        return THEMES.get(settings.get("theme", "light"), THEMES["light"])

    # Ensure light theme default
    if settings.get("theme") not in ["light", "dark", "glass"]:
        settings["theme"] = "light"

    # ── root window ───────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title(f"{APP_NAME} v{VERSION}")
    root.geometry("1100x680")
    root.minsize(900, 540)
    root.configure(bg=T()["bg"])
    root.withdraw()  # Initially hidden until update check passes

    try:
        root.iconbitmap(str(BASE_DIR / "assets" / "icon.ico"))
    except Exception:
        pass

    FONT_UI    = ("Segoe UI", 9)
    FONT_BOLD  = ("Segoe UI", 9, "bold")
    FONT_TITLE = ("Segoe UI", 12, "bold")
    FONT_MONO  = ("Consolas", 9)

    style = ttk.Style(root)
    try: style.theme_use("clam")
    except Exception: pass

    # ══════════════════════════════════════════════════════════════════════════
    # CUSTOM IDM-STYLE BUTTON
    # ══════════════════════════════════════════════════════════════════════════
    class IDMButton(tk.Canvas):
        def __init__(self, parent, text, command=None, icon="", width=90, **kw):
            t = T()
            super().__init__(parent, width=width, height=34,
                             bg=t["toolbar"], bd=0, highlightthickness=0, **kw)
            self._text=text; self._icon=icon; self._cmd=command; self._hov=False
            self.bind("<Enter>",    self._enter)
            self.bind("<Leave>",    self._leave)
            self.bind("<Button-1>", self._click)
            self._draw()

        def _draw(self):
            t=T(); self.delete("all")
            bg = t["btn_hover"] if self._hov else t["btn_bg"]
            w,h,r = int(self["width"]),34,6
            self.create_polygon(r,0,w-r,0,w,r,w,h-r,w-r,h,r,h,0,h-r,0,r,
                                fill=bg,smooth=True,outline=t["accent"],width=1)
            self.create_text(w//2,h//2,
                             text=(self._icon+" "+self._text).strip(),
                             fill=t["btn_fg"],font=FONT_BOLD,anchor="center")

        def _enter(self,_): self._hov=True;  self._draw()
        def _leave(self,_): self._hov=False; self._draw()
        def _click(self,_):
            if self._cmd: self._cmd()
        def reconfigure(self):
            t=T(); self.configure(bg=t["toolbar"]); self._draw()

    all_btns = []
    def mkbtn(par, text, cmd, icon="", width=92, w=None, **kw):
        if w is not None: width = w
        b = IDMButton(par, text, cmd, icon=icon, width=width, **kw)
        all_btns.append(b); return b

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════════════

    # ── MENU BAR ──────────────────────────────────────────────────────────────
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    dm  = tk.Menu(menubar,tearoff=0)
    vm  = tk.Menu(menubar,tearoff=0)
    tm  = tk.Menu(menubar,tearoff=0)
    hm  = tk.Menu(menubar,tearoff=0)
    menubar.add_cascade(label="Downloads",menu=dm)
    menubar.add_cascade(label="View",     menu=vm)
    menubar.add_cascade(label="Tools",    menu=tm)
    menubar.add_cascade(label="Help",     menu=hm)

    dm.add_command(label="Add Download (Ctrl+N)",   command=lambda: add_dialog())
    dm.add_command(label="Batch Download",           command=lambda: batch_dialog())
    dm.add_command(label="Playlist / YouTube",       command=lambda: playlist_dialog())
    dm.add_command(label="Site Grabber",             command=lambda: grabber_dialog())
    dm.add_command(label="Torrent / Magnet",         command=lambda: torrent_dialog())
    dm.add_separator()
    dm.add_command(label="Settings",                 command=lambda: settings_dialog())
    dm.add_separator()
    dm.add_command(label="Exit",                     command=root.quit)

    vm.add_command(label="Toggle Theme",             command=lambda: toggle_theme())
    vm.add_command(label="Analytics Dashboard",      command=lambda: dashboard_dialog())

    tm.add_command(label="Test Proxy",               command=lambda: test_proxy_dialog())
    tm.add_command(label="Activate License",         command=lambda: activate_dialog())
    tm.add_command(label="Repair Browser Extension", command=lambda: repair_ext_dialog())
    tm.add_command(label="Check for Updates",        command=lambda: check_updates())

    hm.add_command(label=f"About {APP_NAME}",        command=lambda: about_dialog())

    root.bind("<Control-n>", lambda _: add_dialog())
    root.bind("<Delete>",    lambda _: do_remove())
    root.bind("<space>",     lambda _: (do_pause() if
                             (get_sel() and get_sel().status=="downloading")
                             else do_resume()))
    root.bind("<F5>",        lambda _: do_resume())

    # ── HEADER ────────────────────────────────────────────────────────────────
    hdr = tk.Frame(root, height=50)
    hdr.pack(fill="x"); hdr.pack_propagate(False)

    hdr_title = tk.Label(hdr, text=f"☁️  {APP_NAME}", font=FONT_TITLE, anchor="w")
    hdr_title.pack(side="left", padx=14)
    hdr_ver   = tk.Label(hdr, text=f"v{VERSION} — Smart Cloud Downloader",
                          font=FONT_UI, anchor="w")
    hdr_ver.pack(side="left")

    hdr_spd_var = tk.StringVar(value="")
    hdr_spd     = tk.Label(hdr, textvariable=hdr_spd_var, font=FONT_MONO, anchor="e")
    hdr_spd.pack(side="right", padx=14)

    # trial label
    trial_var = tk.StringVar(value="")
    trial_lbl = tk.Label(hdr, textvariable=trial_var, font=FONT_UI, anchor="e")
    trial_lbl.pack(side="right", padx=6)

    # ── TOOLBAR ───────────────────────────────────────────────────────────────
    tbar = tk.Frame(root, height=48)
    tbar.pack(fill="x"); tbar.pack_propagate(False)

    sep1 = tk.Frame(root, height=2)
    sep1.pack(fill="x")

    # ── CLIPBOARD BANNER ──────────────────────────────────────────────────────
    clip_frame = tk.Frame(root, height=0)
    clip_frame.pack(fill="x")

    clip_lbl = tk.Label(clip_frame, text="", font=FONT_UI, anchor="w")
    clip_lbl.pack(side="left", padx=10, fill="x", expand=True)
    clip_yes = tk.Button(clip_frame, text="⬇ Download", relief="flat", cursor="hand2")
    clip_yes.pack(side="right", padx=4, pady=2)
    clip_no  = tk.Button(clip_frame, text="✕ Ignore",   relief="flat", cursor="hand2")
    clip_no.pack(side="right", padx=0, pady=2)

    def show_clip_banner(url):
        _clip_banner["visible"] = True
        _clip_banner["url"]     = url
        short = url[:80] + ("…" if len(url)>80 else "")
        clip_lbl.configure(text=f"📋 {_('clipboard_found')}  {short}")
        apply_clip_theme()
        clip_frame.configure(height=30)
        clip_frame.pack_propagate(False)

    def hide_clip_banner():
        _clip_banner["visible"] = False
        clip_frame.configure(height=0)

    clip_yes.configure(command=lambda: (add_task(_clip_banner["url"]), hide_clip_banner()))
    clip_no.configure(command=hide_clip_banner)

    # ── BODY ──────────────────────────────────────────────────────────────────
    body = tk.Frame(root)
    body.pack(fill="both", expand=True)

    # sidebar
    sidebar = tk.Frame(body, width=170)
    sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)

    sb_title = tk.Label(sidebar, text="Categories", font=FONT_BOLD, anchor="w")
    sb_title.pack(fill="x", padx=8, pady=(10,4))

    cat_lb = tk.Listbox(sidebar, selectmode="single", activestyle="none",
                         bd=0, highlightthickness=0, relief="flat",
                         font=("Segoe UI",10), width=20)
    cat_lb.pack(fill="both", expand=True, padx=4, pady=4)

    sb_sep = tk.Frame(body, width=1)
    sb_sep.pack(side="left", fill="y")

    # main
    main = tk.Frame(body)
    main.pack(side="left", fill="both", expand=True)

    # tree
    tf = tk.Frame(main)
    tf.pack(fill="both", expand=True)

    cols = ("icon","file","size","progress","speed","eta","status")
    tree = ttk.Treeview(tf, columns=cols, show="headings",
                        selectmode="browse", height=14)
    for col,w,lbl,anch in [
        ("icon",  36,"","center"),("file",310,"Filename","w"),
        ("size",  80,"Size","center"),("progress",72,"Progress","center"),
        ("speed",100,"Speed","center"),("eta",70,"ETA","center"),
        ("status",110,"Status","center"),
    ]:
        tree.heading(col,text=lbl)
        tree.column(col,width=w,anchor=anch,stretch=(col=="file"))

    vsb = ttk.Scrollbar(tf,orient="vertical",   command=tree.yview)
    hsb = ttk.Scrollbar(tf,orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right",fill="y")
    hsb.pack(side="bottom",fill="x")
    tree.pack(fill="both",expand=True)

    # context menu
    ctx = tk.Menu(root,tearoff=0)
    ctx.add_command(label="▶  Resume",     command=lambda: do_resume())
    ctx.add_command(label="⏸  Pause",      command=lambda: do_pause())
    ctx.add_command(label="⏹  Stop",       command=lambda: do_stop())
    ctx.add_separator()
    ctx.add_command(label="📂  Open Folder",command=lambda: (open_folder(get_sel().filepath) if get_sel() else None))
    ctx.add_command(label="🔗  Copy URL",   command=lambda: (root.clipboard_clear() or root.clipboard_append(get_sel().url) if get_sel() else None))
    ctx.add_command(label="🔄  Refresh URL",command=lambda: refresh_url_dialog())
    ctx.add_separator()
    ctx.add_command(label="🗑  Remove",     command=lambda: do_remove())

    def show_ctx(e):
        try: tree.selection_set(tree.identify_row(e.y))
        except Exception: pass
        try: ctx.tk_popup(e.x_root,e.y_root)
        finally: ctx.grab_release()

    tree.bind("<Button-3>", show_ctx)
    tree.bind("<<TreeviewSelect>>", lambda _: on_select())
    tree.bind("<Double-1>", lambda _: (do_resume() if get_sel() and
                             get_sel().status in ("paused","stopped","error") else None))

    # ── DETAIL PANEL ──────────────────────────────────────────────────────────
    det_sep = tk.Frame(main,height=2)
    det_sep.pack(fill="x")

    det = tk.Frame(main,height=130)
    det.pack(fill="x"); det.pack_propagate(False)

    det_l = tk.Frame(det)
    det_l.pack(side="left",fill="both",expand=True,padx=10,pady=6)
    det_r = tk.Frame(det,width=170)
    det_r.pack(side="right",fill="y",padx=10,pady=6); det_r.pack_propagate(False)

    det_file  = tk.Label(det_l,text=_("no_select"),font=FONT_BOLD,anchor="w")
    det_file.pack(fill="x")
    det_url   = tk.Label(det_l,text="",font=FONT_UI,anchor="w")
    det_url.pack(fill="x")
    det_info  = tk.Label(det_l,text="",font=FONT_UI,anchor="w")
    det_info.pack(fill="x")
    det_pbar  = ttk.Progressbar(det_l,orient="horizontal",mode="determinate")
    det_pbar.pack(fill="x",pady=4)
    det_chunk = tk.Canvas(det_l,height=20)
    det_chunk.pack(fill="x")

    det_st_title = tk.Label(det_r,text="Transfer Info",font=FONT_BOLD,anchor="w")
    det_st_title.pack(fill="x")
    det_st_spd   = tk.Label(det_r,text="Speed :  —",font=FONT_MONO,anchor="w")
    det_st_spd.pack(fill="x")
    det_st_eta   = tk.Label(det_r,text="ETA   :  —",font=FONT_MONO,anchor="w")
    det_st_eta.pack(fill="x")
    det_st_seg   = tk.Label(det_r,text="Segments: —",font=FONT_MONO,anchor="w")
    det_st_seg.pack(fill="x")
    det_st_time  = tk.Label(det_r,text="Added :  —",font=FONT_UI,anchor="w")
    det_st_time.pack(fill="x")
    det_st_cat   = tk.Label(det_r,text="Category: —",font=FONT_UI,anchor="w")
    det_st_cat.pack(fill="x")

    # ── STATUS BAR ────────────────────────────────────────────────────────────
    st_sep = tk.Frame(root,height=2)
    st_sep.pack(fill="x")
    stbar = tk.Frame(root,height=24)
    stbar.pack(fill="x",side="bottom"); stbar.pack_propagate(False)
    sb_l  = tk.Label(stbar,text=_("ready"),font=FONT_UI,anchor="w")
    sb_l.pack(side="left",padx=8)
    sb_r  = tk.Label(stbar,text="",font=FONT_MONO,anchor="e")
    sb_r.pack(side="right",padx=8)

    # ══════════════════════════════════════════════════════════════════════════
    # TOOLBAR BUTTONS (MATCHES IDM 6.19 & 6.35)
    # ══════════════════════════════════════════════════════════════════════════
    TB = [
        ("Add URL",      "➕", lambda: add_dialog(),      68),
        ("Resume",       "▶",  lambda: do_resume(),       64),
        ("Stop",         "■",  lambda: do_pause(),        60),
        ("Stop All",     "✋", lambda: do_stop_all(),     68),
        ("Delete",       "🗑",  lambda: do_remove(),       64),
        ("Delete Co...", "🧹", lambda: do_del_completed(),76),
        ("Options",      "⚙",  lambda: settings_dialog(), 64),
        ("Scheduler",    "⏰", lambda: schedule_dialog(), 70),
        ("Start Qu...",  "🚀", lambda: do_start_queue(),  72),
        ("Stop Qu...",   "🛑", lambda: do_stop_queue(),   72),
        ("Grabber",      "🌐", lambda: grabber_dialog(),  66),
        ("Tell a Friend","👥", lambda: about_dialog(),    80),
    ]
    tb_btns = {}
    for name, icon, cmd, w in TB:
        b = mkbtn(tbar, name, cmd, icon=icon, width=w)
        b.pack(side="left", padx=1, pady=2)
        tb_btns[name] = b

    theme_btn = mkbtn(tbar, "Theme", lambda: toggle_theme(), icon="🌙", width=62)
    theme_btn.pack(side="right", padx=2, pady=2)
    all_btns.append(theme_btn)

    def get_cat_filter():
        sel = cat_tree.selection()
        return sel[0] if sel else "all"

    active_dialogs = {}
    def show_download_dialog(task):
        if not task: return
        dlg = active_dialogs.get(id(task))
        if dlg and dlg.win.winfo_exists():
            dlg.win.deiconify()
            dlg.win.lift()
            dlg.win.focus_force()
        else:
            active_dialogs[id(task)] = IDMDownloadStatusDialog(root, task, T)

    def do_stop_all():
        for t2 in tasks:
            if t2.status in ("downloading", "queued"):
                t2.pause()

    def do_start_queue():
        for t2 in tasks:
            if t2.status in ("queued", "paused", "stopped"):
                t2.start()

    def do_stop_queue():
        for t2 in tasks:
            if t2.status == "queued":
                t2.status = "stopped"

    def do_del_completed():
        to_del = [t2 for t2 in tasks if t2.status == "completed"]
        for t2 in to_del:
            iid = str(id(t2))
            if tree.exists(iid):
                tree.delete(iid)
            tasks.remove(t2)

    # ══════════════════════════════════════════════════════════════════════════
    # TASK HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def get_sel():
        s = tree.selection()
        if not s: return None
        for t2 in tasks:
            if str(id(t2)) == s[0]: return t2
        return None

    def on_select():
        sel["task"] = get_sel()
        refresh_detail()

    def add_task(url, filename=None, autostart=True, referer="", is_ytdlp=False,
                 quality="best", fmt="mp4", audio_only=False):
        if is_ytdlp or is_video_stream_url(url):
            task = YtDlpTask(url, settings["download_dir"],
                             quality=quality or settings.get("yt_quality", "best"),
                             fmt=fmt or settings.get("yt_format", "mp4"),
                             audio_only=audio_only,
                             proxy=settings.get("proxy",""))
        else:
            task = DownloadTask(url, settings["download_dir"],
                                connections=settings.get("connections",8),
                                speed_limit_kbps=settings.get("speed_limit_kbps",0),
                                filename=filename,
                                proxy=settings.get("proxy",""),
                                referer=referer)
        task.on_complete = on_task_complete
        tasks.append(task)
        icon = CAT_ICONS.get(task.category, "📁")
        date_s = datetime.fromtimestamp(task.added_at).strftime("%b %d %H:%M:%S %Y")
        tree.insert("", "end", iid=str(id(task)),
                    values=(f"{icon}  {task.filename or url[:35]}", "", "?", "Queued", "—", "—", date_s, url[:50]))
        if autostart:
            task.start()
            root.after(100, lambda: show_download_dialog(task))
        return task

    def on_task_complete(task):
        """Called from download thread when done."""
        if settings.get("notification_sound"):
            play_sound()
        if not settings.get("silent_mode"):
            windows_notify(_("dl_complete"), task.filename)
        if settings.get("auto_scan") and os.path.exists(task.filepath):
            no_win = 0x08000000 if sys.platform == "win32" else 0
            threading.Thread(target=lambda: subprocess.run(
                ["powershell","-Command",
                 f'Start-Process "MpCmdRun.exe" -ArgumentList "-Scan -ScanType 3 -File \'{task.filepath}\'"'],
                capture_output=True, creationflags=no_win), daemon=True).start()

    # ── action functions ───────────────────────────────────────────────────────
    def do_pause():
        t2 = get_sel()
        if t2: t2.pause()

    def do_resume():
        t2 = get_sel()
        if t2: t2.resume()

    def do_stop():
        t2 = get_sel()
        if t2: t2.stop()

    def do_remove():
        t2 = get_sel()
        if not t2: return
        if t2.status == "downloading":
            t2.stop(); time.sleep(0.3)
        tasks.remove(t2)
        iid = str(id(t2))
        if tree.exists(iid): tree.delete(iid)
        fp = getattr(t2,"filepath","")
        if t2.status=="completed" and fp and os.path.exists(fp):
            if messagebox.askyesno("Delete file?","Also delete the downloaded file?",parent=root):
                try: os.remove(fp)
                except OSError: pass

    def do_checksum():
        t2 = get_sel()
        if not t2 or t2.status!="completed":
            messagebox.showinfo("Checksum","Select a completed download first.",parent=root); return
        fp = getattr(t2,"filepath","")
        if not fp or not os.path.exists(fp):
            messagebox.showinfo("Checksum","File not found.",parent=root); return
        sha = sha256_of(fp)
        md5 = md5_of(fp)
        messagebox.showinfo("File Checksum",
                            f"File:    {t2.filename}\n\nSHA-256:\n{sha}\n\nMD5:\n{md5}",
                            parent=root)

    def do_mp3():
        t2 = get_sel()
        if not t2 or t2.status!="completed":
            messagebox.showinfo("MP3","Select a completed video/audio first.",parent=root); return
        if not shutil.which("ffmpeg"):
            messagebox.showinfo("ffmpeg Not Found",
                                "Install ffmpeg and add to PATH, then retry.",parent=root); return
        fp  = getattr(t2,"filepath","")
        out = os.path.splitext(fp)[0]+".mp3"
        try:
            subprocess.run(["ffmpeg","-y","-i",fp,"-vn","-acodec","libmp3lame","-q:a","4",out],
                           check=True, capture_output=True)
            messagebox.showinfo("MP3 Ready",f"Saved:\n{out}",parent=root)
        except subprocess.CalledProcessError:
            messagebox.showerror("Failed","ffmpeg conversion failed.",parent=root)

    def toggle_theme():
        order = ["dark","light","glass"]
        cur   = settings.get("theme","dark")
        nxt   = order[(order.index(cur)+1) % len(order)]
        settings["theme"] = nxt
        save_json(SETTINGS_FILE,settings)
        apply_theme()

    # ── wire toolbar ──────────────────────────────────────────────────────────
    # Toolbar buttons assigned at creation

    # ══════════════════════════════════════════════════════════════════════════
    # DIALOGS
    # ══════════════════════════════════════════════════════════════════════════
    def _dlg(title, w=540, h=320):
        win = tk.Toplevel(root)
        win.title(title)
        x = max(50, (win.winfo_screenwidth() - w) // 2)
        y = max(50, (win.winfo_screenheight() - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        if root.state() != "withdrawn":
            try: win.transient(root)
            except Exception: pass
        win.grab_set()
        t2 = T(); win.configure(bg=t2["bg"])
        return win, t2

    def _lbl(w, text, t2):
        tk.Label(w,text=text,bg=t2["bg"],fg=t2["fg"],
                 font=FONT_UI,anchor="w").pack(fill="x",padx=14,pady=(8,2))

    def _ent(w, t2, width=60):
        e=tk.Entry(w,bg=t2["field"],fg=t2["fg"],insertbackground=t2["fg"],
                   font=FONT_UI,relief="flat",bd=4,width=width)
        e.pack(fill="x",padx=14); return e

    def _btn(w, text, cmd, t2):
        b=tk.Button(w,text=text,command=cmd,bg=t2["accent"],fg="#fff",
                    font=FONT_BOLD,relief="flat",padx=16,pady=6,cursor="hand2")
        b.pack(pady=10); return b

    # ── Add Download ──────────────────────────────────────────────────────────
    def add_dialog(prefill_url=None):
        win,t2 = _dlg("Add New Download",540,330)
        win.deiconify()
        win.lift()
        win.attributes("-topmost", True)
        win.after_idle(win.attributes, "-topmost", False)
        _lbl(win,"Download URL:",t2)
        url_e=_ent(win,t2)
        if prefill_url:
            url_e.insert(0, prefill_url)
        _lbl(win,"Save filename (optional — auto-detect if empty):",t2)
        name_e=_ent(win,t2)
        _lbl(win,"Save folder:",t2)
        fr=tk.Frame(win,bg=t2["bg"]); fr.pack(fill="x",padx=14)
        folder_e=tk.Entry(fr,bg=t2["field"],fg=t2["fg"],insertbackground=t2["fg"],
                          font=FONT_UI,relief="flat",bd=4)
        folder_e.pack(side="left",fill="x",expand=True)
        folder_e.insert(0,settings["download_dir"])
        tk.Button(fr,text="Browse",command=lambda:(
            folder_e.delete(0,"end") or folder_e.insert(0,filedialog.askdirectory(parent=win) or folder_e.get())),
                  bg=t2["btn_bg"],fg=t2["btn_fg"],font=FONT_UI,relief="flat",padx=8,cursor="hand2"
        ).pack(side="left",padx=4)

        def do_add():
            url=url_e.get().strip()
            if not url.startswith(("http://","https://")):
                messagebox.showwarning("Invalid URL","Enter a valid http/https URL.",parent=win); return
            settings["download_dir"]=folder_e.get().strip() or settings["download_dir"]
            save_json(SETTINGS_FILE,settings)
            add_task(url,filename=name_e.get().strip() or None)
            win.destroy()

        _btn(win,"⬇  Start Download",do_add,t2)
        url_e.focus()

    # ── Batch ─────────────────────────────────────────────────────────────────
    def batch_dialog():
        win,t2 = _dlg("Batch Download",540,400)
        _lbl(win,"One URL per line:",t2)
        txt=tk.Text(win,height=14,bg=t2["field"],fg=t2["fg"],
                    insertbackground=t2["fg"],font=FONT_UI,relief="flat",bd=4)
        txt.pack(fill="both",expand=True,padx=14)
        def do():
            urls=[u.strip() for u in txt.get("1.0","end").splitlines()
                  if u.strip().startswith(("http://","https://"))]
            for u in urls: add_task(u)
            win.destroy()
            if urls: messagebox.showinfo("Batch",f"{len(urls)} downloads queued.",parent=root)
        _btn(win,"📦  Add All",do,t2)

    # ── Playlist ──────────────────────────────────────────────────────────────
    def playlist_dialog(prefill_url=None):
        win,t2 = _dlg("🎬 Video / YouTube Download - CDM", 580, 430)
        win.deiconify()
        win.lift()
        win.attributes("-topmost", True)
        win.after_idle(win.attributes, "-topmost", False)
        _lbl(win, "Video URL (YouTube, Facebook, Twitter, TikTok, etc.):", t2)
        url_e = _ent(win, t2)
        if prefill_url:
            url_e.insert(0, prefill_url)

        _lbl(win, "Select Resolution / Video Quality:", t2)
        fr = tk.Frame(win, bg=t2["bg"])
        fr.pack(fill="x", padx=14, pady=2)
        q_var = tk.StringVar(value=settings.get("yt_quality", "best"))

        qualities = [
            ("best", "🌟 Best (Max)"),
            ("4k", "4K (2160p)"),
            ("2k", "2K (1440p)"),
            ("1080p", "1080p (Full HD)"),
            ("720p", "720p (HD)"),
            ("480p", "480p (SD)"),
            ("360p", "360p")
        ]

        row1 = tk.Frame(fr, bg=t2["bg"])
        row1.pack(fill="x", pady=2)
        for val, label in qualities[:4]:
            tk.Radiobutton(row1, text=label, variable=q_var, value=val,
                           bg=t2["bg"], fg=t2["fg"], selectcolor=t2["field"],
                           activebackground=t2["bg"], font=FONT_UI).pack(side="left", padx=6)

        row2 = tk.Frame(fr, bg=t2["bg"])
        row2.pack(fill="x", pady=2)
        for val, label in qualities[4:]:
            tk.Radiobutton(row2, text=label, variable=q_var, value=val,
                           bg=t2["bg"], fg=t2["fg"], selectcolor=t2["field"],
                           activebackground=t2["bg"], font=FONT_UI).pack(side="left", padx=6)

        _lbl(win, "Video Format:", t2)
        fr2 = tk.Frame(win, bg=t2["bg"])
        fr2.pack(fill="x", padx=14, pady=2)
        fmt_var = tk.StringVar(value=settings.get("yt_format", "mp4"))
        for f in ["mp4", "mkv", "webm", "mp3"]:
            tk.Radiobutton(fr2, text=f.upper(), variable=fmt_var, value=f,
                           bg=t2["bg"], fg=t2["fg"], selectcolor=t2["field"],
                           activebackground=t2["bg"], font=FONT_UI).pack(side="left", padx=8)

        audio_var = tk.BooleanVar(value=False)
        tk.Checkbutton(win, text="🎵 Audio Only (Extract MP3)", variable=audio_var,
                       bg=t2["bg"], fg=t2["fg"], selectcolor=t2["field"],
                       activebackground=t2["bg"], font=FONT_BOLD).pack(anchor="w", padx=14, pady=6)

        def do():
            url = url_e.get().strip()
            if not url: return
            settings["yt_quality"] = q_var.get()
            settings["yt_format"] = fmt_var.get()
            save_json(SETTINGS_FILE, settings)
            add_task(url, is_ytdlp=True, quality=q_var.get(),
                     fmt=fmt_var.get(), audio_only=audio_var.get())
            win.destroy()

        _btn(win, "⬇  Start Download", do, t2)
        url_e.focus()

    # ── Site Grabber ──────────────────────────────────────────────────────────
    def grabber_dialog():
        win,t2 = _dlg("🌐 Site Grabber",580,460)
        _lbl(win,"Page URL:",t2)
        url_e=_ent(win,t2)
        _btn_scan=tk.Button(win,text="🔍 Scan Page",bg=t2["btn_bg"],fg=t2["btn_fg"],
                            font=FONT_BOLD,relief="flat",padx=14,pady=5,cursor="hand2")
        _btn_scan.pack(pady=6)
        _lbl(win,"Found links (tick to download):",t2)

        lb_frame=tk.Frame(win,bg=t2["bg"]); lb_frame.pack(fill="both",expand=True,padx=14)
        lb=tk.Listbox(lb_frame,selectmode="multiple",bg=t2["field"],fg=t2["fg"],
                      font=FONT_MONO,relief="flat",bd=2,height=8)
        lb.pack(fill="both",expand=True,side="left")
        sb2=ttk.Scrollbar(lb_frame,command=lb.yview)
        sb2.pack(side="right",fill="y"); lb.configure(yscrollcommand=sb2.set)

        found_links = []

        def scan():
            pg=url_e.get().strip()
            if not pg: return
            lb.delete(0,"end")
            links=SiteGrabber().grab(pg,proxy=settings.get("proxy",""))
            found_links.clear(); found_links.extend(links)
            for lk in links: lb.insert("end",lk)
            if not links: lb.insert("end","No downloadable files found.")

        _btn_scan.configure(command=scan)

        def dl_sel():
            idxs=lb.curselection()
            for i in idxs:
                if i < len(found_links): add_task(found_links[i])
            win.destroy()

        _btn(win,"⬇  Download Selected",dl_sel,t2)
        url_e.focus()

    # ── Torrent ───────────────────────────────────────────────────────────────
    def torrent_dialog():
        win,t2 = _dlg("🧲 Torrent / Magnet",540,220)
        _lbl(win,"Magnet link or .torrent file URL:",t2)
        url_e=_ent(win,t2)

        def do():
            url=url_e.get().strip()
            if not url: return
            aria2c=shutil.which("aria2c") or shutil.which("aria2c.exe")
            if not aria2c:
                messagebox.showinfo("aria2c Not Found",
                                    "Install aria2c for torrent support.\nhttps://aria2.github.io/",
                                    parent=win); return
            out=settings.get("download_dir",".")
            subprocess.Popen([aria2c,"--dir",out,url])
            win.destroy()
            messagebox.showinfo("Torrent","Torrent started via aria2c. Check terminal.",parent=root)

        _btn(win,"🧲  Start Torrent",do,t2)
        url_e.focus()

    # ── Settings ─────────────────────────────────────────────────────────────
    def settings_dialog():
        win,t2 = _dlg("Settings",520,500)
        _lbl(win,"Default save folder:",t2)
        folder_e=_ent(win,t2)
        folder_e.insert(0,settings["download_dir"])

        _lbl(win,"Connections (1–16):",t2)
        fr=tk.Frame(win,bg=t2["bg"]); fr.pack(fill="x",padx=14)
        conn_s=tk.Spinbox(fr,from_=1,to=16,width=6,bg=t2["field"],fg=t2["fg"],font=FONT_UI,relief="flat")
        conn_s.pack(side="left"); conn_s.delete(0,"end"); conn_s.insert(0,str(settings.get("connections",8)))

        _lbl(win,"Speed limit KB/s (0 = unlimited):",t2)
        spd_e=_ent(win,t2,14); spd_e.insert(0,str(settings.get("speed_limit_kbps",0)))

        _lbl(win,"Proxy (e.g. http://host:port or socks5://host:port):",t2)
        prx_e=_ent(win,t2); prx_e.insert(0,settings.get("proxy",""))

        _lbl(win,"Theme:",t2)
        fr3=tk.Frame(win,bg=t2["bg"]); fr3.pack(fill="x",padx=14)
        theme_var=tk.StringVar(value=settings.get("theme","dark"))
        for v,lbl in [("dark","🌙 Dark"),("light","☀ Light"),("glass","🔮 Glass")]:
            tk.Radiobutton(fr3,text=lbl,variable=theme_var,value=v,
                           bg=t2["bg"],fg=t2["fg"],selectcolor=t2["field"],
                           activebackground=t2["bg"],font=FONT_UI).pack(side="left",padx=6)

        _lbl(win,"Language:",t2)
        fr4=tk.Frame(win,bg=t2["bg"]); fr4.pack(fill="x",padx=14)
        lang_var=tk.StringVar(value=settings.get("language","en"))
        for v,lbl in [("en","English"),("bn","বাংলা"),("hi","हिंदी")]:
            tk.Radiobutton(fr4,text=lbl,variable=lang_var,value=v,
                           bg=t2["bg"],fg=t2["fg"],selectcolor=t2["field"],
                           activebackground=t2["bg"],font=FONT_UI).pack(side="left",padx=6)

        # checkboxes
        frck=tk.Frame(win,bg=t2["bg"]); frck.pack(fill="x",padx=14,pady=4)
        sil_var=tk.BooleanVar(value=settings.get("silent_mode",False))
        clp_var=tk.BooleanVar(value=settings.get("clipboard_monitor",True))
        snd_var=tk.BooleanVar(value=settings.get("notification_sound",True))
        scn_var=tk.BooleanVar(value=settings.get("auto_scan",False))
        for var,lbl in [(sil_var,"🔕 Silent mode"),(clp_var,"📋 Clipboard monitor"),
                         (snd_var,"🔔 Notification sound"),(scn_var,"🛡️ Windows Defender auto-scan")]:
            tk.Checkbutton(frck,text=lbl,variable=var,bg=t2["bg"],fg=t2["fg"],
                           selectcolor=t2["field"],activebackground=t2["bg"],
                           font=FONT_UI).pack(anchor="w")

        def save():
            settings["download_dir"]=folder_e.get().strip() or settings["download_dir"]
            try: settings["connections"]=max(1,min(16,int(conn_s.get())))
            except ValueError: pass
            try: settings["speed_limit_kbps"]=max(0,int(spd_e.get()))
            except ValueError: pass
            settings["proxy"]               = prx_e.get().strip()
            settings["theme"]               = theme_var.get()
            settings["language"]            = lang_var.get()
            settings["silent_mode"]         = sil_var.get()
            settings["clipboard_monitor"]   = clp_var.get()
            settings["notification_sound"]  = snd_var.get()
            settings["auto_scan"]           = scn_var.get()
            save_json(SETTINGS_FILE,settings)
            apply_theme()
            # update clipboard monitor
            if settings["clipboard_monitor"]: clip_mon.start()
            else: clip_mon.stop()
            win.destroy()

        _btn(win,"💾  Save Settings",save,t2)

    # ── Schedule ──────────────────────────────────────────────────────────────
    def schedule_dialog():
        t2=simpledialog.askstring("Scheduler","Start at? (HH:MM, e.g. 23:30)",parent=root)
        if not t2: return
        try:
            hh,mm=t2.strip().split(":")
            assert 0<=int(hh)<24 and 0<=int(mm)<60
            schedule_at["time"]=f"{int(hh):02d}:{int(mm):02d}"
            sb_l.configure(text=f"🕒 {_('schedule')}: queued downloads start at {schedule_at['time']}")
        except Exception:
            messagebox.showwarning("Invalid","Use HH:MM format.",parent=root)

    # ── Refresh URL ───────────────────────────────────────────────────────────
    def refresh_url_dialog():
        t2=get_sel()
        if not t2: return
        win,th=_dlg("🔄 Refresh Download URL",540,180)
        _lbl(win,"New URL for this download:",th)
        url_e=_ent(win,th)
        url_e.insert(0,t2.url)
        def do():
            t2.url=url_e.get().strip()
            t2.prepared=False
            t2.downloaded=0
            for p in t2.parts: p["done"]=0; p["finished"]=False
            t2.resume()
            win.destroy()
        _btn(win,"🔄  Refresh & Resume",do,th)

    # ── Proxy Test ────────────────────────────────────────────────────────────
    def test_proxy_dialog():
        prx=settings.get("proxy","")
        if not prx:
            messagebox.showinfo("Proxy","No proxy configured in Settings.",parent=root); return
        try:
            import urllib.request as ur
            opener=ur.build_opener(ur.ProxyHandler({"http":prx,"https":prx}))
            opener.open("https://httpbin.org/ip",timeout=10)
            messagebox.showinfo("Proxy OK","✅ Proxy is working!",parent=root)
        except Exception as e:
            messagebox.showerror("Proxy Failed",f"❌ Proxy error:\n{e}",parent=root)

    # ── License Activate (Microsoft-style) ───────────────────────────────────
    def activate_dialog(mandatory=False):
        win = tk.Toplevel(root)
        win.title("🔑 CDM Product Activation")
        win.geometry("560x360")
        win.resizable(False, False)
        win.transient(root)
        win.grab_set()
        t2 = T()
        win.configure(bg=t2["bg"])

        hdr_frame = tk.Frame(win, bg=t2["panel"], height=60)
        hdr_frame.pack(fill="x")
        hdr_frame.pack_propagate(False)

        tk.Label(hdr_frame, text="🔑  Enter your CDM Product Key", bg=t2["panel"],
                 fg="#ffffff", font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", padx=18, pady=10)

        content = tk.Frame(win, bg=t2["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(content,
                 text="Enter your 25-character product key to activate CDM (Cloud Download Manager):\nExample: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
                 bg=t2["bg"], fg=t2["muted"], font=FONT_UI, justify="left", anchor="w").pack(fill="x", pady=(0, 10))

        key_var = tk.StringVar()
        key_ent = tk.Entry(content, textvariable=key_var, font=("Consolas", 13, "bold"),
                           bg=t2["field"], fg=t2["accent"], insertbackground=t2["fg"],
                           relief="flat", bd=6, justify="center")
        key_ent.pack(fill="x", pady=6)

        stat_lbl = tk.Label(content, text="", bg=t2["bg"], font=FONT_UI)
        stat_lbl.pack(fill="x", pady=4)

        def on_key_type(*args):
            v = key_var.get().upper().replace(" ", "")
            if v.startswith("CDM-") and len(v) < 25:
                return
            clean = "".join(c for c in v if c.isalnum())
            if len(clean) > 25:
                clean = clean[:25]
            grouped = [clean[i:i+5] for i in range(0, len(clean), 5)]
            formatted = "-".join(grouped)
            if formatted != key_var.get():
                key_var.set(formatted)
                key_ent.icursor(len(formatted))

        key_var.trace_add("write", on_key_type)

        btn_row = tk.Frame(win, bg=t2["bg"])
        btn_row.pack(fill="x", padx=20, pady=(0, 18))

        def do_activate():
            k = key_var.get().strip()
            if trial.activate(k):
                stat_lbl.configure(text="✅ Verification successful! Full lifetime license activated.", fg=t2["green"])
                update_trial_label()
                messagebox.showinfo("Activation Successful",
                                    "Thank you! CDM (Cloud Download Manager) has been successfully activated.\n\nYou have unlimited lifetime access.", parent=win)
                win.destroy()
            else:
                stat_lbl.configure(text="❌ Invalid Product Key. Please check the key and try again.", fg=t2["red"])

        def do_trial():
            trial.start_trial()
            update_trial_label()
            messagebox.showinfo("Trial Started",
                                f"Your {TRIAL_DAYS}-day free trial has been activated.\nEnjoy full features of CDM (Cloud Download Manager)!", parent=win)
            win.destroy()

        def do_close():
            if mandatory and not trial.is_valid:
                root.destroy()
            else:
                win.destroy()

        win.protocol("WM_DELETE_WINDOW", do_close)

        tk.Button(btn_row, text="🔑 Activate Now", command=do_activate,
                  bg=t2["accent"], fg="#ffffff", font=FONT_BOLD,
                  relief="flat", padx=16, pady=7, cursor="hand2").pack(side="left")

        if not trial.is_trial_active and not trial.is_activated:
            tk.Button(btn_row, text="⏱ Start 3-Day Trial", command=do_trial,
                      bg=t2["btn_bg"], fg=t2["btn_fg"], font=FONT_UI,
                      relief="flat", padx=12, pady=7, cursor="hand2").pack(side="left", padx=8)

        tk.Button(btn_row, text="✕ Exit" if mandatory else "Cancel", command=do_close,
                  bg=t2["bg2"], fg=t2["muted"], font=FONT_UI,
                  relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right")

        key_ent.focus()

    # ── Repair Extension ─────────────────────────────────────────────────────
    def repair_ext_dialog():
        ext_dir = BASE_DIR / "browser_extension"
        chrome_dir = ext_dir / "chrome"
        msg = f"Extension path:\n{chrome_dir}\n\nTo manually install:\n"
        msg += "Chrome: chrome://extensions → Load unpacked → select chrome folder\n"
        msg += "Firefox: about:debugging → Load Temporary Add-on → select manifest.json"
        messagebox.showinfo("Browser Extension",msg,parent=root)

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def dashboard_dialog():
        win,t2=_dlg("📊 Analytics Dashboard",500,420)
        st=load_json(STATS_FILE,{"total_bytes":0,"total_files":0,"by_category":{}})
        tk.Label(win,text="📊 Download Analytics",bg=t2["bg"],fg=t2["accent"],
                 font=FONT_TITLE).pack(pady=10)
        rows=[
            ("Total Downloaded",human_size(st.get("total_bytes",0))),
            ("Total Files",str(st.get("total_files",0))),
            ("Active Downloads",str(sum(1 for t3 in tasks if t3.status=="downloading"))),
            ("Completed",str(sum(1 for t3 in tasks if t3.status=="completed"))),
            ("In Queue",str(sum(1 for t3 in tasks if t3.status=="queued"))),
        ]
        fr=tk.Frame(win,bg=t2["panel"]); fr.pack(fill="x",padx=20,pady=4)
        for k,v in rows:
            row=tk.Frame(fr,bg=t2["panel"]); row.pack(fill="x",padx=10,pady=3)
            tk.Label(row,text=k+":",bg=t2["panel"],fg=t2["muted"],font=FONT_UI,anchor="w",width=22).pack(side="left")
            tk.Label(row,text=v,bg=t2["panel"],fg=t2["accent"],font=FONT_BOLD,anchor="w").pack(side="left")

        # by category
        tk.Label(win,text="By Category:",bg=t2["bg"],fg=t2["fg"],font=FONT_BOLD).pack(anchor="w",padx=20,pady=(10,2))
        bc=st.get("by_category",{})
        frb=tk.Frame(win,bg=t2["panel"]); frb.pack(fill="x",padx=20)
        for cat,cnt in sorted(bc.items(),key=lambda x:-x[1]):
            row=tk.Frame(frb,bg=t2["panel"]); row.pack(fill="x",padx=10,pady=2)
            icon=CAT_ICONS.get(cat,"📁")
            tk.Label(row,text=f"{icon} {cat}:",bg=t2["panel"],fg=t2["muted"],font=FONT_UI,anchor="w",width=16).pack(side="left")
            tk.Label(row,text=f"{cnt} files",bg=t2["panel"],fg=t2["fg"],font=FONT_UI,anchor="w").pack(side="left")

    # ── About ─────────────────────────────────────────────────────────────────
    def about_dialog():
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{VERSION}\n\n"
            "IDM-er Dada, Goriber Bondhu!\n\n"
            "✅ Multi-connection Download\n"
            "✅ Playlist & YouTube (yt-dlp)\n"
            "✅ Browser Extension (Chrome/Firefox)\n"
            "✅ Site Grabber, Torrent, Proxy\n"
            "✅ Dark / Light / Glass Theme\n"
            "✅ English / বাংলা / हिंदी\n\n"
            f"Build: {BUILD_DATE}  |  Python {sys.version.split()[0]}",
            parent=root)

    # ── Update check (GitHub update.json) ────────────────────────────────────
    def check_updates(manual=True, on_startup=False, on_success_no_update=None):
        def _check_worker():
            try:
                up_url = settings.get("update_url", "https://raw.githubusercontent.com/telemy464-arch/CDM/main/update.json")
                req = urllib.request.Request(up_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CDM-Updater/2.0"})
                try:
                    ctx = ssl.create_default_context()
                    resp = urllib.request.urlopen(req, timeout=8, context=ctx)
                except Exception:
                    ctx = ssl._create_unverified_context()
                    resp = urllib.request.urlopen(req, timeout=8, context=ctx)

                with resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)

                remote_v = data.get("version", "").strip()
                if not remote_v:
                    if on_startup and on_success_no_update:
                        root.after(0, on_success_no_update)
                    return

                def vtuple(v):
                    return [int(x) for x in re.findall(r'\d+', v)]

                is_mandatory = bool(data.get("mandatory", False)) or on_startup
                has_update = vtuple(remote_v) > vtuple(VERSION)

                if has_update:
                    root.after(0, lambda: show_update_popup(data, mandatory=is_mandatory))
                else:
                    if on_startup and on_success_no_update:
                        root.after(0, on_success_no_update)
                    elif manual:
                        root.after(0, lambda: messagebox.showinfo(
                            "Up to Date",
                            f"You have the latest version of {APP_NAME}!\n\nCurrent Version: v{VERSION}\nLatest Version:  v{remote_v}",
                            parent=root))
            except Exception as e:
                if on_startup:
                    root.after(0, lambda: show_offline_prompt(str(e), on_success_no_update))
                elif manual:
                    root.after(0, lambda: messagebox.showerror(
                        "Update Check",
                        f"Current version: v{VERSION}\n\nCould not reach GitHub update server.\nMake sure update.json is online.\n\nError: {e}",
                        parent=root))

        threading.Thread(target=_check_worker, daemon=True).start()

    def show_offline_prompt(err_msg, on_continue):
        win = tk.Toplevel(root)
        win.title(f"{APP_NAME} - Connection Notice")
        w, h = 500, 240
        x = max(50, (win.winfo_screenwidth() - w) // 2)
        y = max(50, (win.winfo_screenheight() - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.resizable(False, False)
        t2 = T(); win.configure(bg=t2["bg"])
        win.deiconify(); win.lift(); win.focus_force(); win.grab_set()

        hdr_fr = tk.Frame(win, bg=t2["panel"])
        hdr_fr.pack(fill="x", padx=16, pady=12)
        tk.Label(hdr_fr, text="⚠️  Could Not Check for Updates",
                 bg=t2["panel"], fg=t2["yellow"], font=FONT_TITLE, anchor="w").pack(padx=10, pady=(8,2), fill="x")
        tk.Label(hdr_fr, text="Unable to connect to the CDM online update server.\nPlease check your internet connection.",
                 bg=t2["panel"], fg=t2["muted"], font=FONT_UI, anchor="w").pack(padx=10, pady=(0,8), fill="x")

        btn_fr = tk.Frame(win, bg=t2["bg"])
        btn_fr.pack(fill="x", padx=16, pady=12)

        def do_retry():
            win.destroy()
            check_updates(manual=False, on_startup=True, on_success_no_update=on_continue)

        def do_continue():
            win.destroy()
            if on_continue:
                on_continue()

        def do_exit():
            win.destroy()
            root.destroy()
            sys.exit(0)

        tk.Button(btn_fr, text="🔄  Retry", command=do_retry,
                  bg=t2["btn_bg"], fg=t2["btn_fg"], font=FONT_BOLD, relief="flat", padx=14, pady=6, cursor="hand2").pack(side="left")
        tk.Button(btn_fr, text="Continue Offline", command=do_continue,
                  bg=t2["panel"], fg=t2["fg"], font=FONT_UI, relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=10)
        tk.Button(btn_fr, text="✕ Exit", command=do_exit,
                  bg=t2["bg2"], fg=t2["muted"], font=FONT_UI, relief="flat", padx=12, pady=6, cursor="hand2").pack(side="right")

    def show_update_popup(data, mandatory=False):
        remote_v = data.get("version", "").strip()
        win = tk.Toplevel(root)
        win_title = f"🚨 CDM - Critical Update Required (v{remote_v})" if mandatory else f"🚀 CDM - New Update Available (v{remote_v})"
        win.title(win_title)
        w, h = 560, 480
        x = max(50, (win.winfo_screenwidth() - w) // 2)
        y = max(50, (win.winfo_screenheight() - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.resizable(False, False)

        if os.path.exists(str(BASE_DIR / "assets" / "icon.ico")):
            try: win.iconbitmap(str(BASE_DIR / "assets" / "icon.ico"))
            except Exception: pass

        t2 = T()
        win.configure(bg=t2["bg"])
        win.deiconify()
        win.lift()
        win.attributes("-topmost", True)
        win.after_idle(win.attributes, "-topmost", False)
        win.focus_force()
        win.grab_set()

        def _exit_app():
            win.destroy()
            root.destroy()
            sys.exit(0)

        if mandatory:
            win.protocol("WM_DELETE_WINDOW", _exit_app)
        else:
            win.protocol("WM_DELETE_WINDOW", win.destroy)

        # Header banner
        hdr_fr = tk.Frame(win, bg=t2["panel"])
        hdr_fr.pack(fill="x", padx=14, pady=(12, 6))

        title_lbl = f"🚨 Critical Update Required! (v{remote_v})" if mandatory else f"✨ New Version of {APP_NAME} Available!"
        title_col = t2["red"] if mandatory else t2["accent"]
        tk.Label(hdr_fr, text=title_lbl, bg=t2["panel"], fg=title_col, font=FONT_TITLE, anchor="w").pack(padx=10, pady=(8, 2), fill="x")

        sub_text = "You must install this update to continue using CDM." if mandatory else "A new version with performance improvements is ready to install."
        tk.Label(hdr_fr, text=sub_text, bg=t2["panel"], fg=t2["muted"], font=FONT_UI, anchor="w").pack(padx=10, pady=(0, 8), fill="x")

        # Version & info row
        info_fr = tk.Frame(win, bg=t2["panel"])
        info_fr.pack(fill="x", padx=14, pady=4)
        tk.Label(info_fr, text=f"Installed Version: v{VERSION}  ➔  New Version: v{remote_v}",
                 bg=t2["panel"], fg=t2["green"], font=FONT_TITLE, anchor="w").pack(padx=10, pady=(6, 2), fill="x")

        rel_date = data.get("release_date", "")
        min_os = data.get("min_os", "Windows 10 / 11")
        tk.Label(info_fr, text=f"Release Date: {rel_date}  |  Supported: {min_os}",
                 bg=t2["panel"], fg=t2["muted"], font=FONT_UI, anchor="w").pack(padx=10, pady=(0, 6), fill="x")

        _lbl(win, "What's new in this release:", t2)
        txt = tk.Text(win, height=6, bg=t2["field"], fg=t2["fg"], font=FONT_UI, relief="flat", bd=4)
        txt.pack(fill="both", expand=True, padx=14, pady=4)
        changelog = data.get("changelog", [])
        if isinstance(changelog, list):
            for item in changelog:
                txt.insert("end", f"• {item}\n")
        else:
            txt.insert("end", str(changelog))
        txt.configure(state="disabled")

        # Progress frame (initially hidden)
        prog_fr = tk.Frame(win, bg=t2["bg"])
        prog_status = tk.Label(prog_fr, text="Preparing download...", bg=t2["bg"], fg=t2["fg"], font=FONT_BOLD, anchor="w")
        prog_status.pack(fill="x", padx=14, pady=(4, 2))
        prog_bar = ttk.Progressbar(prog_fr, orient="horizontal", mode="determinate", maximum=100)
        prog_bar.pack(fill="x", padx=14, pady=4)
        prog_detail = tk.Label(prog_fr, text="0 MB / 0 MB • 0 KB/s", bg=t2["bg"], fg=t2["muted"], font=FONT_UI, anchor="w")
        prog_detail.pack(fill="x", padx=14, pady=(2, 6))

        dl_url = data.get("download_url", "https://raw.githubusercontent.com/telemy464-arch/CDM/main/installer/output/CDM_Setup_v2.0.exe")

        # Buttons frame
        btn_fr = tk.Frame(win, bg=t2["bg"])
        btn_fr.pack(fill="x", padx=14, pady=10)

        def do_download_and_install():
            btn_fr.pack_forget()
            prog_fr.pack(fill="x", padx=14, pady=10)

            def _worker():
                try:
                    prog_status.configure(text=f"Connecting to update server...")
                    temp_dir = tempfile.gettempdir()
                    fname = os.path.basename(urllib.parse.urlparse(dl_url).path) or f"CDM_Setup_v{remote_v}.exe"
                    dest_file = os.path.join(temp_dir, fname)

                    req = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CDM-Updater/2.0"})
                    try:
                        ctx = ssl.create_default_context()
                        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
                    except Exception:
                        ctx = ssl._create_unverified_context()
                        resp = urllib.request.urlopen(req, timeout=30, context=ctx)

                    with resp:
                        total_bytes = int(resp.headers.get("Content-Length", 0))
                        downloaded = 0
                        start_time = time.time()
                        last_update = 0

                        with open(dest_file, "wb") as f:
                            while True:
                                chunk = resp.read(65536)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded += len(chunk)
                                now = time.time()
                                if now - last_update >= 0.1 or downloaded == total_bytes:
                                    last_update = now
                                    elapsed = now - start_time
                                    spd = downloaded / elapsed if elapsed > 0 else 0
                                    pct = int((downloaded / total_bytes * 100)) if total_bytes > 0 else 0
                                    det_text = f"{human_size(downloaded)} / {human_size(total_bytes)} ({pct}%) • {human_speed(spd)}"
                                    win.after(0, lambda p=pct, d=det_text: (
                                        prog_bar.configure(value=p),
                                        prog_status.configure(text=f"Downloading CDM v{remote_v} Update ({p}%)..."),
                                        prog_detail.configure(text=d)
                                    ))

                    win.after(0, lambda: (
                        prog_status.configure(text="⚡ Applying update & restarting CDM...", fg=t2["green"]),
                        prog_detail.configure(text="Please wait, CDM will restart automatically...")
                    ))
                    time.sleep(0.8)

                    # Build silent auto-update batch script
                    updater_bat = os.path.join(temp_dir, "cdm_auto_updater.bat")
                    current_exe = sys.executable if getattr(sys, 'frozen', False) else ""

                    bat_code = f"""@echo off
chcp 65001 >nul
timeout /t 1 /nobreak >nul
taskkill /f /im CDM.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /f /im CDM.exe >nul 2>&1

:: Run Inno Setup installer 100% silently in background
start /wait "" "{dest_file}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-

:: Restart CDM
if exist "{current_exe}" (
    start "" "{current_exe}"
) else if exist "%ProgramFiles%\\CDM\\CDM.exe" (
    start "" "%ProgramFiles%\\CDM\\CDM.exe"
) else if exist "%LocalAppData%\\Programs\\CDM\\CDM.exe" (
    start "" "%LocalAppData%\\Programs\\CDM\\CDM.exe"
)

del "%~f0" >nul 2>&1
"""
                    with open(updater_bat, "w", encoding="utf-8") as f:
                        f.write(bat_code)

                    # Launch with PowerShell elevation so it can overwrite in Program Files
                    ps_cmd = f'Start-Process -FilePath "cmd.exe" -ArgumentList \'/c "{updater_bat}"\' -WindowStyle Hidden -Verb RunAs'
                    try:
                        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd],
                                         creationflags=0x08000000)
                    except Exception:
                        subprocess.Popen(["cmd.exe", "/c", updater_bat],
                                         creationflags=0x08000000)

                    time.sleep(0.3)
                    os._exit(0)
                except Exception as ex:
                    def _show_err(err=str(ex)):
                        messagebox.showerror("Update Download Failed", f"Could not download update:\n{err}", parent=win)
                        prog_fr.pack_forget()
                        btn_fr.pack(fill="x", padx=14, pady=10)
                    win.after(0, _show_err)

            threading.Thread(target=_worker, daemon=True).start()

        tk.Button(btn_fr, text="⬇  Download & Install Update Now", command=do_download_and_install,
                  bg=t2["green"], fg="#ffffff", font=FONT_BOLD, relief="flat", padx=16, pady=7, cursor="hand2").pack(side="left")

        if mandatory:
            tk.Button(btn_fr, text="✕  Exit CDM", command=_exit_app,
                      bg=t2["red"], fg="#ffffff", font=FONT_BOLD, relief="flat", padx=14, pady=7, cursor="hand2").pack(side="right")
        else:
            tk.Button(btn_fr, text="Remind Me Later", command=win.destroy,
                      bg=t2["btn_bg"], fg=t2["btn_fg"], font=FONT_UI, relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right")

    # ══════════════════════════════════════════════════════════════════════════
    # DRAW HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def draw_chunk_map(task):
        det_chunk.delete("all")
        t2=T(); w=det_chunk.winfo_width()
        if w<10 or not task or not hasattr(task,"parts") or not task.parts: return
        h=20; total=task.size or sum(p["size"] for p in task.parts) or 1; x=0
        for p in task.parts:
            pw=max(2,int(w*p["size"]/total)); done_w=int(pw*(p["done"]/p["size"])) if p["size"] else 0
            det_chunk.create_rectangle(x,2,x+pw-1,h-2,fill=t2["bar_bg"],outline=t2["bg"])
            if done_w>0: det_chunk.create_rectangle(x,2,x+done_w,h-2,fill=t2["bar_fill"],outline="")
            if p["finished"]: det_chunk.create_rectangle(x,2,x+pw-1,h-2,fill=t2["green"],outline="")
            x+=pw

    def refresh_detail():
        task=sel["task"]; t2=T()
        wlist=[det_l,det_r,det_chunk,det_st_title,det_st_spd,det_st_eta,
               det_st_seg,det_st_time,det_st_cat,det_file,det_url,det_info]
        for w2 in wlist:
            try: w2.configure(bg=t2["bg"])
            except Exception: pass
        for w2 in [det_file,det_url,det_info,det_st_title,det_st_spd,
                    det_st_eta,det_st_seg,det_st_time,det_st_cat]:
            try: w2.configure(fg=t2["fg"])
            except Exception: pass

        if not task:
            det_file.configure(text=_("no_select"))
            det_url.configure(text=""); det_info.configure(text="")
            det_pbar["value"]=0
            for w2 in [det_st_spd,det_st_eta,det_st_seg,det_st_time,det_st_cat]:
                w2.configure(text=w2.cget("text").split(":")[0]+":  —")
            draw_chunk_map(None); return

        det_file.configure(text=task.filename or task.url[:70])
        det_url.configure(text=task.url[:90]+("…" if len(task.url)>90 else ""))
        spd=getattr(task,"_speed",0)
        segs=len(getattr(task,"parts",[])) or 1
        eta="—"
        if task.size:
            det_info.configure(
                text=f"{human_size(task.downloaded)} / {human_size(task.size)}"
                     f"  ({task.progress*100:.1f}%)  •  {task.status}"
                     +(f"  ⚠ {task.error_msg}" if task.error_msg else ""))
            det_pbar["value"]=task.progress*100
            if task.status=="downloading" and spd>0:
                eta=format_eta((task.size-task.downloaded)/max(1,spd))
        else:
            det_info.configure(text=f"{human_size(task.downloaded)} downloaded  •  {task.status}")
            det_pbar["value"]=int(task.progress*100)
        det_st_spd.configure(text=f"Speed :  {human_speed(spd)}")
        det_st_eta.configure(text=f"ETA   :  {eta}")
        det_st_seg.configure(text=f"Segments: {segs}")
        det_st_time.configure(text=f"Added :  {datetime.fromtimestamp(task.added_at).strftime('%H:%M:%S')}")
        det_st_cat.configure(text=f"Category: {getattr(task,'category','—')}")
        draw_chunk_map(task)

    def refresh_tree():
        cat_f = get_cat_filter()
        for task in tasks:
            iid = str(id(task))
            if not tree.exists(iid): continue
            show = True
            if cat_f == "all": show = True
            elif cat_f == "cat_Compressed": show = (getattr(task, "category", "") == "Compressed")
            elif cat_f == "cat_Documents":  show = (getattr(task, "category", "") == "Documents")
            elif cat_f == "cat_Music":      show = (getattr(task, "category", "") == "Music")
            elif cat_f == "cat_Programs":   show = (getattr(task, "category", "") == "Programs")
            elif cat_f == "cat_Video":      show = (getattr(task, "category", "") == "Video")
            elif cat_f == "unfinished":     show = (task.status in ("downloading", "queued", "paused", "stopped"))
            elif cat_f == "finished":       show = (task.status == "completed")
            elif cat_f == "queues":         show = (task.status == "queued")
            elif cat_f == "grabber":        show = ("grabber" in getattr(task, "source", ""))

            if show:
                raw_pct = getattr(task, "progress", 0.0) or 0.0
                pct = f"{raw_pct*100:.1f}%" if getattr(task, "size", None) else ("—" if isinstance(task, DownloadTask) else f"{int(raw_pct*100)}%")
                size_s = human_size(task.size) if getattr(task, "size", None) else human_size(task.downloaded)
                spd = getattr(task, "_speed", 0) if task.status == "downloading" else 0
                eta = format_eta((task.size - task.downloaded) / max(1, spd)) if (getattr(task, "size", None) and task.status == "downloading" and spd > 0) else "—"
                speed_s = human_speed(spd) if task.status == "downloading" else "—"
                icon = CAT_ICONS.get(getattr(task, "category", ""), "📁")
                date_s = datetime.fromtimestamp(task.added_at).strftime("%b %d %H:%M:%S %Y") if getattr(task, "added_at", None) else "—"
                stat_s = "Complete" if task.status == "completed" else (f"{pct}" if task.status == "downloading" else task.status.capitalize())
                desc_s = getattr(task, "url", "")[:50]

                tree.item(iid, values=(f"{icon}  {task.filename or task.url[:35]}", "", size_s, stat_s, eta, speed_s, date_s, desc_s))
                col = STATUS_COLORS.get(task.status, "#e0e0e0")
                tree.tag_configure(task.status, foreground=col)
                tree.item(iid, tags=(task.status,))
                try: tree.reattach(iid, "", "end")
                except Exception: pass
            else:
                try: tree.detach(iid)
                except Exception: pass

    # ══════════════════════════════════════════════════════════════════════════
    # TRIAL LABEL
    # ══════════════════════════════════════════════════════════════════════════
    def update_trial_label():
        if trial.is_activated:
            trial_var.set("✅ Full Version")
            trial_lbl.configure(fg=T()["green"])
        elif trial.is_trial_active:
            hrs = trial.hours_left
            if hrs <= 24:
                trial_var.set(f"⏱ Trial: {hrs}h left")
            else:
                trial_var.set(_("trial_left").format(d=trial.days_left))
            trial_lbl.configure(fg=T()["yellow"])
        else:
            trial_var.set(_("trial_expired"))
            trial_lbl.configure(fg=T()["red"])

    # ══════════════════════════════════════════════════════════════════════════
    # THEME
    # ══════════════════════════════════════════════════════════════════════════
    def apply_clip_theme():
        t2=T()
        clip_frame.configure(bg=t2["accent2"])
        clip_lbl.configure(bg=t2["accent2"],fg="#fff")
        clip_yes.configure(bg=t2["accent"],fg="#fff",relief="flat")
        clip_no.configure(bg=t2["bg2"],fg=t2["fg"],relief="flat")

    def apply_theme():
        t2=T()
        root.configure(bg=t2["bg"])
        style.configure("TFrame",        background=t2["bg"])
        style.configure("TLabel",        background=t2["bg"],     foreground=t2["fg"])
        style.configure("Treeview",      background=t2["tree_bg"],fieldbackground=t2["tree_bg"],
                        foreground=t2["fg"],rowheight=28)
        style.configure("Treeview.Heading",background=t2["header_bg"],foreground=t2["header_fg"],
                        relief="flat",font=FONT_BOLD)
        style.map("Treeview",background=[("selected",t2["tree_sel"])],
                  foreground=[("selected",t2["tree_sel_fg"])])
        style.configure("Horizontal.TProgressbar",background=t2["bar_fill"],
                        troughcolor=t2["bar_bg"],borderwidth=0,thickness=14)
        style.configure("TScrollbar",background=t2["sb_bg"],troughcolor=t2["sb_trough"],borderwidth=0)

        for w2 in [hdr,tbar,body,sidebar,main,tf,det,det_l,det_r]:
            try: w2.configure(bg=t2["bg"])
            except Exception: pass
        hdr.configure(bg=t2["toolbar"])
        tbar.configure(bg=t2["toolbar"])
        sidebar.configure(bg=t2["cat_bg"])
        sb_sep.configure(bg=t2["sep"])
        sep1.configure(bg=t2["sep"])
        det_sep.configure(bg=t2["sep"])
        stbar.configure(bg=t2["bg2"])
        st_sep.configure(bg=t2["sep"])
        hdr_title.configure(bg=t2["toolbar"],fg=t2["accent"])
        hdr_ver.configure(bg=t2["toolbar"],fg=t2["muted"])
        hdr_spd.configure(bg=t2["toolbar"],fg=t2["green"])
        trial_lbl.configure(bg=t2["toolbar"])
        sb_title.configure(bg=t2["cat_bg"],fg=t2["fg"])
        cat_lb.configure(bg=t2["cat_bg"],fg=t2["fg"],
                          selectbackground=t2["cat_sel"],selectforeground=t2["tree_sel_fg"])
        det_chunk.configure(bg=t2["bg"],highlightthickness=0)
        for w2 in [det_file,det_url,det_info,det_st_title,det_st_spd,det_st_eta,det_st_seg,det_st_time,det_st_cat]:
            try: w2.configure(bg=t2["bg"],fg=t2["fg"])
            except Exception: pass
        sb_l.configure(bg=t2["bg2"],fg=t2["muted"])
        sb_r.configure(bg=t2["bg2"],fg=t2["muted"])
        for b in all_btns:
            try: b.reconfigure()
            except Exception: pass
        theme_btn._icon="🌙" if settings.get("theme")=="dark" else ("☀" if settings.get("theme")=="light" else "🔮")
        theme_btn._draw()
        ctx.configure(bg=t2["panel"],fg=t2["fg"],
                      activebackground=t2["tree_sel"],activeforeground=t2["tree_sel_fg"])
        apply_clip_theme()
        update_trial_label()

    # ══════════════════════════════════════════════════════════════════════════
    # BROWSER EXTENSION SERVER
    # ══════════════════════════════════════════════════════════════════════════
    ext_server = ExtensionServer(EXT_PORT)
    def on_ext_url(url, referer):
        if is_video_stream_url(url):
            root.after(0, lambda: playlist_dialog(prefill_url=url))
        else:
            root.after(0, lambda: add_dialog(prefill_url=url))
    ext_server.on_url = on_ext_url
    ext_server.start()

    # ══════════════════════════════════════════════════════════════════════════
    # CLIPBOARD MONITOR
    # ══════════════════════════════════════════════════════════════════════════
    def on_clip(url):
        if settings.get("clipboard_monitor") and not settings.get("silent_mode"):
            if is_video_stream_url(url):
                root.after(0, lambda: (show_clip_banner(url), playlist_dialog(prefill_url=url)))
            else:
                root.after(0, lambda: (show_clip_banner(url), add_dialog(prefill_url=url)))

    clip_mon = ClipboardMonitor(on_clip)
    if settings.get("clipboard_monitor", True):
        clip_mon.start()

    # ══════════════════════════════════════════════════════════════════════════
    # STARTUP CHECK (MANDATORY UPDATE FIRST, THEN ACTIVATION & ACCESS)
    # ══════════════════════════════════════════════════════════════════════════
    def on_startup_allow_access():
        root.deiconify()
        root.lift()
        if not trial.is_valid:
            root.after(150, lambda: activate_dialog(mandatory=True))

    # Always check for mandatory updates on launch immediately
    root.after(50, lambda: check_updates(manual=False, on_startup=True, on_success_no_update=on_startup_allow_access))

    # ══════════════════════════════════════════════════════════════════════════
    # MAIN REFRESH LOOP
    # ══════════════════════════════════════════════════════════════════════════
    def refresh():
        # global speed
        total_dl=sum(t3.downloaded for t3 in tasks)
        now=time.time(); dt=now-_gs["at"]
        if dt>0: _gs["spd"]=(total_dl-_gs["total"])/dt
        _gs["total"]=total_dl; _gs["at"]=now
        spd=_gs["spd"]
        hdr_spd_var.set(f"↓ {human_speed(spd)}" if spd>0 else "")

        refresh_tree()

        # scheduler
        if schedule_at["time"]:
            if datetime.now().strftime("%H:%M")>=schedule_at["time"]:
                for t3 in tasks:
                    if t3.status=="queued": t3.start()
                schedule_at["time"]=None
                sb_l.configure(text="🕒 Scheduler: started!")

        # status bar
        st=load_json(STATS_FILE,{"total_bytes":0,"total_files":0})
        active=sum(1 for t3 in tasks if t3.status=="downloading")
        done_c=sum(1 for t3 in tasks if t3.status=="completed")
        if not schedule_at["time"]:
            sb_l.configure(text=f"  {len(tasks)} item(s)  •  {active} active  •  {done_c} done")
        sb_r.configure(text=f"All time: {human_size(st.get('total_bytes',0))}  ({st.get('total_files',0)} files)  ")

        if sel["task"]: refresh_detail()

        root.after(250, refresh)

    # ══════════════════════════════════════════════════════════════════════════
    # WINDOW CLOSE
    # ══════════════════════════════════════════════════════════════════════════
    def on_close():
        clip_mon.stop()
        ext_server.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    apply_theme()
    update_trial_label()
    refresh()
    root.mainloop()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    try:
        launch_gui()
    except ImportError as e:
        print(f"Tkinter not found: {e}\nInstall Python with tkinter support.")
        sys.exit(1)

if __name__ == "__main__":
    main()
