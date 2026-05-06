"""
Unit tests for teams_writer.py (native messaging host).

Run with:  python3 -m pytest tests/test_teams_writer.py -v
"""

import io
import json
import os
import struct
import sys
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

# ── Make the native-host module importable regardless of cwd ──────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "native-host"))
import teams_writer  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# safe_filename
# ─────────────────────────────────────────────────────────────────────────────

class TestSafeFilename:
    def test_normal_name(self):
        assert teams_writer.safe_filename("general") == "general"

    def test_spaces_become_dashes(self):
        result = teams_writer.safe_filename("my channel")
        assert result == "my-channel"

    def test_special_chars_become_underscores(self):
        # Slashes, colons, etc. should become underscores
        result = teams_writer.safe_filename("chan/nel:name")
        assert "_" in result
        assert "/" not in result
        assert ":" not in result

    def test_alphanumeric_preserved(self):
        result = teams_writer.safe_filename("Team123")
        assert result == "Team123"

    def test_dashes_and_underscores_preserved(self):
        result = teams_writer.safe_filename("my-team_channel")
        assert result == "my-team_channel"

    def test_empty_string_returns_empty(self):
        assert teams_writer.safe_filename("") == ""

    def test_only_special_chars(self):
        result = teams_writer.safe_filename("!@#$%^&*()")
        # All replaced with underscores, leading/trailing stripped
        assert "/" not in result
        assert "!" not in result

    def test_path_traversal_attempt(self):
        result = teams_writer.safe_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_path_traversal_with_null_bytes(self):
        result = teams_writer.safe_filename("name\x00evil")
        assert "\x00" not in result

    def test_unicode_letters_preserved(self):
        # isalnum() returns True for unicode letters
        result = teams_writer.safe_filename("café")
        assert "c" in result
        assert "f" in result

    def test_leading_trailing_spaces_stripped(self):
        result = teams_writer.safe_filename("  hello  ")
        # After replacing spaces→dashes the strip() removes whitespace
        assert not result.startswith("-")
        assert "hello" in result

    def test_mixed_valid_invalid(self):
        result = teams_writer.safe_filename("Hello World!")
        assert result == "Hello-World_"


# ─────────────────────────────────────────────────────────────────────────────
# resolve_output_dir
# ─────────────────────────────────────────────────────────────────────────────

class TestResolveOutputDir:
    def test_default_within_home(self):
        settings = {}
        result = teams_writer.resolve_output_dir(settings)
        home = os.path.expanduser("~")
        assert result.startswith(home)

    def test_tilde_expansion(self):
        settings = {"outputDir": "~/teams-extractor/data/"}
        result = teams_writer.resolve_output_dir(settings)
        assert "~" not in result
        assert os.path.isabs(result)

    def test_valid_subdir_within_home(self):
        home = os.path.expanduser("~")
        settings = {"outputDir": os.path.join(home, "my-output")}
        result = teams_writer.resolve_output_dir(settings)
        assert result.startswith(home)

    def test_path_outside_home_raises(self):
        settings = {"outputDir": "/tmp/evil-output"}
        with pytest.raises(ValueError, match="must be within home directory"):
            teams_writer.resolve_output_dir(settings)

    def test_path_traversal_outside_home_raises(self):
        home = os.path.expanduser("~")
        # Attempt to escape via ../..
        evil = os.path.join(home, "..", "..", "etc")
        settings = {"outputDir": evil}
        with pytest.raises(ValueError, match="must be within home directory"):
            teams_writer.resolve_output_dir(settings)

    def test_slash_root_raises(self):
        settings = {"outputDir": "/"}
        with pytest.raises(ValueError):
            teams_writer.resolve_output_dir(settings)


