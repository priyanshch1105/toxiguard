const apiUrl = document.getElementById("apiUrl");
const enabled = document.getElementById("enabled");
const hideToxic = document.getElementById("hideToxic");
const statusEl = document.getElementById("status");
const siteChip = document.getElementById("siteChip");

function currentSite(url) {
  if (!url) return "Unknown";
  if (url.includes("youtube.com")) return "YouTube";
  if (url.includes("linkedin.com")) return "LinkedIn";
  if (url.includes("web.whatsapp.com")) return "WhatsApp Web";
  return "Unsupported";
}

async function sendToTab(message) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return null;
  siteChip.textContent = currentSite(tab.url || "");
  try {
    return await chrome.tabs.sendMessage(tab.id, message);
  } catch (error) {
    return { error: "Open YouTube, LinkedIn, or WhatsApp Web, then click Scan." };
  }
}

async function load() {
  const stored = await chrome.storage.sync.get({
    apiUrl: "http://127.0.0.1:5000",
    enabled: true,
    hideToxic: false
  });
  apiUrl.value = stored.apiUrl;
  enabled.checked = stored.enabled;
  hideToxic.checked = stored.hideToxic;
  const stats = await sendToTab({ type: "GET_STATS" });
  if (stats && !stats.error) {
    document.getElementById("scanned").textContent = stats.scanned || 0;
    document.getElementById("safe").textContent = stats.safe || 0;
    document.getElementById("toxic").textContent = stats.toxic || 0;
  }
}

async function persist() {
  await chrome.storage.sync.set({
    apiUrl: apiUrl.value.trim().replace(/\/$/, ""),
    enabled: enabled.checked,
    hideToxic: hideToxic.checked
  });
  await sendToTab({
    type: "UPDATE_SETTINGS",
    apiUrl: apiUrl.value.trim().replace(/\/$/, ""),
    enabled: enabled.checked,
    hideToxic: hideToxic.checked
  });
}

apiUrl.addEventListener("change", persist);
enabled.addEventListener("change", persist);
hideToxic.addEventListener("change", persist);

document.getElementById("scanNow").addEventListener("click", async () => {
  statusEl.textContent = "Scanning...";
  await persist();
  const result = await sendToTab({ type: "SCAN_NOW" });
  if (result?.error) {
    statusEl.textContent = result.error;
    return;
  }
  document.getElementById("scanned").textContent = result.scanned || 0;
  document.getElementById("safe").textContent = result.safe || 0;
  document.getElementById("toxic").textContent = result.toxic || 0;
  statusEl.textContent = `Done. ${result.scanned || 0} messages checked.`;
});

load();
