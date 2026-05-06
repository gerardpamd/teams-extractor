"""
End-to-end tests for teams_writer.py — feed JSON via stdin as a subprocess,
assert the output .md file is correct, then clean up.

Run with:  python3 -m pytest tests/test_e2e.py -v
"""

import io
import json
import os
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import pytest

# Path to the native host script
WRITER = os.path.join(os.path.dirname(__file__), "..", "native-host", "teams_writer.py")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def encode_message(payload: dict) -> bytes:
    """Encode a single native-messaging message (4-byte LE length prefix + JSON body)."""
    body = json.dumps(payload).encode("utf-8")
    return struct.pack("<I", len(body)) + body


def send_to_host(payload: dict, output_dir: str) -> dict:
    """
    Inject _settings.outputDir, encode the payload, run teams_writer.py as a
    subprocess, and return the parsed response dict.
    """
    payload = dict(payload)  # shallow copy — don't mutate caller's dict
    payload.setdefault("_settings", {})
    payload["_settings"]["outputDir"] = output_dir

    proc = subprocess.run(
        [sys.executable, WRITER],
        input=encode_message(payload),
        capture_output=True,
        timeout=10,
    )

    assert proc.returncode == 0, f"Process exited {proc.returncode}. stderr: {proc.stderr.decode()}"

    raw = proc.stdout
    assert len(raw) >= 4, "Response too short — no length prefix"
    msg_len = struct.unpack("<I", raw[:4])[0]
    return json.loads(raw[4 : 4 + msg_len].decode("utf-8"))


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmpdir():
    """Provide a temporary directory inside the home dir (required by path guard)."""
    home = os.path.expanduser("~")
    d = tempfile.mkdtemp(dir=home)
    yield d
    # Cleanup: remove all files we created then the directory
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    os.rmdir(d)


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestE2EChannel:
    PAYLOAD = {
        "source": "channel",
        "name": "general",
        "messages": [
            {"sender": "Alice", "timestamp": "2026-05-04T09:00:00Z", "body": "Hello team"},
            {"sender": "Bob",   "timestamp": "2026-05-04T09:01:00Z", "body": "Morning!",    "isReply": False},
            {"sender": "Carol", "timestamp": "2026-05-04T09:02:00Z", "body": "Ready to go", "isReply": True},
        ],
    }

    def test_response_ok(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        assert resp.get("ok") is True

    def test_output_file_exists(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        assert os.path.exists(resp["path"])

    def test_output_file_within_tmpdir(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        assert resp["path"].startswith(tmpdir)

    def test_output_filename_ends_with_md(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        assert resp["path"].endswith(".md")

    def test_count_matches_payload(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        assert resp["count"] == len(self.PAYLOAD["messages"])

    def test_frontmatter_source(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert "source: channel" in content

    def test_frontmatter_name(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert "name: general" in content

    def test_frontmatter_message_count(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert f"message_count: {len(self.PAYLOAD['messages'])}" in content

    def test_frontmatter_fenced(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        lines = open(resp["path"]).read().splitlines()
        assert lines[0] == "---"
        assert "---" in lines[1:]

    def test_message_bodies_present(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert "Hello team" in content
        assert "Morning!" in content
        assert "Ready to go" in content

    def test_reply_prefixed_with_blockquote(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        lines = content.splitlines()
        reply_lines = [l for l in lines if l.startswith("> ")]
        assert len(reply_lines) == 1
        assert "Carol" in reply_lines[0]

    def test_sender_bold_formatted(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert "**Alice**" in content
        assert "**Bob**" in content


class TestE2EChat:
    PAYLOAD = {
        "source": "chat",
        "name": "Alice, David",
        "participants": ["Alice", "David"],
        "messages": [
            {"sender": "Alice", "timestamp": "2026-05-04T14:00:00Z", "body": "Hey, review the doc?"},
            {"sender": "David", "timestamp": "2026-05-04T14:03:00Z", "body": "On it!"},
            {"sender": "Alice", "timestamp": "2026-05-04T14:04:00Z", "body": "Thanks!"},
        ],
    }

    def test_response_ok(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        assert resp.get("ok") is True

    def test_participants_in_frontmatter(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert "participants:" in content
        assert "Alice" in content
        assert "David" in content

    def test_source_is_chat(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert "source: chat" in content

    def test_all_messages_written(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        content = open(resp["path"]).read()
        assert "Hey, review the doc?" in content
        assert "On it!" in content
        assert "Thanks!" in content


class TestE2EMeetingCaptions:
    """
    Captions arrive as a flush message — different JSON shape.
    """
    PAYLOAD = {
        "flush": True,
        "source": "meeting-captions",
        "_settings": {},
        "messages": [
            {"speaker": "Alice", "timestamp": "2026-05-04T10:00:01Z", "text": "Welcome everyone"},
            {"speaker": "Bob",   "timestamp": "2026-05-04T10:00:10Z", "text": "Thanks for joining"},
            {"speaker": "Alice", "timestamp": "2026-05-04T10:00:20Z", "text": "Let's start"},
        ],
    }

    def test_response_ok(self, tmpdir):
        # For flush messages we inject outputDir differently
        payload = dict(self.PAYLOAD)
        payload["_settings"] = {"outputDir": tmpdir}
        proc = subprocess.run(
            [sys.executable, WRITER],
            input=encode_message(payload),
            capture_output=True,
            timeout=10,
        )
        assert proc.returncode == 0
        raw = proc.stdout
        resp = json.loads(raw[4:].decode("utf-8"))
        assert resp.get("ok") is True

    def test_output_file_exists(self, tmpdir):
        payload = dict(self.PAYLOAD)
        payload["_settings"] = {"outputDir": tmpdir}
        proc = subprocess.run(
            [sys.executable, WRITER],
            input=encode_message(payload),
            capture_output=True,
            timeout=10,
        )
        raw = proc.stdout
        resp = json.loads(raw[4:].decode("utf-8"))
        assert os.path.exists(resp["path"])

    def test_captions_text_in_output(self, tmpdir):
        payload = dict(self.PAYLOAD)
        payload["_settings"] = {"outputDir": tmpdir}
        proc = subprocess.run(
            [sys.executable, WRITER],
            input=encode_message(payload),
            capture_output=True,
            timeout=10,
        )
        raw = proc.stdout
        resp = json.loads(raw[4:].decode("utf-8"))
        content = open(resp["path"]).read()
        assert "Welcome everyone" in content
        assert "Thanks for joining" in content
        assert "Let's start" in content

    def test_source_is_meeting_captions(self, tmpdir):
        payload = dict(self.PAYLOAD)
        payload["_settings"] = {"outputDir": tmpdir}
        proc = subprocess.run(
            [sys.executable, WRITER],
            input=encode_message(payload),
            capture_output=True,
            timeout=10,
        )
        raw = proc.stdout
        resp = json.loads(raw[4:].decode("utf-8"))
        content = open(resp["path"]).read()
        assert "source: meeting-captions" in content


class TestE2ENamingConventions:
    PAYLOAD = {
        "source": "channel",
        "name": "general",
        "messages": [
            {"sender": "Alice", "timestamp": "2026-05-04T09:00:00Z", "body": "Test message"},
        ],
    }

    def test_by_date_default_starts_with_date(self, tmpdir):
        resp = send_to_host(self.PAYLOAD, tmpdir)
        filename = os.path.basename(resp["path"])
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert filename.startswith(date_str)

    def test_by_source_convention(self, tmpdir):
        payload = dict(self.PAYLOAD)
        payload["_settings"] = {"namingConvention": "by-source"}
        resp = send_to_host(payload, tmpdir)
        filename = os.path.basename(resp["path"])
        assert filename.startswith("channel")


class TestE2EErrorHandling:
    def test_bad_output_dir_outside_home_returns_error(self, tmpdir):
        payload = {
            "source": "channel",
            "name": "general",
            "messages": [{"sender": "A", "timestamp": "t", "body": "hi"}],
            "_settings": {"outputDir": "/tmp/evil-output"},
        }
        proc = subprocess.run(
            [sys.executable, WRITER],
            input=encode_message(payload),
            capture_output=True,
            timeout=10,
        )
        assert proc.returncode == 0  # host doesn't crash — it returns an error response
        raw = proc.stdout
        resp = json.loads(raw[4:].decode("utf-8"))
        assert resp.get("ok") is False
        assert "error" in resp

    def test_multiple_messages_in_sequence(self, tmpdir):
        """Send two payloads back-to-back in a single stdin stream."""
        p1 = {
            "source": "channel", "name": "alpha",
            "messages": [{"sender": "A", "timestamp": "t1", "body": "msg1"}],
            "_settings": {"outputDir": tmpdir},
        }
        p2 = {
            "source": "chat", "name": "beta",
            "messages": [{"sender": "B", "timestamp": "t2", "body": "msg2"}],
            "_settings": {"outputDir": tmpdir},
        }
        combined = encode_message(p1) + encode_message(p2)
        proc = subprocess.run(
            [sys.executable, WRITER],
            input=combined,
            capture_output=True,
            timeout=10,
        )
        assert proc.returncode == 0
        raw = proc.stdout

        # Parse first response
        len1 = struct.unpack("<I", raw[:4])[0]
        r1 = json.loads(raw[4 : 4 + len1])
        # Parse second response
        offset = 4 + len1
        len2 = struct.unpack("<I", raw[offset : offset + 4])[0]
        r2 = json.loads(raw[offset + 4 : offset + 4 + len2])

        assert r1.get("ok") is True
        assert r2.get("ok") is True
        assert os.path.exists(r1["path"])
        assert os.path.exists(r2["path"])
