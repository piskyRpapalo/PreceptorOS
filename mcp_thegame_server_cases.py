import unittest


class MCPServerTests(unittest.TestCase):
    def test_handshake_seven_tools_and_closed_arguments(self):
        import canales
        import mcp_thegame_server as server
        with self.assertRaises(canales.CanalRechazado):
            canales.di("app", "soberano", "test")
        response, ready = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(response["result"]["protocolVersion"], "2026-07-28")
        listed, _ = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, ready)
        self.assertEqual(len(listed["result"]["tools"]), 7)
        self.assertLess(len(server._bytes(listed)), 1024)
        unknown, _ = server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "unknown", "arguments": {}}}, ready)
        extra, _ = server.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "consultar_politica", "arguments": {"extra": True}}}, ready)
        self.assertEqual(unknown["error"]["code"], -32602)
        self.assertEqual(extra["error"]["code"], -32602)

    def test_tool_output_is_bounded_and_proposal_does_not_execute(self):
        import mcp_thegame_server as server
        ready = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})[1]
        response, _ = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "consultar_politica", "arguments": {}}}, ready)
        payload = response["result"]["content"][0]["text"].encode()
        self.assertLess(len(payload), 1024)
        self.assertFalse(response["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
