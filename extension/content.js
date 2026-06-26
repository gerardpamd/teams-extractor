"use strict";

// ─── Selector Fallback Helper ───
function querySelector(selectors, root = document) {
  for (const sel of selectors) {
    const el = root.querySelector(sel);
    if (el) return el;
  }
  return null;
}

function querySelectorAll(selectors, root = document) {
  for (const sel of selectors) {
    const els = root.querySelectorAll(sel);
    if (els.length) return Array.from(els);
  }
  return [];
}

// ─── Context Detection ───
function detectContext() {
  const url = location.href;
  if (url.includes("/channel/") || url.includes("threadType=channel")) return "channel";
  if (url.includes("/meeting/")) return "meeting";
  if (url.includes("/chat/")) return "chat";
  return "chat"; // default fallback
}

// ─── Timestamp Parser ───
function parseTimestamp(el) {
  if (!el) return "";
  return el.getAttribute("datetime") || el.title || el.textContent.trim();
}

// ─── Channel Extraction ───
function extractChannel() {
  const messageEls = Array.from(document.querySelectorAll("[data-tid='chat-pane-message']"));

  const channelNameEl = document.querySelector("h2.fui-StyledText") ||
                        document.querySelector("[data-tid='channel-name']");
  const name = channelNameEl?.textContent.trim() || "unknown-channel";

  const messages = messageEls.map((m) => {
    const mid = m.getAttribute("data-mid");
    if (!mid) return null;

    const sender    = document.getElementById("author-" + mid)?.textContent.trim() || "Unknown";
    const tsEl      = document.getElementById("timestamp-" + mid);
    const timestamp = parseTimestamp(tsEl);
    const body      = document.getElementById("content-" + mid)?.innerText.trim() || "";
    const isReply   = m.closest("[data-tid='reply-chain']") !== null ||
                      m.getAttribute("data-is-reply") === "true";

    return { sender, timestamp, body, isReply };
  }).filter((m) => m && m.body);

  return { source: "channel", name, messages };
}

// ─── Chat Extraction ───
function extractChat() {
  const messageEls = Array.from(document.querySelectorAll("[data-tid='chat-pane-message']"));

  const nameEl = document.querySelector("h2.fui-StyledText") ||
                 document.querySelector("[data-tid='chat-header-title']");
  const name = nameEl?.textContent.trim() || "unknown-chat";

  const messages = messageEls.map((m) => {
    const mid = m.getAttribute("data-mid");
    if (!mid) return null;

    const sender = document.getElementById("author-" + mid)?.textContent.trim() || "Unknown";
    const tsEl   = document.getElementById("timestamp-" + mid);
    const timestamp = parseTimestamp(tsEl);
    const body   = document.getElementById("content-" + mid)?.innerText.trim() || "";

    return { sender, timestamp, body };
  }).filter((m) => m && m.body);

  return { source: "chat", name, participants: [], messages };
}

// ─── Meeting Chat Extraction ───
function extractMeetingChat() {
  const result = extractChat();
  result.source = "meeting-chat";
  return result;
}

// ─── Live Captions ───
let captionObserver = null;
let captionBuffer = [];

function startCaptions() {
  const container = querySelector([
    "[data-tid='closed-captions-renderer']",
    "[class*='captions-container']",
    "[class*='caption-renderer']"
  ]);

  if (!container) {
    chrome.runtime.sendMessage({ type: "CAPTION_ERROR", error: "Captions container not found. Enable live captions first." });
    return;
  }

  captionBuffer = [];
  captionObserver = new MutationObserver(() => {
    const lines = querySelectorAll([
      "[data-tid='closed-caption-text']",
      "[class*='caption-text']"
    ], container);

    lines.forEach((line) => {
      if (line.dataset.teExtracted) return;
      line.dataset.teExtracted = "1";

      const speaker = querySelector(["[class*='caption-speaker']", "[data-tid='caption-speaker']"], line)
        ?.textContent.trim() || "Unknown";
      const text = line.textContent.trim();
      if (!text) return;

      const chunk = { speaker, text, timestamp: new Date().toISOString() };
      captionBuffer.push(chunk);
      chrome.runtime.sendMessage({ type: "CAPTION_CHUNK", source: "meeting-captions", chunk });
    });
  });

  captionObserver.observe(container, { childList: true, subtree: true });
}

function stopCaptions() {
  if (captionObserver) {
    captionObserver.disconnect();
    captionObserver = null;
  }
  chrome.runtime.sendMessage({
    type: "CAPTION_CHUNK",
    source: "meeting-captions",
    flush: true,
    messages: captionBuffer
  });
  captionBuffer = [];
}

// ─── SPA Navigation Detection ───
let lastHref = location.href;
setInterval(() => {
  if (location.href !== lastHref) {
    lastHref = location.href;
    if (captionObserver) stopCaptions(); // stop captions on nav
  }
}, 1000);

// ─── Staged Reply Bar ───

// Compose box fallback selectors (Teams DOM varies by version/channel/chat context).
// Run the diagnostic snippet in DevTools if none of these match:
//   document.querySelectorAll('[contenteditable="true"]') — pick the compose box element,
//   then right-click → Copy selector to get a stable path.
const COMPOSE_SELECTORS = [
  "[data-tid='ckeditor']",
  "[data-tid='compose-editor']",
  "[class*='ql-editor']",
  "[contenteditable='true'][role='textbox']",
  "[contenteditable='true'][data-tid]",
  "div[contenteditable='true']",
];