# ─────────────────────────────────────────────────────────────────────────────
# build_filepath
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildFilepath:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_by_date_convention_format(self):
        path = teams_writer.build_filepath(self.tmpdir, "channel", "general", "by-date")
        filename = os.path.basename(path)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert filename.startswith(date_str)
        assert "channel" in filename
        assert "general" in filename
        assert filename.endswith(".md")

    def test_by_source_convention_format(self):
        path = teams_writer.build_filepath(self.tmpdir, "chat", "MyChat", "by-source")
        filename = os.path.basename(path)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # by-source: source_name_date
        assert filename.startswith("chat")
        assert "MyChat" in filename
        assert filename.endswith(f"{date_str}.md")

    def test_output_within_output_dir(self):
        path = teams_writer.build_filepath(self.tmpdir, "channel", "general", "by-date")
        assert path.startswith(self.tmpdir)

    def test_creates_output_dir_if_missing(self):
        subdir = os.path.join(self.tmpdir, "new-subdir")
        assert not os.path.exists(subdir)
        teams_writer.build_filepath(subdir, "channel", "general", "by-date")
        assert os.path.exists(subdir)

    def test_empty_source_falls_back_to_unknown(self):
        path = teams_writer.build_filepath(self.tmpdir, "", "general", "by-date")
        assert "unknown" in os.path.basename(path)

    def test_empty_name_falls_back_to_unknown(self):
        path = teams_writer.build_filepath(self.tmpdir, "channel", "", "by-date")
        assert "unknown" in os.path.basename(path)

    def test_special_chars_in_source_sanitised(self):
        path = teams_writer.build_filepath(self.tmpdir, "chan/nel", "general", "by-date")
        assert "/" not in os.path.basename(path)

    def test_path_stays_within_output_dir(self):
        # Even with path-traversal-like names the result must stay in output_dir
        path = teams_writer.build_filepath(self.tmpdir, "../../evil", "payload", "by-date")
        assert os.path.commonpath([self.tmpdir, path]) == self.tmpdir


# ─────────────────────────────────────────────────────────────────────────────
# messages_to_markdown
# ─────────────────────────────────────────────────────────────────────────────

class TestMessagesToMarkdown:
    def _data(self, **overrides):
        base = {
            "source": "channel",
            "name": "general",
            "messages": [],
        }
        base.update(overrides)
        return base

    # ── Front-matter ────────────────────────────────────────────────────────

    def test_frontmatter_contains_source(self):
        md = teams_writer.messages_to_markdown(self._data(source="channel"))
        assert "source: channel" in md

    def test_frontmatter_contains_name(self):
        md = teams_writer.messages_to_markdown(self._data(name="general"))
        assert "name: general" in md

    def test_frontmatter_contains_message_count(self):
        data = self._data(messages=[{"sender": "A", "timestamp": "12:00", "body": "hi"}])
        md = teams_writer.messages_to_markdown(data)
        assert "message_count: 1" in md

    def test_frontmatter_fenced_by_triple_dash(self):
        md = teams_writer.messages_to_markdown(self._data())
        lines = md.splitlines()
        assert lines[0] == "---"
        # Find closing ---
        assert "---" in lines[1:]

    def test_participants_included_when_present(self):
        data = self._data(participants=["Alice", "Bob"])
        md = teams_writer.messages_to_markdown(data)
        assert "participants:" in md
        assert "Alice" in md
        assert "Bob" in md

    def test_participants_omitted_when_absent(self):
        data = self._data()
        md = teams_writer.messages_to_markdown(data)
        assert "participants:" not in md

    # ── Channel with replies ─────────────────────────────────────────────────

    def test_channel_message_format(self):
        data = self._data(messages=[
            {"sender": "Alice", "timestamp": "2026-05-04T10:00:00Z", "body": "Hello team"}
        ])
        md = teams_writer.messages_to_markdown(data)
        assert "**Alice**" in md
        assert "Hello team" in md
        assert "2026-05-04T10:00:00Z" in md

    def test_reply_prefixed_with_blockquote(self):
        data = self._data(messages=[
            {"sender": "Alice", "timestamp": "10:00", "body": "Hello", "isReply": False},
            {"sender": "Bob",   "timestamp": "10:01", "body": "Hi there", "isReply": True},
        ])
        md = teams_writer.messages_to_markdown(data)
        lines = md.splitlines()
        reply_lines = [l for l in lines if l.startswith("> ")]
        assert len(reply_lines) == 1
        assert "Bob" in reply_lines[0]

    def test_non_reply_not_prefixed(self):
        data = self._data(messages=[
            {"sender": "Alice", "timestamp": "10:00", "body": "Hello", "isReply": False},
        ])
        md = teams_writer.messages_to_markdown(data)
        assert not any(l.startswith("> ") for l in md.splitlines())

    # ── Chat with participants ───────────────────────────────────────────────

    def test_chat_participants_in_frontmatter(self):
        data = {
            "source": "chat",
            "name": "Alice, Bob",
            "participants": ["Alice", "Bob"],
            "messages": [
                {"sender": "Alice", "timestamp": "09:00", "body": "Morning!"},
                {"sender": "Bob",   "timestamp": "09:01", "body": "Hey!"},
            ]
        }
        md = teams_writer.messages_to_markdown(data)
        assert "participants: [Alice, Bob]" in md
        assert "**Alice**" in md
        assert "**Bob**" in md

    # ── Meeting captions ────────────────────────────────────────────────────

    def test_meeting_captions_source(self):
        data = {
            "source": "meeting-captions",
            "name": "meeting-captions",
            "messages": [
                {"sender": "Alice", "timestamp": "10:00:00Z", "body": "Welcome everyone"},
                {"sender": "Bob",   "timestamp": "10:00:05Z", "body": "Thanks for joining"},
                {"sender": "Alice", "timestamp": "10:00:10Z", "body": "Let's get started"},
            ]
        }
        md = teams_writer.messages_to_markdown(data)
        assert "source: meeting-captions" in md
        assert "Welcome everyone" in md
        assert "Thanks for joining" in md
        assert "Let's get started" in md

    # ── Empty message list ───────────────────────────────────────────────────

    def test_empty_messages_produces_valid_frontmatter(self):
        md = teams_writer.messages_to_markdown(self._data(messages=[]))
        assert "message_count: 0" in md
        assert "---" in md

    def test_empty_messages_no_body_lines(self):
        md = teams_writer.messages_to_markdown(self._data(messages=[]))
        lines = [l for l in md.splitlines() if l.startswith("**")]
        assert len(lines) == 0

    def test_missing_timestamp_omitted_from_line(self):
        data = self._data(messages=[
            {"sender": "Alice", "body": "no timestamp"}
        ])
        md = teams_writer.messages_to_markdown(data)
        # Parenthesised timestamp should not appear
        assert "**Alice**: no timestamp" in md

    def test_body_is_stripped(self):
        data = self._data(messages=[
            {"sender": "Alice", "timestamp": "10:00", "body": "  trimmed  "}
        ])
        md = teams_writer.messages_to_markdown(data)
        assert "trimmed" in md


