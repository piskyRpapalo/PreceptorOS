# App surface census · 2026-10-22

Base: `921a254`; 2026-10-22; Python 3.14.4 on Linux 7.0.0-38-generic x86_64. Scope: three existing surfaces measured in two fresh Python processes. The digest is SHA-256 over 4-byte big-endian length-prefixed canonical output bytes in the listed order. No source behavior changed.

| Surface | Rows | Audio state | Bytes (max row) | SHA-256 |
|---|---|---|---:|---|
| State (`NO_DATA`, `LIVE`, `STALE`) | 3 | `NO_HABLA`: structured state has no audio field | 1,506 (528) | `852aacb8dcab4b1b7203c8cee646a6e14a2cb2c413dbab1b57a5bcc7eedc817d` |
| Receipt (rejected, `NO_DATA`, accepted) | 3 | `NO_HABLA`: machine-readable outcomes only | 179 (64) | `2f8a3b03cff947642ca8d761c5613e93117961f2c60ec3112d9c2d997d028221` |
| Error text (three intents, `NO_DATA`) | 3 | `NO_HABLA`: sound is `INACTIVO`; text and cause are present | 849 (283) | `b254fdf83274e308d9b3ebfbc5d28c2104c843d69be5519f6238699f82486882` |

Physical speech playback: `NO_DATA`, cause: no audio device or loopback was exercised. The NO_DATA error projection retained its caller cause in all three intents. A cause-removal sabotage failed twice; the directed tests (`test_estado_app`, `test_nodo_export`, `test_orquestador_respuesta`) passed 19/19 twice. Measurement output matched byte-for-byte across the two processes.

Source SHA-256: `estado_app.py` `098ad85c113d250c66c28ee60e5a912286e30bb43d0bdef38d87395ac087ea1b`; `nodo_export.py` `5a30d3f1d884287eefd6bc1faab786fb337888aff3e6c5191294fbed85471d62`; `audio_feedback.py` `6c953a42ace279b350894889b836f1d76a26e22033482f1d03fa39305d4b4df6`.
