# VnA Download Manager (CDM) v2.0 🚀
> **The Ultimate IDM-like Smart Download Manager for Windows**

[![GitHub release](https://img.shields.io/github/v/release/telemy464-arch/CDM?color=brightgreen)](https://github.com/telemy464-arch/CDM/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue)](https://github.com/telemy464-arch/CDM)
[![License](https://img.shields.io/badge/license-Proprietary-orange)](https://github.com/telemy464-arch/CDM)

---

## ⚡ Features at a Glance

### 📥 Downloading Engine
- ⚡ **Multi-Connection Segmented Download:** Up to 16 parallel threads for maximum bandwidth utilization.
- ⏸ **Full Control:** Pause, Resume, and Stop downloads anytime without data corruption.
- 🐢 **Speed Limiter:** Customize maximum download speeds or leave unlimited.
- 🗺️ **Live Chunk Map:** Real-time visual progress of each download segment.
- 🎞️ **Playlist & Media Grabber:** Integrated `yt-dlp` support for video quality selection (1080p, 720p, etc.) and audio extraction.
- 📦 **Batch Download:** Add hundreds of links at once.
- 🌐 **Site Grabber:** Automatically scan any webpage and extract all downloadable media and files.
- 🧲 **Torrent & Magnet:** Support for torrents via `aria2c`.

### 🌍 Browser Extensions
- 🔹 **Full Browser Support:** Google Chrome, Microsoft Edge, Mozilla Firefox, Brave, Opera, Vivaldi.
- 🔹 **Automatic Interception:** Captures browser downloads directly into VnA.
- 🔹 **Video Download Button:** Floating download button appears directly on web videos.
- 🔹 **Context Menu Integration:** Right-click any link or media to "Download with VnA".
- 🔹 **Extension Toggle:** Easy 1-click ON/OFF switch in extension popup.

### 🔑 Security & Licensing
- 🔑 **Microsoft-Style Product Key System:** 25-character formatted key (`XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`).
- ⏱️ **3-Day Free Trial:** Evaluation mode with full features.
- 🛡️ **Windows Defender Integration:** Automatic post-download malware scan.
- ✓ **Integrity Verification:** Check SHA-256 and MD5 checksums.

### 🎨 User Interface & Experience
- 🎨 **Modern Themes:** Dark (IDM Navy/Crimson), Light (Clean Blue), and Glass (Cyberpunk Neon).
- 🗣️ **Multilingual:** English, বাংলা (Bengali), and हिंदी (Hindi).
- 🕒 **Scheduler:** Schedule downloads to start automatically at any specific time (e.g., late-night data).
- 📊 **Analytics Dashboard:** Total data downloaded, file count, and category breakdown.
- 🔕 **Silent Mode & Notifications:** Windows toast notifications and chime sounds.
- 🔄 **GitHub Auto-Update:** Automatic notification and 1-click upgrade via `update.json`.

---

## 💻 Installation & Usage

### 1. Ready-to-use Installer (Recommended)
Download the installer from the Releases section or run:
```
VnA_Download_Manager_v2.0_Setup.exe
```
Follow the simple **Next ➔ Next ➔ Finish** wizard. Desktop shortcuts and file associations will be created automatically.

### 2. Run Directly from Source (Developers)
```bash
# 1. Clone repository
git clone https://github.com/telemy464-arch/CDM.git
cd CDM

# 2. Run without terminal window
pythonw vna_download_manager.py
# or double-click run.bat
```

### 3. Generate Product Keys
Generate unique license keys using the built-in generator:
```bash
python generate_keys.py 20
```

---

## 🌐 Browser Extension Setup

### Chrome / Edge / Brave / Opera:
1. Open `chrome://extensions` (or `edge://extensions`)
2. Turn on **Developer mode** in the top-right corner.
3. Click **Load unpacked** and select the folder:
   `browser_extension/chrome`

### Firefox:
1. Open `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on...**
3. Select `browser_extension/firefox/manifest.json`

---

## 🔄 Update System (`update.json`)
This app checks `update.json` on the `main` branch:
```
https://raw.githubusercontent.com/telemy464-arch/CDM/main/update.json
```
To push an update to your users, simply bump the `"version"` field in `update.json` and publish a new Release!

---

## 📄 License
Developed for fast, reliable, and user-friendly downloading on Windows.
