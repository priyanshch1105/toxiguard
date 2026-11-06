const SELECTORS = {
  youtube: [
    "ytd-comment-view-model #content-text",
    "ytd-comment-renderer #content-text"
  ],
  linkedin: [
    ".comments-comment-item__main-content",
    ".feed-shared-update-v2__description",
    ".update-components-text"
  ],
  whatsapp: [
    "span.selectable-text.copyable-text",
    "div.copyable-text span.selectable-text"
  ]
};

const stats = { scanned: 0, safe: 0, toxic: 0 };
const analyzed = new WeakSet();
let settings = { apiUrl: "http://127.0.0.1:5000", enabled: true, hideToxic: false };
let scanTimer = null;

function detectPlatform() {
  const host = location.hostname;
  if (host.includes("youtube.com")) return "youtube";
  if (host.includes("linkedin.com")) return "linkedin";
  if (host.includes("whatsapp.com")) return "whatsapp";
  return null;
}

function visibleText(node) {
  return (node.innerText || node.textContent || "").replace(/\s+/g, " ").trim();
}

function badgeClass(result) {
  if (result.moderation_result === "BLOCK") return "sg-block";
  if (result.moderation_result === "REVIEW") return "sg-review";
  return "sg-safe";
}

function attachBadge(node, result) {
  if (node.parentElement?.querySelector(":scope > .sg-badge")) return;
  const badge = document.createElement("span");
  badge.className = `sg-badge ${badgeClass(result)}`;
  badge.textContent = result.is_toxic ? result.moderation_result : "SAFE";
  const labels = result.triggered_labels?.length ? result.triggered_labels.join(", ") : "No toxicity labels";
  badge.title = `${labels} · ${Math.round((result.max_confidence || 0) * 100)}%`;
  node.insertAdjacentElement("afterend", badge);
  if (settings.hideToxic && result.is_toxic) node.classList.add("sg-blur");
}

function analyzeText(text, source) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      { type: "ANALYZE", apiUrl: settings.apiUrl, text, source },
      (response) => resolve(response || { ok: false, error: "No response from extension" })
    );
  });
}

async function scanNode(node, source) {
  if (!settings.enabled || analyzed.has(node)) return;
  const text = visibleText(node);
  if (text.length < 8 || text.length > 2000) return;
  analyzed.add(node);
  const response = await analyzeText(text, source);
  if (!response.ok) return;
  stats.scanned += 1;
  if (response.data.is_toxic) stats.toxic += 1;
  else stats.safe += 1;
  attachBadge(node, response.data);
}

async function scanPage() {
  const platform = detectPlatform();
  if (!platform || !settings.enabled) return stats;
  const nodes = document.querySelectorAll(SELECTORS[platform].join(","));
  let pending = 0;
  for (const node of nodes) {
    if (analyzed.has(node)) continue;
    pending += 1;
    await scanNode(node, `extension-${platform}`);
    if (pending >= 12) break;
  }
  return stats;
}

function queueScan() {
  clearTimeout(scanTimer);
  scanTimer = setTimeout(() => {
    scanPage();
  }, 900);
}

chrome.storage.sync.get(settings, (value) => {
  settings = { ...settings, ...value };
  queueScan();
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "GET_STATS") {
    sendResponse(stats);
    return;
  }
  if (message.type === "UPDATE_SETTINGS") {
    settings = { ...settings, ...message };
    document.querySelectorAll(".sg-blur").forEach((el) => {
      if (!settings.hideToxic) el.classList.remove("sg-blur");
    });
    queueScan();
    sendResponse({ ok: true });
    return;
  }
  if (message.type === "SCAN_NOW") {
    scanPage().then(sendResponse);
    return true;
  }
  return undefined;
});

const observer = new MutationObserver(queueScan);
observer.observe(document.body, { childList: true, subtree: true });
queueScan();