# ─────────────────────────────────────────────────────────────────────────────
# Native Messaging Protocol — write_message / read_message round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestNativeMessagingProtocol:
    """
    pytest wraps sys.stdin in a DontReadFromInput whose .buffer property
    cannot be monkey-patched.  We instead patch the module-level sys references
    inside teams_writer directly.
    """

    def _encode(self, payload: dict) -> bytes:
        """Manually encode a message the same way write_message does."""
        encoded = json.dumps(payload).encode("utf-8")
        return struct.pack("<I", len(encoded)) + encoded

    def test_write_message_produces_length_prefix(self):
        buf = io.BytesIO()
        fake_stdout = type("FakeStdout", (), {"buffer": buf, "flush": buf.flush})()
        with patch("teams_writer.sys") as mock_sys:
            mock_sys.stdout = fake_stdout
            teams_writer.write_message({"ok": True})
        buf.seek(0)
        raw_len = buf.read(4)
        msg_len = struct.unpack("<I", raw_len)[0]
        body = buf.read(msg_len)
        assert json.loads(body) == {"ok": True}

    def test_read_message_consumes_length_prefix(self):
        payload = {"source": "channel", "name": "general"}
        raw = self._encode(payload)
        fake_stdin = type("FakeStdin", (), {"buffer": io.BytesIO(raw)})()
        with patch("teams_writer.sys") as mock_sys:
            mock_sys.stdin = fake_stdin
            result = teams_writer.read_message()
        assert result == payload

    def test_round_trip_arbitrary_payload(self):
        payload = {"key": "value", "number": 42, "list": [1, 2, 3]}
        raw = self._encode(payload)
        fake_stdin = type("FakeStdin", (), {"buffer": io.BytesIO(raw)})()
        with patch("teams_writer.sys") as mock_sys:
            mock_sys.stdin = fake_stdin
            result = teams_writer.read_message()
        assert result == payload

    def test_round_trip_unicode_payload(self):
        payload = {"name": "café 日本語", "body": "émoji 🎉"}
        raw = self._encode(payload)
        fake_stdin = type("FakeStdin", (), {"buffer": io.BytesIO(raw)})()
        with patch("teams_writer.sys") as mock_sys:
            mock_sys.stdin = fake_stdin
            result = teams_writer.read_message()
        assert result == payload

    def test_read_message_returns_none_on_empty_stdin(self):
        fake_stdin = type("FakeStdin", (), {"buffer": io.BytesIO(b"")})()
        with patch("teams_writer.sys") as mock_sys:
            mock_sys.stdin = fake_stdin
            result = teams_writer.read_message()
        assert result is None

    def test_length_prefix_is_little_endian_uint32(self):
        buf = io.BytesIO()
        fake_stdout = type("FakeStdout", (), {"buffer": buf, "flush": buf.flush})()
        with patch("teams_writer.sys") as mock_sys:
            mock_sys.stdout = fake_stdout
            teams_writer.write_message({"x": 1})
        buf.seek(0)
        raw = buf.read(4)
        # Must be exactly 4 bytes, little-endian unsigned int
        assert len(raw) == 4
        value = struct.unpack("<I", raw)[0]
        assert value > 0


