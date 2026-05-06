# Installing Teams Extractor

This guide walks you through everything needed to get Teams Extractor running. There are two main pieces to set up: the Edge browser extension, and the native messaging host (a small bridge that lets the extension write files to your WSL filesystem).

**Total time:** about 10 minutes.

---

## Prerequisites

Before you start, confirm you have:

- **Microsoft Edge** installed on Windows (the extension does not work in Chrome or Firefox)
- **WSL** installed with Python 3 available — open a WSL terminal and run `python3 --version`. You should see something like `Python 3.12.x`. If you get an error, install Python with `sudo apt install python3`
- The `teams-extractor` project folder already in your WSL home directory at `~/teams-extractor/`

---

## Step 1 — Load the extension in Edge

The extension is not published to the Edge Add-ons store, so you load it directly from the project folder.

1. Open Microsoft Edge.
2. Type `edge://extensions` in the address bar and press Enter.
3. In the top-right corner, turn on **Developer mode** (the toggle switch).
4. Click **Load unpacked** (the button that appears after enabling Developer mode).
5. In the file browser that opens, navigate to your WSL filesystem. WSL files are accessible at `\\wsl$\Ubuntu\home\gpietryk\teams-extractor\extension` — paste that path into the folder address bar.
6. Click **Select Folder**.

The extension should now appear in your extensions list with the name "Teams Extractor".

[screenshot: Edge extensions page showing Teams Extractor loaded with Developer mode enabled]

---

## Step 2 — Copy your extension ID

After loading the extension, Edge assigns it a unique ID — a long string of letters that looks like `abcdefghijklmnopabcdefghijklmnop`. You need this ID in the next step.

1. On the `edge://extensions` page, find the Teams Extractor card.
2. Look for the line that says **ID:** followed by the long letter string.
3. Copy the full ID to your clipboard.

[screenshot: Teams Extractor extension card on edge://extensions showing the ID field]

---

## Step 3 — Update the native messaging host manifest with your extension ID

The native messaging host only accepts connections from an extension whose ID you explicitly authorize. You need to paste your extension ID into the host configuration file before registering.

1. Open a WSL terminal.
2. Open the host configuration file in a text editor:
   ```
   nano ~/teams-extractor/native-host/com.teams_extractor.writer.json
   ```
3. Find this line:
   ```
   "chrome-extension://REPLACE_WITH_EXTENSION_ID/"
   ```
4. Replace `REPLACE_WITH_EXTENSION_ID` with the ID you copied in Step 2. The result should look like:
   ```
   "chrome-extension://abcdefghijklmnopabcdefghijklmnop/"
   ```
5. Save and close: press `Ctrl+O`, then Enter, then `Ctrl+X`.

---

## Step 4 — Register the native messaging host

This step runs a PowerShell script that creates the folder and registry entry Edge needs to find the Python host.

1. Open **PowerShell** on Windows. (Press the Windows key, type `PowerShell`, and click the result. You do **not** need to run it as Administrator.)
2. Run the following command, pasting it exactly:
   ```powershell
   powershell -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu\home\gpietryk\teams-extractor\native-host\register.ps1"
   ```
3. Press Enter. The script will run and print output like:
   ```
   Registered native messaging host.
     WSL user  : gpietryk
     Host dir  : C:\teams-extractor-host
     Registry  : HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.teams_extractor.writer
   ```

**What this script does:**
- Creates the folder `C:\teams-extractor-host\` on your Windows drive
- Generates a `run_host.bat` file inside that folder — this is what Edge launches when the extension needs to write a file
- Copies your updated `com.teams_extractor.writer.json` into that folder
- Writes a Windows registry entry at `HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.teams_extractor.writer` pointing to the JSON file

You do not need to touch any of those files or the registry directly — the script handles it all.

[screenshot: PowerShell window showing the successful output from register.ps1]

---

## Step 5 — Test the connection

1. Click the Teams Extractor icon in your Edge toolbar. (If you don't see it, click the puzzle-piece icon to find it in the extensions list, then pin it.)
2. The popup opens. Look at the small colored dot in the top-right corner of the popup:
   - **Green dot** — the extension can reach the native host. Setup is complete.
   - **Grey or red dot** — something went wrong. See Troubleshooting below.

[screenshot: Teams Extractor popup with the green dot visible in the top-right corner]

---

## Troubleshooting

### Dot stays grey or red — native host not reachable

The extension cannot connect to the Python script. Most likely the registry entry is missing or points to a wrong path.

1. Open PowerShell and re-run the register.ps1 command from Step 4.
2. Close Edge completely (all windows) and reopen it. Edge reads the registry at startup.
3. Click the extension icon again and check the dot.

To manually verify the registry entry exists:
1. Press Windows key + R, type `regedit`, press Enter.
2. Navigate to `HKEY_CURRENT_USER\Software\Microsoft\Edge\NativeMessagingHosts\com.teams_extractor.writer`.
3. The default value should be `C:\teams-extractor-host\com.teams_extractor.writer.json`.

### "Content script did not respond" message

The extension can reach the native host, but it could not read the Teams page. This usually means:
- You are not on a Microsoft Teams page (`teams.microsoft.com`) — navigate to Teams first, then click the extension.
- Teams has not finished loading — wait a few seconds for the page to fully appear, then try again.

### Python not found — WSL path issue

The `run_host.bat` file calls `wsl.exe python3`. If your WSL distribution does not have Python 3, install it:
1. Open a WSL terminal.
2. Run: `sudo apt update && sudo apt install python3`
3. Re-run the register.ps1 script to regenerate `run_host.bat` (it detects your WSL username automatically).

### Extension ID changed

If you reload the extension or reinstall it, Edge may assign a new ID. The old ID in the host manifest will no longer match, and the connection will fail.

1. Go back to Step 2 to copy the new ID.
2. Go back to Step 3 to update `com.teams_extractor.writer.json`.
3. Go back to Step 4 to re-run `register.ps1` (this copies the updated JSON into `C:\teams-extractor-host\`).
4. Restart Edge.