let replyPollInterval = null;

function findComposeBox() {
  return querySelector(COMPOSE_SELECTORS);
}

function removeReplyBar() {
  const existing = document.getElementById("te-reply-bar");
  if (existing) existing.remove();
}

function injectReplyBar(text) {
  // Idempotent — never show two bars
  if (document.getElementById("te-reply-bar")) return;

  // Stop polling while bar is displayed
  if (replyPollInterval) {
    clearInterval(replyPollInterval);
    replyPollInterval = null;
  }

  // ─── Build bar ───
  const bar = document.createElement("div");
  bar.id = "te-reply-bar";
  bar.style.cssText = [
    "position: fixed",
    "bottom: 80px",
    "left: 50%",
    "transform: translateX(-50%)",
    "width: 560px",
    "max-width: calc(100vw - 32px)",
    "display: flex",
    "flex-direction: column",
    "gap: 6px",
    "padding: 8px 12px",
    "background: #f3f2f1",
    "border: 1px solid #c8c6c4",
    "border-radius: 6px",
    "box-shadow: 0 4px 16px rgba(0,0,0,0.18)",
    "font-family: 'Segoe UI', sans-serif",
    "font-size: 13px",
    "color: #201f1e",
    "z-index: 999999",
    "box-sizing: border-box",
  ].join("; ");

  // Header row: label + dismiss button
  const header = document.createElement("div");
  header.style.cssText = "display: flex; align-items: center; justify-content: space-between;";

  const label = document.createElement("span");
  label.style.cssText = "font-weight: 600; font-size: 12px; color: #605e5c;";
  label.textContent = "📋 Claude Reply (staged)";

  const dismissBtn = document.createElement("button");
  dismissBtn.textContent = "✕";
  dismissBtn.title = "Discard reply";
  dismissBtn.style.cssText = [
    "background: none",
    "border: none",
    "cursor: pointer",
    "font-size: 14px",
    "color: #605e5c",
    "padding: 0 2px",
    "line-height: 1",
  ].join("; ");
  dismissBtn.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "DISCARD_PENDING_REPLY" }, () => {
      removeReplyBar();
      startReplyPoller(); // resume polling for next staged reply
    });
  });

  header.appendChild(label);
  header.appendChild(dismissBtn);

  // Preview text
  const preview = document.createElement("div");
  preview.style.cssText = [
    "background: #ffffff",
    "border: 1px solid #e1dfdd",
    "border-radius: 3px",
    "padding: 6px 8px",
    "max-height: 80px",
    "overflow-y: auto",
    "white-space: pre-wrap",
    "word-break: break-word",
    "font-size: 13px",
    "color: #201f1e",
  ].join("; ");
  preview.textContent = text;

  // Footer row: paste button
  const footer = document.createElement("div");
  footer.style.cssText = "display: flex; justify-content: flex-end;";

  const pasteBtn = document.createElement("button");
  pasteBtn.textContent = "Paste into chat →";
  pasteBtn.style.cssText = [
    "background: #6264a7",
    "color: #ffffff",
    "border: none",
    "border-radius: 3px",
    "padding: 5px 12px",
    "font-size: 13px",
    "font-family: 'Segoe UI', sans-serif",
    "cursor: pointer",
  ].join("; ");
  pasteBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(text).then(() => {
      pasteBtn.textContent = "Copied! Now press Ctrl+V in chat →";
      pasteBtn.style.background = "#107c10";
      // Auto-dismiss after 8 seconds so bar doesn't linger
      setTimeout(() => {
        removeReplyBar();
        startReplyPoller();
      }, 8000);
    }).catch(() => {
      // Clipboard API blocked — fall back to execCommand
      const box = findComposeBox();
      if (box) {
        box.focus();
        document.execCommand("insertText", false, text);
        box.dispatchEvent(new Event("input", { bubbles: true }));
      }
      removeReplyBar();
      startReplyPoller();
    });
  });

  footer.appendChild(pasteBtn);

  bar.appendChild(header);
  bar.appendChild(preview);
  bar.appendChild(footer);

  document.body.appendChild(bar);
}

function pollForPendingReply() {
  chrome.runtime.sendMessage({ type: "GET_PENDING_REPLY" }, (res) => {
    if (chrome.runtime.lastError) return; // extension context invalidated
    if (res && res.ok && res.text) {
      injectReplyBar(res.text);
    }
  });
}

function startReplyPoller() {
  if (replyPollInterval) return; // already running
  replyPollInterval = setInterval(pollForPendingReply, 3000);
}

// Kick off the poller as soon as the content script loads
startReplyPoller();

// ─── Message Listener ───
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "EXTRACT") {
    const ctx = detectContext();
    let data;
    try {
      if (ctx === "channel") data = extractChannel();
      else if (ctx === "meeting") data = extractMeetingChat();
      else data = extractChat();
    } catch (e) {
      sendResponse({ error: e.message });
      return false;
    }
    sendResponse(data);
    return false;
  }

  if (msg.type === "START_CAPTIONS") {
    startCaptions();
    sendResponse({ ok: true });
    return false;
  }

  if (msg.type === "STOP_CAPTIONS") {
    stopCaptions();
    sendResponse({ ok: true });
    return false;
  }
});
