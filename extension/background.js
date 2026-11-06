chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.get({ apiUrl: "http://127.0.0.1:5000", enabled: true, hideToxic: false }, (value) => {
    chrome.storage.sync.set(value);
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type !== "ANALYZE") return undefined;
  const url = `${message.apiUrl.replace(/\/$/, "")}/api/analyze`;
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: message.text, source: message.source || "extension" })
  })
    .then(async (response) => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Analyze failed");
      sendResponse({ ok: true, data });
    })
    .catch((error) => sendResponse({ ok: false, error: error.message }));
  return true;
});
