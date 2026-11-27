const CDM_PORT = 19876;

const toggleExt = document.getElementById('toggleExt');
const urlInput  = document.getElementById('urlInput');
const btnDl     = document.getElementById('btnDl');
const statusEl  = document.getElementById('status');
const connDot   = document.getElementById('connDot');
const quality   = document.getElementById('quality');

const rt = typeof chrome !== 'undefined' ? chrome : browser;

// Load saved state
rt.runtime.sendMessage({ type: 'GET_STATE' }, (r) => {
  if (r) toggleExt.checked = r.enabled;
});

// Check CDM connection
fetch(`http://127.0.0.1:${CDM_PORT}/ping`)
  .then(r => r.ok ? setConn(true) : setConn(false))
  .catch(() => setConn(false));

function setConn(ok) {
  connDot.className = 'dot' + (ok ? '' : ' off');
  statusEl.textContent = ok ? 'CDM is connected ✓' : 'CDM app not running';
  statusEl.className = 'status ' + (ok ? 'ok' : 'err');
}

toggleExt.addEventListener('change', () => {
  rt.runtime.sendMessage({ type: 'TOGGLE', value: toggleExt.checked });
});

btnDl.addEventListener('click', () => {
  const url = urlInput.value.trim();
  if (!url) { statusEl.textContent = 'Please enter a URL'; return; }
  const ua = navigator.userAgent;
  const browser = /Firefox\//.test(ua) ? 'firefox' : (/Edg\//.test(ua) ? 'edge' : 'chrome');
  rt.runtime.sendMessage({ type: 'SEND_URL', url, referer: '', quality: quality.value, browser }, (res) => {
    if (rt.runtime.lastError || !res || !res.ok) {
      statusEl.textContent = 'Could not send — is CDM running?';
      statusEl.className = 'status err';
      return;
    }
    statusEl.textContent = 'Added to CDM ✓';
    statusEl.className = 'status ok';
    urlInput.value = '';
  });
});

// Paste current tab URL
rt.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0]?.url) urlInput.placeholder = tabs[0].url.slice(0, 50) + '...';
});
