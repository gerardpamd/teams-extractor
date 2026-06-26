"use strict";

// ─── Native Messaging ───
const HOST_NAME = "com.teams_extractor.writer";
let nativePort = null;
let pendingSend = null;

function connectNative() {
  nativePort = chrome.runtime.connectNative(HOST_NAME);

  nativePort.onMessage.addListener((msg) => {
    if (pendingSend) {
      pendingSend.resolve(msg);
      pendingSend = null;
    }
  });

  nativePort.onDisconnect.addListener(() => {
    nativePort = null;
    if (pendingSend) {
      pendingSend.reject(chrome.runtime.lastError?.message || "Native host disconnected");
      pendingSend = null;
    }
  });
}

function sendToNative(payload) {
  return new Promise((resolve, reject) => {
    if (!nativePort) {
      try { connectNative(); } catch (e) { return reject(e.message); }
    }
    pendingSend = { resolve, reject };
    nativePort.postMessage(payload);
  });
}

// ─── Status ───
let status = { state: "idle", lastExtracted: null, count: 0, error: null };

function setStatus(update) {
  Object.assign(status, update);
  chrome.storage.local.set({ status });
}

// ─── Message Router ───
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "GET_STATUS") {
    sendResponse(status);
    return false;
  }

  if (msg.type === "EXTRACT") {
    setStatus({ state: "extracting", error: null });

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        setStatus({ state: "error", error: "No active Teams tab found." });
        sendResponse({ ok: false, error: status.error });
        return;
      }

      chrome.tabs.sendMessage(tabs[0].id, { type: "EXTRACT" }, (data) => {
        if (chrome.runtime.lastError || !data) {
          const err = chrome.runtime.lastError?.message || "Content script did not respond.";
          setStatus({ state: "error", error: err });
          sendResponse({ ok: false, error: err });
          return;
        }
        if (data.error) {
          setStatus({ state: "error", error: data.error });
          sendResponse({ ok: false, error: data.error });
          return;
        }

        sendToNative(data)
          .then((res) => {
            setStatus({ state: "idle", lastExtracted: new Date().toISOString(), count: data.messages?.length || 0, error: null });
            sendResponse({ ok: true, res });
          })
          .catch((err) => {
            setStatus({ state: "error", error: String(err) });
            sendResponse({ ok: false, error: String(err) });
          });
      });
    });

    return true; // async response
  }

  if (msg.type === "CAPTION_CHUNK") {
    // Captions streamed from content script — buffer and forward to native host
    sendToNative(msg).catch((err) => {
      console.error("Failed to forward caption chunk:", err);
    });
    return false;
  }

  // ─── Pending Reply Routing ───

  if (msg.type === "GET_PENDING_REPLY") {
    sendToNative({ type: "READ_PENDING_REPLY" })
      .then((res) => sendResponse(res))
      .catch((err) => sendResponse({ ok: false, error: String(err) }));
    return true; // async response
  }

  if (msg.type === "DISCARD_PENDING_REPLY") {
    sendToNative({ type: "DISCARD_PENDING_REPLY" })
      .then((res) => sendResponse(res))
      .catch((err) => sendResponse({ ok: false, error: String(err) }));
    return true; // async response
  }
});