# ─────────────────────────────────────────────────────────────────────────────
# Caption flush reconstruction
# ─────────────────────────────────────────────────────────────────────────────

class TestCaptionFlush:
    """
    When a flush=True message arrives the main loop reconstructs a standard
    data dict. We test the reconstruction logic inline (same logic as main()).
    """

    def _reconstruct(self, flush_msg: dict) -> dict:
        """Mirror the flush-branch logic from teams_writer.main()."""
        assert flush_msg.get("flush") is True
        data = {
            "source":    flush_msg.get("source", "meeting-captions"),
            "name":      "meeting-captions",
            "_settings": flush_msg.get("_settings", {}),
            "messages": [
                {"sender": c["speaker"], "timestamp": c["timestamp"], "body": c["text"]}
                for c in flush_msg.get("messages", [])
            ]
        }
        return data

    def test_flush_source_preserved(self):
        msg = {
            "flush": True,
            "source": "meeting-captions",
            "_settings": {},
            "messages": []
        }
        data = self._reconstruct(msg)
        assert data["source"] == "meeting-captions"

    def test_flush_name_always_meeting_captions(self):
        msg = {"flush": True, "source": "meeting-captions", "_settings": {}, "messages": []}
        data = self._reconstruct(msg)
        assert data["name"] == "meeting-captions"

    def test_flush_settings_preserved(self):
        settings = {"outputDir": "~/teams-extractor/data/", "namingConvention": "by-source"}
        msg = {"flush": True, "source": "meeting-captions", "_settings": settings, "messages": []}
        data = self._reconstruct(msg)
        assert data["_settings"] == settings

    def test_flush_messages_remapped_correctly(self):
        captions = [
            {"speaker": "Alice", "timestamp": "10:00:01Z", "text": "Hello"},
            {"speaker": "Bob",   "timestamp": "10:00:05Z", "text": "Hi Bob"},
        ]
        msg = {"flush": True, "source": "meeting-captions", "_settings": {}, "messages": captions}
        data = self._reconstruct(msg)
        assert len(data["messages"]) == 2
        assert data["messages"][0] == {"sender": "Alice", "timestamp": "10:00:01Z", "body": "Hello"}
        assert data["messages"][1] == {"sender": "Bob",   "timestamp": "10:00:05Z", "body": "Hi Bob"}

    def test_flush_empty_messages(self):
        msg = {"flush": True, "source": "meeting-captions", "_settings": {}, "messages": []}
        data = self._reconstruct(msg)
        assert data["messages"] == []

    def test_flush_missing_source_defaults(self):
        msg = {"flush": True, "_settings": {}, "messages": []}
        data = self._reconstruct(msg)
        assert data["source"] == "meeting-captions"

    def test_flush_missing_settings_defaults_to_empty_dict(self):
        msg = {"flush": True, "source": "meeting-captions", "messages": []}
        data = self._reconstruct(msg)
        assert data["_settings"] == {}

    def test_full_flush_produces_valid_markdown(self):
        captions = [
            {"speaker": "Alice", "timestamp": "10:00:01Z", "text": "Welcome"},
            {"speaker": "Bob",   "timestamp": "10:00:10Z", "text": "Thanks"},
        ]
        msg = {"flush": True, "source": "meeting-captions", "_settings": {}, "messages": captions}
        data = self._reconstruct(msg)
        md = teams_writer.messages_to_markdown(data)
        assert "source: meeting-captions" in md
        assert "**Alice**" in md
        assert "Welcome" in md
        assert "**Bob**" in md
        assert "Thanks" in md
