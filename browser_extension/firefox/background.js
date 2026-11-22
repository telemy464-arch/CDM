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

const IGNORE_EXTS = ['.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.json', '.xml', '.js', '.css'];

// Intercept browser downloads
rt.downloads.onCreated.addListener((item) => {
  if (!extensionEnabled) return;
  const url = item.url || "";
  if (url.startsWith("blob:") || url.startsWith("data:")) return;

  const isVideoSite = /youtube\.com|youtu\.be|facebook\.com|tiktok\.com|instagram\.com|twitter\.com|x\.com/i.test(url);
  if (isVideoSite) return;

  const ext = getExt(url);
  if (IGNORE_EXTS.includes(ext) || item.mime === "text/html" || item.mime === "application/xhtml+xml") {
    return;
  }

  if (DL_EXTS.includes(ext) || isLargeDownload(item)) {
    rt.downloads.cancel(item.id).then(() => {
      rt.downloads.erase({ id: item.id }).catch(() => {});
      sendToCDM(url);
    }).catch(() => {});
  }
});

function isLargeDownload(item) {
  if (item.mime === "text/html" || item.mime === "application/xhtml+xml") return false;
  const ext = getExt(item.url || "");
  if (IGNORE_EXTS.includes(ext)) return false;
  return item.fileSize > 2 * 1024 * 1024; // >2MB
}

function getExt(url) {
  try {
    const path = new URL(url).pathname;
    const dot = path.lastIndexOf('.');
    return dot >= 0 ? path.slice(dot).toLowerCase().split('?')[0] : '';
  } catch { return ''; }
}

function sendToCDM(url, referer, quality) {
  return fetch(CDM_HOST + "/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      referer: referer || "",
      quality: quality || "best",
      autostart: true
    })
  }).then(r => {
    if (!r.ok) throw new Error("HTTP error " + r.status);
    return r.json();
  });
}

// Messages from popup / content scripts
rt.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "TOGGLE") {
    extensionEnabled = msg.value;
    rt.storage.local.set({ enabled: msg.value });
    sendResponse({ ok: true });
    return false;
  }
  if (msg.type === "SEND_URL") {
    sendToCDM(msg.url, msg.referer, msg.quality)
      .then(data => {
        sendResponse({ ok: true, data });
      })
      .catch(err => {
        sendResponse({ ok: false, error: err.message || "CDM unreachable" });
      });
    return true;
  }
  if (msg.type === "GET_STATE") {
    sendResponse({ enabled: extensionEnabled });
    return false;
  }
  return true;
});
