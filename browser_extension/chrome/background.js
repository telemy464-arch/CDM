// CDM - Cloud Download Manager - Chrome Extension Background Service Worker
const CDM_PORT = 19876;
const CDM_HOST = "http://127.0.0.1:" + CDM_PORT;

let extensionEnabled = true;
const DL_EXTS = ['.zip','.rar','.7z','.exe','.msi','.apk','.dmg','.iso',
                 '.pdf','.doc','.docx','.xls','.xlsx','.mp3','.flac','.wav',
                 '.mp4','.mkv','.avi','.mov','.webm','.gz','.tar','.bz2','.deb','.rpm','.torrent'];

// Load saved state
chrome.storage.local.get(['enabled'], (r) => {
  if (r.enabled !== undefined) extensionEnabled = r.enabled;
});

// Context Menus
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "cdm_download_link",
    title: "⚡ Download with CDM",
    contexts: ["link"]
  });
  chrome.contextMenus.create({
    id: "cdm_download_video",
    title: "⚡ Download Video/Audio with CDM",
    contexts: ["video", "audio"]
  });
  chrome.contextMenus.create({
    id: "cdm_download_image",
    title: "⚡ Download Image with CDM",
    contexts: ["image"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  let url = info.linkUrl || info.srcUrl || info.pageUrl;
  if (url) sendToCDM(url, tab?.url);
});

// Intercept browser downloads
chrome.downloads.onCreated.addListener((item) => {
  if (!extensionEnabled) return;
  const url = item.url;
  const ext = getExt(url);
  if (DL_EXTS.includes(ext) || isLargeDownload(item)) {
    chrome.downloads.cancel(item.id, () => {
      chrome.downloads.erase({ id: item.id });
      sendToCDM(url);
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

function sendToCDM(url, referer) {
  fetch(CDM_HOST + "/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, referer: referer || "" })
  }).then(r => r.json()).then(data => {
    console.log("Sent to CDM successfully:", url);
  }).catch((err) => {
    console.warn("Could not reach CDM server:", err);
    const isVideoSite = /youtube\.com|youtu\.be|facebook\.com|tiktok\.com|instagram\.com|twitter\.com|x\.com/i.test(url);
    if (!isVideoSite && getExt(url)) {
      chrome.downloads.download({ url: url });
    }
  });
}

// Messages from popup / content scripts
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "TOGGLE") {
    extensionEnabled = msg.value;
    chrome.storage.local.set({ enabled: msg.value });
    sendResponse({ ok: true });
  }
  if (msg.type === "SEND_URL") {
    sendToCDM(msg.url, msg.referer);
    sendResponse({ ok: true });
  }
  if (msg.type === "GET_STATE") {
    sendResponse({ enabled: extensionEnabled });
  }
  return true;
});
