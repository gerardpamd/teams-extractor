#!/usr/bin/env python3
"""Native Messaging Host — receives JSON from the Teams Extractor extension and writes .md files."""

import json
import os
import struct
import sys
from datetime import datetime, timezone

# ─── Native Messaging Protocol ───

def read_message():
    raw_len = sys.stdin.buffer.read(4)
    if len(raw_len) < 4:
        return None
    msg_len = struct.unpack("<I", raw_len)[0]
    data = sys.stdin.buffer.read(msg_len)
    return json.loads(data.decode("utf-8"))

def write_message(payload):
    encoded = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

# ─── Path Helpers ───

_HOME = os.path.expanduser("~")

def resolve_output_dir(settings):
    raw = settings.get("outputDir", "~/teams-extractor/data/")
    resolved = os.path.realpath(os.path.expanduser(raw))
    # Confine writes to home directory
    if not resolved.startswith(_HOME):
        raise ValueError(f"Output directory must be within home directory: {resolved}")
    return resolved

def safe_filename(value):
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in value).strip().replace(" ", "-")

def build_filepath(output_dir, source, name, convention):
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_source = safe_filename(source) or "unknown"
    safe_name   = safe_filename(name)   or "unknown"

    if convention == "by-date":
        filename = f"{date_str}_{safe_source}_{safe_name}.md"
    else:
        filename = f"{safe_source}_{safe_name}_{date_str}.md"

    return os.path.join(output_dir, filename)

# ─── Markdown Conversion ───

def messages_to_markdown(data):
    source      = data.get("source", "unknown")
    name        = data.get("name", "unknown")
    participants = data.get("participants", [])
    messages    = data.get("messages", [])
    extracted   = datetime.now(timezone.utc).isoformat()

    lines = [
        "---",
        f"source: {source}",
        f"name: {name}",
    ]
    if participants:
        lines.append(f"participants: [{', '.join(participants)}]")
    lines += [
        f"extracted: {extracted}",
        f"message_count: {len(messages)}",
        "---",
        "",
    ]

    for msg in messages:
        sender    = msg.get("sender", "Unknown")
        timestamp = msg.get("timestamp", "")
        body      = msg.get("body", "").strip()
        is_reply  = msg.get("isReply", False)

        ts_part = f" ({timestamp})" if timestamp else ""
        line = f"**{sender}**{ts_part}: {body}"
        if is_reply:
            line = "> " + line
        lines.append(line)
        lines.append("")

    return "\n".join(lines)

# ─── Main Loop ───

def main():
    while True:
        try:
            msg = read_message()
        except Exception as e:
            write_message({"ok": False, "error": f"Failed to read message: {e}"})
            continue

        if msg is None:
            break

        try:
            # Caption flush message — reconstruct as standard data dict, preserving settings
            if msg.get("flush"):
                data = {
                    "source":    msg.get("source", "meeting-captions"),
                    "name":      "meeting-captions",
                    "_settings": msg.get("_settings", {}),
                    "messages": [
                        {"sender": c["speaker"], "timestamp": c["timestamp"], "body": c["text"]}
                        for c in msg.get("messages", [])
                    ]
                }
            else:
                data = msg

            settings   = data.get("_settings", {})
            output_dir = resolve_output_dir(settings)
            convention = settings.get("namingConvention", "by-date")
            filepath   = build_filepath(output_dir, data.get("source", "unknown"), data.get("name", "unknown"), convention)
            markdown   = messages_to_markdown(data)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown)

            write_message({"ok": True, "path": filepath, "count": len(data.get("messages", []))})

        except Exception as e:
            write_message({"ok": False, "error": str(e)})

if __name__ == "__main__":
    main()
