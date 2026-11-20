// VnA Download Manager - Chrome Extension Background Service Worker
const VNA_PORT = 19876;
const VNA_HOST = "http://127.0.0.1:" + VNA_PORT;

let extensionEnabled = true;
const VIDEO_EXTS = ['.mp4','.mkv','.webm','.avi','.mov','.flv','.m3u8','.mpd','.ts'];
const SKIP_EXTS  = ['.html','.htm','.php','.asp','.js','.css','.json','.xml','.ico'];
const DL_EXTS    = ['.zip','.rar','.7z','.exe','.msi','.apk','.dmg','.iso',
                    '.pdf','.doc','.docx','.xls','.xlsx','.mp3','.flac','.wav',
                    '.mp4','.mkv','.avi','.mov','.webm','.gz','.tar','.bz2','.deb','.rpm'];

// Load saved state
chrome.storage.local.get(['enabled'], (r) => {
  if (r.enabled !== undefined) extensionEnabled = r.enabled;
});

// Context Menus
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "cdm_download_link",
    title: "☁️ Download with CDM",
    contexts: ["link"]
  });
  chrome.contextMenus.create({
    id: "cdm_download_video",
    title: "☁️ Download Video with CDM",
    contexts: ["video", "audio"]
  });
  chrome.contextMenus.create({
    id: "cdm_download_image",
    title: "☁️ Download Image with CDM",
    contexts: ["image"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  let url = info.linkUrl || info.srcUrl || info.pageUrl;
  if (url) sendToVnA(url, tab?.url);
});

// Intercept downloads
chrome.downloads.onCreated.addListener((item) => {
  if (!extensionEnabled) return;
  const url = item.url;
  const ext = getExt(url);
  if (DL_EXTS.includes(ext) || isLargeDownload(item)) {
    chrome.downloads.cancel(item.id, () => {
      chrome.downloads.erase({ id: item.id });
      sendToVnA(url);
    });
  }
});

function isLargeDownload(item) {
  return item.fileSize > 1024 * 1024; // >1MB
}

function getExt(url) {
  try {
    const path = new URL(url).pathname;
    const dot = path.lastIndexOf('.');
    return dot >= 0 ? path.slice(dot).toLowerCase().split('?')[0] : '';
  } catch { return ''; }
}

function sendToVnA(url, referer) {
  fetch(VNA_HOST + "/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, referer: referer || "" })
  }).catch(() => {
    // VnA not running - open normally
    chrome.tabs.create({ url });
  });
}

// Message from popup / content
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "TOGGLE") {
    extensionEnabled = msg.value;
    chrome.storage.local.set({ enabled: msg.value });
    sendResponse({ ok: true });
  }
  if (msg.type === "SEND_URL") {
    sendToVnA(msg.url, msg.referer);
    sendResponse({ ok: true });
  }
  if (msg.type === "GET_STATE") {
    sendResponse({ enabled: extensionEnabled });
  }
  return true;
});
