# Synthetic signing fixtures

`generate.mjs` creates a key pair with Node's `crypto.generateKeyPairSync` for the creation-signature test fixtures. This is generated test material, not an application credential or a production key. The checked-in fixture set contains no literal PEM private-key header. Do not replace these fixtures with live credentials; keep key values out of notes, logs, and receipts.
