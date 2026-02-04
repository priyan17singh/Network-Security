console.log("Phishing Detector background running");

const urlCache = new Map();

// -----------------------------
// Respond to popup requests
// -----------------------------
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "get_result") {
    const label = urlCache.get(request.url) || "unknown";
    sendResponse({ label });
  }
});

// -----------------------------
// Listen for tab URL changes
// -----------------------------
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (
    changeInfo.status !== "complete" ||
    !tab.url ||
    !tab.url.startsWith("http")
  ) return;

  checkURL(tab.url);
});

chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const tab = await chrome.tabs.get(activeInfo.tabId);
  if (tab.url && tab.url.startsWith("http")) {
    checkURL(tab.url);
  }
});

// -----------------------------
// Core URL checking logic
// -----------------------------
async function checkURL(url) {
  if (
    urlCache.has(url) ||
    url.startsWith("chrome://") ||
    url.startsWith("file://")
  ) return;

  try {
    const res = await fetch("http://localhost:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await res.json();
    const label = data.label || "unknown";

    urlCache.set(url, label);
    updateBadge(label);

    if (label === "phishing") {
      showPhishingNotification(url);
    }

  } catch (err) {
    console.error("Prediction error:", err);
  }
}

// -----------------------------
// Notification
// -----------------------------
function showPhishingNotification(url) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: chrome.runtime.getURL("icon1.png"),
    title: "⚠️ Phishing Website Detected",
    message: `This website may steal your data:\n${url}`,
    priority: 2,
  });
}

// -----------------------------
// Badge
// -----------------------------
function updateBadge(label) {
  if (label === "phishing") {
    chrome.action.setBadgeText({ text: "!" });
    chrome.action.setBadgeBackgroundColor({ color: "#d93025" });
  } else if (label === "legitimate") {
    chrome.action.setBadgeText({ text: "OK" });
    chrome.action.setBadgeBackgroundColor({ color: "#188038" });
  } else {
    chrome.action.setBadgeText({ text: "?" });
    chrome.action.setBadgeBackgroundColor({ color: "#888" });
  }
}

