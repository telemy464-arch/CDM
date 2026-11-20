// CDM - Cloud Download Manager - Content Script (Firefox)
// Adds IDM-style floating download buttons on video elements and streaming media

(function () {
  'use strict';

  const CDM_PORT = 19876;
  const VIDEO_EXTS = /\.(mp4|mkv|webm|avi|mov|flv|m3u8|mpd|ts|aac|mp3|flac|m4a|m4v)/i;

  function isYouTube() {
    return location.hostname.includes('youtube.com') || location.hostname.includes('youtu.be');
  }

  function isFacebook() {
    return location.hostname.includes('facebook.com') || location.hostname.includes('fb.watch');
  }

  // Create IDM-style floating download button
  function createDownloadButton(videoEl) {
    if (videoEl.dataset.cdmAttached) return;
    videoEl.dataset.cdmAttached = 'true';

    const btn = document.createElement('div');
    btn.className = 'cdm-download-btn-overlay';
    btn.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;">
        <span style="font-size:14px;">⚡</span>
        <span>Download Video (CDM)</span>
      </div>
    `;
    btn.title = "Download this video with CDM (Cloud Download Manager)";
    btn.style.cssText = `
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 2147483647;
      background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%);
      color: #ffffff;
      padding: 6px 14px;
      border-radius: 6px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.25);
      user-select: none;
      transition: all 0.2s ease;
      opacity: 0.92;
    `;

    btn.onmouseenter = () => {
      btn.style.opacity = '1.0';
      btn.style.transform = 'scale(1.04)';
      btn.style.boxShadow = '0 6px 16px rgba(13,110,253,0.6)';
    };
    btn.onmouseleave = () => {
      btn.style.opacity = '0.92';
      btn.style.transform = 'scale(1.0)';
      btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.4)';
    };

    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();

      let targetUrl = '';
      if (isYouTube() || isFacebook()) {
        targetUrl = location.href;
      } else {
        targetUrl = videoEl.currentSrc || videoEl.src || videoEl.querySelector('source')?.src || location.href;
      }

      btn.innerHTML = `<span>⏳ Sending to CDM...</span>`;
      btn.style.background = '#ffc107';
      btn.style.color = '#000000';

      const rt = (typeof chrome !== 'undefined' ? chrome : browser).runtime;
      rt.sendMessage({
        type: 'SEND_URL',
        url: targetUrl,
        referer: location.href
      }, (res) => {
        btn.innerHTML = `<span>✓ Sent to CDM!</span>`;
        btn.style.background = '#198754';
        btn.style.color = '#ffffff';
        setTimeout(() => {
          btn.innerHTML = `
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-size:14px;">⚡</span>
              <span>Download Video (CDM)</span>
            </div>
          `;
          btn.style.background = 'linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%)';
        }, 2500);
      });
    };

    // Attach to video container
    let container = videoEl.parentElement;
    if (isYouTube()) {
      container = document.querySelector('#movie_player') || document.querySelector('.html5-video-player') || container;
    }
    if (container) {
      const pos = getComputedStyle(container).position;
      if (pos === 'static') {
        container.style.position = 'relative';
      }
      container.appendChild(btn);
    }
  }

  // Scan and attach to all videos
  function attachVideoButtons() {
    const videos = document.querySelectorAll('video');
    videos.forEach(v => {
      if (!v.dataset.cdmAttached) {
        createDownloadButton(v);
      }
    });
  }

  // Monitor DOM changes for dynamic video loading (like YouTube SPA navigations)
  attachVideoButtons();
  const observer = new MutationObserver(() => {
    attachVideoButtons();
  });
  observer.observe(document.body || document.documentElement, {
    childList: true,
    subtree: true
  });

  // Re-check on URL change (YouTube SPA)
  let lastUrl = location.href;
  setInterval(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      document.querySelectorAll('[data-cdm-attached]').forEach(el => {
        delete el.dataset.cdmAttached;
      });
      document.querySelectorAll('.cdm-download-btn-overlay').forEach(el => el.remove());
      attachVideoButtons();
    }
  }, 1000);

})();
