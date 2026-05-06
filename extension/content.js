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
  const messages = querySelectorAll([
    "[data-tid='message-body']",
    ".ts-message-list-item",
    "[class*='message-body']"
  ]);

  const channelNameEl = querySelector([
    "[data-tid='channel-name']",
    ".channel-name",
    "h1[class*='channel']"
  ]);
  const name = channelNameEl?.textContent.trim() || "unknown-channel";

  return {
    source: "channel",
    name,
    messages: messages.map((m) => {
      const sender = querySelector([
        "[data-tid='message-author-name']",
        ".author",
        "[class*='author-name']"
      ], m)?.textContent.trim() || "Unknown";

      const tsEl = querySelector(["time", "[data-tid='message-timestamp']"], m);
      const timestamp = parseTimestamp(tsEl);

      const body = querySelector([
        "[data-tid='message-body-content']",
        ".message-body",
        "[class*='message-content']"
      ], m)?.innerText.trim() || "";

      const isReply = m.closest("[data-tid='reply-chain']") !== null ||
        m.closest("[class*='reply-chain']") !== null ||
        m.getAttribute("data-is-reply") === "true";

      return { sender, timestamp, body, isReply };
    }).filter((m) => m.body)
  };
}

// ─── Chat Extraction ───
function extractChat() {
  const messages = querySelectorAll([
    "[data-tid='message-body']",
    ".ts-message-list-item",
    "[class*='chat-message']"
  ]);

  const participantEls = querySelectorAll([
    "[data-tid='chat-header-participant']",
    "[class*='participant-name']"
  ]);
  const participants = participantEls.map((p) => p.textContent.trim());

  const nameEl = querySelector([
    "[data-tid='chat-header-title']",
    ".chat-title",
    "[class*='conversation-title']"
  ]);
  const name = nameEl?.textContent.trim() || participants.join(", ") || "unknown-chat";

  return {
    source: "chat",
    name,
    participants,
    messages: messages.map((m) => {
      const sender = querySelector([
        "[data-tid='message-author-name']",
        ".author",
        "[class*='author-name']"
      ], m)?.textContent.trim() || "Unknown";

      const tsEl = querySelector(["time", "[data-tid='message-timestamp']"], m);
      const timestamp = parseTimestamp(tsEl);

      const body = querySelector([
        "[data-tid='message-body-content']",
        ".message-body",
        "[class*='message-content']"
      ], m)?.innerText.trim() || "";

      return { sender, timestamp, body };
    }).filter((m) => m.body)
  };
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
