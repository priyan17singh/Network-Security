chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const url = tabs[0].url;
  document.getElementById("url").innerText = url;

  chrome.runtime.sendMessage(
    { action: "get_result", url },
    (response) => {
      const resultDiv = document.getElementById("result");

      if (!response || response.label === "unknown") {
        resultDiv.innerText = "⏳ Checking...";
        resultDiv.className = "neutral";
        return;
      }

      if (response.label === "phishing") {
        resultDiv.innerText = "⚠️ Phishing Website";
        resultDiv.className = "phishing";
      } else {
        resultDiv.innerText = "✅ Legitimate Website";
        resultDiv.className = "safe";
      }
    }
  );
});
