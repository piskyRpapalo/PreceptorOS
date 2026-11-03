# Native reading of visible text · plan before code

Authority: buzon#30 FIRMA 6592198560 and native-reading decree 6592131133.
Baseline: APP c32e88f9 plus the separately reviewable Hexelion surface 08ee361.
This dependent branch isolates the voice piece against that UI branch; it is
stacked for review, never merged into main by the agent. No web changes or
terminal installation. #151 and pinned terminal language stay untouched.

## Explore

Existing browser HUD reads only local voices; /api/voz reports missing Piper.
The host does have espeak-ng. Its existence is not proof of audio output.
Existing creation voice is a separate Piper profile and is not relabeled.
The real local APP reply measured in this session has actor orquestador,
channel orquesta, n=880, 50 UTF-8 bytes, SHA-256
89923f44d3c73ffb0f41bf408ddc3b17b740020a129952aa3348065080067633.
It is a local pipe-model answer, not a tower/aula answer or a fixture.

## Implement

Read exactly visible attributed text, only on a user gesture. Browser-local
voice is the first explicit selection; no local voice means NO_DATA, never
an implicit cloud/default voice. Offer a separately labeled host espeak-ng
option; selecting it is explicit, not an automatic fallback. A short fixed
same-origin APP endpoint returns bounded PCM WAV plus text/audio digests;
no new service, arbitrary command/path/language, microphone or cloud request.
No private key, aula credential, model invocation or authority in this route.

Host synthesis requires loopback client and matching Origin/Host. Strict JSON,
closed fields, <1,024-byte text chunks, fixed executable lookup, stdin text,
timeout, bounded concurrency and temp cleanup. Honor SIN_HARDWARE. WAV is
returned only after measured layout/size checks. Unknown/offline engine =
NO_DATA. No shell. No remote CORS permission is introduced.

Browser text is split without loss into bounded UTF-8 chunks; each voice
receipt/frame stays below 1,024 bytes. Speech end / audio ended reports only
software completion, never a physical listener. STOP cancels native queues,
pending requests and browser audio; stale callbacks cannot restart reading.
Pagehide invokes STOP. Async load must not start speech after STOP.

## Check

Synthetic tests: no local browser voice, remote-only voice, chunk integrity,
late callback after STOP, invalid body, hostile Origin, missing engine,
timeout, invalid WAV, hardware switch. Real synthesis/browser playback is
measured separately using the real reply and its digest. Headless playback
is not speaker audibility or physical phone proof. Tower/aula authentication
and identity/ACL are separate NO_DATA until measured with admitted access.
Return: remove this voice route/assets; UI remains text-complete. J1 applies;
other J-* mapping is NO_DATA. Desk owns FIRMA+FIRMO and seal letters.
