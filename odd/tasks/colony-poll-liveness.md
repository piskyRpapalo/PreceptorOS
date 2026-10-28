# Colony poll liveness

The app needs a poll boundary that does not confuse a configured node with a live one. This slice proposes an injectable poll adapter: each requested node is polled once; only an explicit successful observation for that same identity is LIVE, all failures and malformed observations are STALE with cause, and only LIVE observations become visible rows. The adapter supplies the measurement; the contract does not assert that a particular transport is trustworthy, authenticated, deployed or fresh beyond that single poll. No address or network source is invented.

Before visual evidence: [app #120](https://github.com/piskyRpapalo/PreceptorOS/pull/120). After screenshot, live endpoint, identity authentication, timeout policy, integration and weakest-device motion are NO_DATA: this slice has no served page or real poll source. Polling is not a wall-clock render input; no placeholder or error panel is produced by this contract.
