// VnA Download Manager - Content Script
// Adds download buttons on video elements and detects streaming media

(function () {
  'use strict';

  const VIDEO_PATTERNS = /\.(mp4|mkv|webm|avi|mov|flv|m3u8|mpd|ts|aac|mp3|flac)/i;

  // Add download button overlay on video elements
  function addVideoButtons() {
    document.querySelectorAll('video:not([data-vna])').forEach(video => {
      video.setAttribute('data-vna', '1');
      const src = video.src || video.querySelector('source')?.src;
      if (!src) return;

      const btn = document.createElement('button');
      btn.textContent = '☁️ CDM';
      btn.title = 'Download with CDM (Cloud Download Manager)';
      btn.style.cssText = `
        position:absolute; z-index:99999; top:8px; right:8px;
        background:linear-gradient(135deg,#e94560,#533483);
        color:#fff; border:none; border-radius:6px;
        padding:5px 12px; font-size:13px; font-weight:bold;
        cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,0.5);
      `;
      btn.onclick = (e) => {
        e.stopPropagation();
        chrome.runtime.sendMessage({ type: 'SEND_URL', url: src, referer: location.href });
        btn.textContent = '✓ Sent!';
        btn.style.background = '#00c851';
        setTimeout(() => { btn.textContent = '☁️ CDM'; btn.style.background = 'linear-gradient(135deg,#e94560,#533483)'; }, 2000);
      };

      const wrapper = video.parentElement;
      if (wrapper) {
        const cs = getComputedStyle(wrapper);
        if (cs.position === 'static') wrapper.style.position = 'relative';
        wrapper.appendChild(btn);
      }
    });
  }

  // Network request interceptor for streaming
  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    if (typeof url === 'string' && VIDEO_PATTERNS.test(url)) {
      window.postMessage({ type: 'VNA_STREAM_URL', url }, '*');
    }
    return origOpen.apply(this, arguments);
  };

  // Run on page load and mutations
  addVideoButtons();
  const obs = new MutationObserver(() => addVideoButtons());
  obs.observe(document.body || document.documentElement, { childList: true, subtree: true });

})();
