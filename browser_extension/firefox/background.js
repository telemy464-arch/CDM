// CDM - Cloud Download Manager - Firefox Extension Background Script
const CDM_PORT = 19876;
const CDM_HOST = "http://127.0.0.1:" + CDM_PORT;

let extensionEnabled = true;
const DL_EXTS = ['.zip','.rar','.7z','.exe','.msi','.apk','.dmg','.iso',
                 '.pdf','.doc','.docx','.xls','.xlsx','.mp3','.flac','.wav',
                 '.mp4','.mkv','.avi','.mov','.webm','.gz','.tar','.bz2','.deb','.rpm','.torrent'];

const rt = typeof browser !== 'undefined' ? browser : chrome;

// Load saved state
rt.storage.local.get(['enabled']).then((r) => {
  if (r && r.enabled !== undefined) extensionEnabled = r.enabled;
}).catch(() => {});

// Context Menus
rt.runtime.onInstalled.addListener(() => {
  rt.contextMenus.create({
    id: "cdm_download_link",
    title: "⚡ Download with CDM",
    contexts: ["link"]
  });
  rt.contextMenus.create({
    id: "cdm_download_video",
    title: "⚡ Download Video/Audio with CDM",
    contexts: ["video", "audio"]
  });
  rt.contextMenus.create({
    id: "cdm_download_image",
    title: "⚡ Download Image with CDM",
    contexts: ["image"]
  });
});

rt.contextMenus.onClicked.addListener((info, tab) => {
  let url = info.linkUrl || info.srcUrl || info.pageUrl;
  if (url) sendToCDM(url, tab?.url);
});

// Intercept browser downloads
rt.downloads.onCreated.addListener((item) => {
  if (!extensionEnabled) return;
  const url = item.url;
  const ext = getExt(url);
  if (DL_EXTS.includes(ext) || isLargeDownload(item)) {
    rt.downloads.cancel(item.id).then(() => {
      rt.downloads.erase({ id: item.id }).catch(() => {});
      sendToCDM(url);
    }).catch(() => {});
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
  }).catch(() => {});
}

// Messages from popup / content scripts
rt.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "TOGGLE") {
    extensionEnabled = msg.value;
    rt.storage.local.set({ enabled: msg.value });
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
