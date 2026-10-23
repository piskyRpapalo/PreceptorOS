import json
import sys
from types import SimpleNamespace
import unittest
import base64

import tools.mcp_stdio_receipt as receipt


class MCPReceiptTests(unittest.TestCase):
    def test_configured_server_handshake_ping_and_inventory(self):
        result = receipt.run_receipt()
        self.assertEqual(result["protocol_version"], "2026-07-28")
        self.assertEqual(result["tool_count"], 7)
        self.assertEqual(result["tool_calls"], 0)
        self.assertEqual(result["process_exit"], 0)
        self.assertLess(result["max_request_bytes"], 1024)
        self.assertLess(result["max_response_bytes"], 1024)
        self.assertEqual(result["bubble_frame_bytes"], 197)
        self.assertLess(result["bubble_frame_probe_request_bytes"], 1024)
        self.assertIn("NO_DATA", result["bubble_frame_capability"])

    def test_sub_1024_bubble_frame_can_exceed_full_json_rpc_envelope(self):
        frame = json.dumps({
            "v": "preceptoros.bubble/1", "id": "CREATION", "cv": [412, 515],
            "style": "clear", "atoms": [{"k": "keepsake", "i": [{
                "o": "ribbon", "f": "cyan", "s": "ink", "d": 0,
                "lw": 2.5, "pts": [[i, 258] for i in range(60)]}]}]},
            separators=(",", ":")).encode("utf-8")
        request = receipt._line({"jsonrpc": "2.0", "id": 1,
                                 "method": "tools/call", "params": {
                                     "name": "bubble_frame.validate",
                                     "arguments": {"frame": base64.b64encode(frame).decode("ascii")}}})
        self.assertLess(len(frame), 1024)
        self.assertGreaterEqual(len(request), 1024)

        class Writer:
            data = b""

            def write(self, value):
                self.data += value

            def flush(self):
                pass

        writer = Writer()
        message = json.loads(request)
        with self.assertRaisesRegex(receipt.ReceiptError, "request reaches"):
            receipt._exchange(SimpleNamespace(stdin=writer), message, 1)
        self.assertEqual(writer.data, b"")

    def test_unicode_envelope_is_counted_as_utf8_with_lf(self):
        line = receipt._line({"jsonrpc": "2.0", "id": 1,
                              "method": "tools/call", "params": {"texto": "á"}})
        self.assertEqual(line[-1:], b"\n")
        self.assertGreater(len(line), len(line.decode("utf-8")))

    def test_unlisted_server_configuration_is_rejected(self):
        original = receipt.CONFIG.read_text(encoding="utf-8")
        changed = json.loads(original)
        changed["server"] = "other.py"
        with self.assertRaisesRegex(receipt.ReceiptError, "closed declaration"):
            receipt._validate_config(changed)

    def test_response_over_limit_is_rejected(self):
        script = "import sys; sys.stdin.readline(); sys.stdout.write('x' * 1024); sys.stdout.flush()"
        with self.assertRaisesRegex(receipt.ReceiptError, "1024-byte line ceiling"):
            receipt.run_receipt([sys.executable, "-c", script], timeout=2)

    def test_mismatched_response_id_is_rejected(self):
        script = ("import sys,json; sys.stdin.readline(); "
                  "print(json.dumps({'jsonrpc':'2.0','id':99,'result':{}}))")
        with self.assertRaisesRegex(receipt.ReceiptError, "id mismatch"):
            receipt.run_receipt([sys.executable, "-c", script], timeout=2)


if __name__ == "__main__":
    unittest.main()
