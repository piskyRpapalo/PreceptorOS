"""LF-5: measure complete UTF-8 stdio lines, including the LF delimiter."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent


def wire(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"


PING = {"jsonrpc": "2.0", "id": 7, "method": "ping"}
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
CALL = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "leer_estado", "arguments": {}}}


class MCPTransportTests(unittest.TestCase):
    def process(self, data, setup=""):
        code = "import mcp_thegame_server as s\n" + setup + "\ns.main()\n"
        result = subprocess.run([sys.executable, "-c", code], input=data,
                                capture_output=True, cwd=ROOT, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        lines = result.stdout.splitlines(keepends=True)
        for line in lines:
            self.assertTrue(line.endswith(b"\n"))
            self.assertLess(len(line), 1024, "whole reply, not just result, must fit")
        return [json.loads(line) for line in lines]

    def test_initialize_list_ping_real_process(self):
        listed = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        replies = self.process(wire(INIT) + wire(listed) + wire(PING))
        self.assertEqual(len(replies[1]["result"]["tools"]), 7)
        self.assertEqual(replies[2]["result"], {})

    def test_input_boundary_counts_delimiter(self):
        raw = wire(PING)
        for size in (1023, 1024, 1025):
            with self.subTest(size=size):
                replies = self.process(raw[:-1] + b" " * (size-len(raw)) + b"\n" + raw)
                if size < 1024:
                    self.assertEqual(replies[0]["result"], {})
                else:
                    self.assertEqual(replies[0]["error"]["code"], -32600)
                self.assertEqual(replies[1]["id"], 7)

    def test_utf8_bytes_not_character_count(self):
        raw = wire(dict(PING, id="é" * 500))
        self.assertLess(len(raw.decode()), 1024)
        self.assertGreaterEqual(len(raw), 1024)
        reply = self.process(raw)[0]
        self.assertEqual(reply["error"]["code"], -32600)
        self.assertIsNone(reply["id"])

    def test_oversize_call_never_dispatches_and_recovers(self):
        raw = wire(CALL)
        # A complete oversized request must not dispatch even when valid JSON.
        setup = "s._call = lambda *args: (_ for _ in ()).throw(SystemExit(23))"
        replies = self.process(wire(INIT) + raw[:-1] + b" " * 200000 + b"\n" + wire(PING), setup)
        self.assertEqual(replies[1]["error"]["code"], -32600)
        self.assertEqual(replies[2]["result"], {})

    def test_invalid_utf8_and_json_recover(self):
        replies = self.process(b'\xff\n{bad}\n' + wire(PING))
        self.assertEqual([r["error"]["code"] for r in replies[:2]], [-32700, -32700])
        self.assertEqual(replies[2]["result"], {})

    def test_eof_without_delimiter_never_dispatches(self):
        setup = "s._call = lambda *args: (_ for _ in ()).throw(SystemExit(23))"
        reply = self.process(wire(INIT) + wire(CALL)[:-1], setup)[1]
        self.assertEqual(reply["error"]["code"], -32700)

    def test_wrapper_overflow_rejects_whole_result(self):
        setup = 's._call = lambda *args: {"content":[{"type":"text","text":"é"*480}],"isError":False}'
        replies = self.process(wire(INIT) + wire(CALL) + wire(PING), setup)
        self.assertEqual(replies[1]["id"], 2)
        self.assertEqual(replies[1]["error"]["code"], -32000)
        self.assertIn("NO_DATA", replies[1]["error"]["message"])
        self.assertEqual(replies[2]["result"], {})

    def test_large_id_cannot_overflow_error_envelope(self):
        request = {"jsonrpc": "2.0", "id": "x" * 950, "method": "tools/list"}
        self.assertLess(len(wire(request)), 1024)
        reply = self.process(wire(INIT) + wire(request))[1]
        self.assertIsNone(reply["id"])
        self.assertEqual(reply["error"]["code"], -32000)

    def test_notifications_stay_silent(self):
        notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        self.assertEqual(self.process(wire(notification)), [])


if __name__ == "__main__":
    unittest.main()
