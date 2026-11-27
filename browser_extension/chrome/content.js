// CDM - Cloud Download Manager - Content Script
// Adds IDM-style floating download button with quality selection dropdown on video players

(function () {
  'use strict';

  function isYouTube() {
    return location.hostname.includes('youtube.com') || location.hostname.includes('youtu.be');
  }

  function isFacebook() {
    return location.hostname.includes('facebook.com') || location.hostname.includes('fb.watch');
  }

  function currentBrowser() {
    const ua = navigator.userAgent;
    if (/Firefox\//.test(ua)) return 'firefox';
    if (/Edg\//.test(ua)) return 'edge';
    return 'chrome';
  }

  const QUALITIES = [
    { id: 'best', label: '🌟 Best Quality (Auto)' },
    { id: '1080p', label: '🎬 1080p (Full HD)' },
    { id: '720p', label: '🎬 720p (HD)' },
    { id: '480p', label: '🎬 480p (SD)' },
    { id: '4k', label: '🎬 4K (2160p)' },
    { id: '2k', label: '🎬 2K (1440p)' },
    { id: 'audio', label: '🎵 Audio Only (MP3)' }
  ];

  function getTargetUrl(videoEl) {
    if (isYouTube() || isFacebook()) {
      return location.href;
    }
    return videoEl?.currentSrc || videoEl?.src || videoEl?.querySelector('source')?.src || location.href;
  }

  function startDownload(targetUrl, quality = 'best', statusBtn) {
    if (!statusBtn) return;
    const originalHtml = `
      <div style="display:flex;align-items:center;gap:6px;">
        <span style="font-size:14px;">⚡</span>
        <span>Download Video (CDM)</span>
      </div>
    `;

    statusBtn.innerHTML = `<span>⏳ Starting Download...</span>`;
    statusBtn.style.background = '#ffc107';
    statusBtn.style.color = '#000000';

    chrome.runtime.sendMessage({
      type: 'SEND_URL',
      url: targetUrl,
      referer: location.href,
      quality: quality,
      browser: currentBrowser()
    }, (res) => {
      if (chrome.runtime.lastError || !res || !res.ok) {
        statusBtn.innerHTML = `<span>⚠ CDM is not connected</span>`;
        statusBtn.style.background = '#b42318';
        statusBtn.style.color = '#ffffff';
        setTimeout(() => {
          statusBtn.innerHTML = originalHtml;
          statusBtn.style.background = 'linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%)';
          statusBtn.style.color = '#ffffff';
        }, 3000);
      } else {
        statusBtn.innerHTML = `<span>⚡ Downloading in CDM!</span>`;
        statusBtn.style.background = '#198754';
        statusBtn.style.color = '#ffffff';

        setTimeout(() => {
          statusBtn.innerHTML = originalHtml;
          statusBtn.style.background = 'linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%)';
          statusBtn.style.color = '#ffffff';
        }, 3000);
      }
    });
  }

  // Create IDM-style floating download widget
  function createDownloadButton(videoEl) {
    if (videoEl.dataset.cdmAttached) return;
    videoEl.dataset.cdmAttached = 'true';

    const widget = document.createElement('div');
    widget.className = 'cdm-download-btn-overlay';
    widget.style.cssText = `
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 2147483647;
      display: inline-flex;
      align-items: stretch;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 13px;
      font-weight: 600;
      border-radius: 6px;
      box-shadow: 0 4px 14px rgba(0,0,0,0.45);
      border: 1px solid rgba(255,255,255,0.3);
      user-select: none;
      transition: all 0.2s ease;
      opacity: 0.95;
    `;

    // Main download button
    const mainBtn = document.createElement('div');
    mainBtn.style.cssText = `
      display: flex;
      align-items: center;
      gap: 6px;
      background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%);
      color: #ffffff;
      padding: 6px 12px;
      border-top-left-radius: 5px;
      border-bottom-left-radius: 5px;
      cursor: pointer;
      transition: background 0.2s;
    `;
    mainBtn.title = "Download this video in CDM (Cloud Download Manager)";
    mainBtn.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;">
        <span style="font-size:14px;">⚡</span>
        <span>Download Video (CDM)</span>
      </div>
    `;

    // Dropdown arrow button
    const arrowBtn = document.createElement('div');
    arrowBtn.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      background: #084298;
      color: #ffffff;
      padding: 0 9px;
      border-top-right-radius: 5px;
      border-bottom-right-radius: 5px;
      cursor: pointer;
      border-left: 1px solid rgba(255,255,255,0.25);
      font-size: 11px;
    `;
    arrowBtn.title = "Select video quality/resolution";
    arrowBtn.innerHTML = `▼`;

    // Quality dropdown menu
    const menu = document.createElement('div');
    menu.style.cssText = `
      position: absolute;
      top: 100%;
      right: 0;
      margin-top: 4px;
      background: #1e1e24;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 6px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6);
      display: none;
      flex-direction: column;
      min-width: 175px;
      padding: 4px 0;
      z-index: 2147483647;
    `;

    QUALITIES.forEach(q => {
      const item = document.createElement('div');
      item.style.cssText = `
        padding: 7px 14px;
        color: #f0f0f0;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.15s;
        display: flex;
        align-items: center;
        gap: 6px;
      `;
      item.innerText = q.label;
      item.onmouseenter = () => { item.style.background = '#0d6efd'; };
      item.onmouseleave = () => { item.style.background = 'transparent'; };
      item.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        menu.style.display = 'none';
        const targetUrl = getTargetUrl(videoEl);
        startDownload(targetUrl, q.id, mainBtn);
      };
      menu.appendChild(item);
    });

    widget.appendChild(mainBtn);
    widget.appendChild(arrowBtn);
    widget.appendChild(menu);

    mainBtn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      menu.style.display = 'none';
      const targetUrl = getTargetUrl(videoEl);
      startDownload(targetUrl, 'best', mainBtn);
    };

    arrowBtn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
    };

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!widget.contains(e.target)) {
        menu.style.display = 'none';
      }
    });

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
      container.appendChild(widget);
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
