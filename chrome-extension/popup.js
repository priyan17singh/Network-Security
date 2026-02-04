chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const url = tabs[0].url;
  document.getElementById("url").innerText = url;

  const resultDiv = document.getElementById("result");
  const statusText = resultDiv.querySelector(".status-text");
  const statusIcon = resultDiv.querySelector(".status-icon");

  chrome.runtime.sendMessage(
    { action: "get_result", url },
    (response) => {
      if (!response || response.label === "unknown") {
        resultDiv.className = "status neutral";
        statusText.innerText = "Checking...";
        statusIcon.innerText = "⏳";
        return;
      }

      if (response.label === "phishing") {
        resultDiv.className = "status phishing";
        statusText.innerText = "Phishing Website";
        statusIcon.innerText = "⚠️";
      } else {
        resultDiv.className = "status safe";
        statusText.innerText = "Legitimate Website";
        statusIcon.innerText = "✅";
      }
    }
  );
});
