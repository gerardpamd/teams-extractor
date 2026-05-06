"use strict";

// ─── Storage Helpers ───
function storageGet(keys) {
  return new Promise((res) => chrome.storage.local.get(keys, res));
}
function storageSet(data) {
  return new Promise((res) => chrome.storage.local.set(data, res));
}

// ─── DOM Refs ───
const hostDot        = document.getElementById("hostDot");
const btnExtract     = document.getElementById("btnExtract");
const btnCaption     = document.getElementById("btnCaptionToggle");
const statusMsg      = document.getElementById("statusMsg");
const lastExtracted  = document.getElementById("lastExtracted");
const outputDir      = document.getElementById("outputDir");
const namingConv     = document.getElementById("namingConvention");
const scopeSel       = document.getElementById("scope");
const btnSave        = document.getElementById("btnSaveSettings");

let captureActive = false;

// ─── Status Display ───
function showStatus(msg, color = "") {
  statusMsg.textContent = msg;
  statusMsg.style.color = color || "";
}

function updateHostDot(state) {
  hostDot.className = "dot";
  if (state === "idle") hostDot.classList.add("dot--ok");
  else if (state === "error") hostDot.classList.add("dot--error");
  else hostDot.classList.add("dot--unknown");
  hostDot.title = state === "idle" ? "Native host connected" :
                  state === "error" ? "Native host error" : "Unknown";
}

async function refreshStatus() {
  const { status } = await storageGet("status");
  if (!status) return;
  updateHostDot(status.state === "error" ? "error" : "idle");
  if (status.error) showStatus(status.error, "#f38ba8");
  if (status.lastExtracted) {
    const d = new Date(status.lastExtracted);
    lastExtracted.textContent = `Last: ${d.toLocaleTimeString()} — ${status.count} messages`;
  }
}

// ─── Load Settings ───
async function loadSettings() {
  const { settings } = await storageGet("settings");
  if (!settings) return;
  outputDir.value    = settings.outputDir    || "";
  namingConv.value   = settings.namingConvention || "by-date";
  scopeSel.value     = settings.scope        || "current";
}

// ─── Save Settings ───
btnSave.addEventListener("click", async () => {
  await storageSet({
    settings: {
      outputDir:         outputDir.value.trim() || "~/teams-extractor/data/",
      namingConvention:  namingConv.value,
      scope:             scopeSel.value
    }
  });
  showStatus("Settings saved.", "#a6e3a1");
  setTimeout(() => showStatus("Ready."), 1500);
});

// ─── Extract ───
btnExtract.addEventListener("click", () => {
  btnExtract.disabled = true;
  showStatus("Extracting…");

  chrome.runtime.sendMessage({ type: "EXTRACT" }, (res) => {
    btnExtract.disabled = false;
    if (chrome.runtime.lastError || !res?.ok) {
      showStatus(res?.error || "Extraction failed.", "#f38ba8");
    } else {
      showStatus("Extraction complete.", "#a6e3a1");
      refreshStatus();
    }
  });
});

// ─── Caption Toggle ───
btnCaption.addEventListener("click", () => {
  captureActive = !captureActive;
  btnCaption.textContent = captureActive ? "Stop Caption Capture" : "Start Caption Capture";
  btnCaption.style.background = captureActive ? "#f38ba8" : "";
  btnCaption.style.color      = captureActive ? "#1e1e2e" : "";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return;
    chrome.tabs.sendMessage(tabs[0].id, {
      type: captureActive ? "START_CAPTIONS" : "STOP_CAPTIONS"
    });
  });
});

// ─── Init ───
loadSettings();
refreshStatus();
