# LF-5 · MCP envelope and channel byte contract

Scope: the existing app JSON-RPC stdio entry point, `mcp_thegame_server.py`.
Base: `0a43bf1063f9397e5aa8aa9a77f1d5ee00129e0f`; measured 2026-10-24.
The seven tools, their arguments and their authority boundaries stay intact.
This is a local transport profile, not a claim that every MCP peer uses this
byte ceiling. Client interoperability is measured separately in LF-6.

## Wire rule

Each complete request and response line is **less than 1,024 UTF-8 bytes**,
including its LF delimiter, JSON-RPC envelope, identifier and escaped content.
Thus 1,023 bytes are admitted; 1,024 are rejected. The existing tool-result
ceiling remains an additional inner check. It cannot establish the size of
the outer line: JSON escaping and the MCP content wrapper add bytes.

The input reader requests at most 1,024 bytes at a time. An oversized line is
drained to LF or EOF, rejected once, and never dispatched. The next complete
line is handled normally. Invalid UTF-8 or JSON and a final line lacking LF
produce explicit parse errors. No partial line is executed. Normal valid
notifications still produce no response. A malformed/oversized frame cannot
be classified as a valid notification and receives an error with a null ID.

Replies are measured after serialization. An oversized reply is replaced
whole by a `NO_DATA` JSON-RPC error; content is never trimmed. Its request ID
is retained if the error fits, otherwise the error has a null ID. Such an
error cannot safely be correlated by ID: the client must stop that operation
and diagnose it. It must not blindly retry a tool that might have written.
The transport cannot roll back effects already performed by a valid tool.

| Condition | JSON-RPC code | Result |
|---|---:|---|
| Input line reaches 1,024 bytes | -32600 | Rejected before dispatch |
| Invalid UTF-8/JSON or missing final LF | -32700 | Rejected before dispatch |
| Serialized response reaches 1,024 bytes | -32000 | Whole response rejected |
| Response cannot be serialized | -32000 | Explicit serialization cause |

No network listener, background client or new tool is introduced. A Bubble
frame below 1,024 bytes does not necessarily fit inside this envelope: LF-6
must measure the entire request, or propose a separate artifact transport.
There is no implicit chunking, truncation or bypass switch.

## Reception evidence

Run `python3 -m unittest test_mcp_transport mcp_thegame_server_cases`.
The new suite also enters `bin/pruebas` in the same commit.

Before the fix, the nine new tests reported five failures and two subtest
errors: a 200,000-byte padded request dispatched, a line without LF
dispatched, UTF-8/ID cases exceeded the ceiling, and a result wrapper emitted
1,050 bytes. The same tests plus the existing two server cases passed 11/11
after the fix. These tests spawn real short-lived stdio processes; they do
not touch the local rack state or require sockets.

Rack/service residency, an attached external model client and browser/Bubble
wiring remain `NO_DATA`: this suite does not measure them. Physical audio and
the E8 journey remain separate evidence. The Mesa receives this proposal;
the Sovereign retains FIRMO.

Full local runner: `TMPDIR=/tmp ./bin/pruebas` counted 1,127 tests across 84
suites. Only `test_puente` failed (four loopback socket permission errors in
the sandbox); this is not a green full gate. The six directed sabotage
groups detected 4/4, 6/6, 15/15, 6/6, 6/6 and 8/8 violations. The private
identifier tree scan was skipped because its CI-supplied scan values were
unavailable. The rack and CI must complete the full gate before FIRMO.
