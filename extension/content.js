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
