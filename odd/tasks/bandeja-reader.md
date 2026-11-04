# Local tray reader

## Explore
The runtime contains the versioned tray but exposes no reader; existing paths
return 404. The data is local and may contain operational information.

## Implement
A read-only loopback, same-origin endpoint reads the two fixed JSONL files on
explicit request. Missing, malformed, symlinked or oversized input is NO_DATA.
The app renders text on a button click; no CORS, writes, or network forwarding.

## Check
Run directed tests and the repository yardsticks. Live deployment and browser
installation remain NO_DATA until the reviewed head reaches the runtime.
