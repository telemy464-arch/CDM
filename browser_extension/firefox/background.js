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
browser.storage.local.get(['enabled'], (r) => {
  if (r.enabled !== undefined) extensionEnabled = r.enabled;
});

// Context Menus
browser.runtime.onInstalled.addListener(() => {
  browser.contextMenus.create({
    id: "vna_download_link",
    title: "⬇ Download with VnA",
    contexts: ["link"]
  });
  browser.contextMenus.create({
    id: "vna_download_video",
    title: "⬇ Download Video with VnA",
    contexts: ["video", "audio"]
  });
  browser.contextMenus.create({
    id: "vna_download_image",
    title: "⬇ Download Image with VnA",
    contexts: ["image"]
  });
});

browser.contextMenus.onClicked.addListener((info, tab) => {
  let url = info.linkUrl || info.srcUrl || info.pageUrl;
  if (url) sendToVnA(url, tab?.url);
});

// Intercept downloads
browser.downloads.onCreated.addListener((item) => {
  if (!extensionEnabled) return;
  const url = item.url;
  const ext = getExt(url);
  if (DL_EXTS.includes(ext) || isLargeDownload(item)) {
    browser.downloads.cancel(item.id, () => {
      browser.downloads.erase({ id: item.id });
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
    browser.tabs.create({ url });
  });
}

// Message from popup / content
browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "TOGGLE") {
    extensionEnabled = msg.value;
    browser.storage.local.set({ enabled: msg.value });
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
