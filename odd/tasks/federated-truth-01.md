# Federated evidence: truthful states and attribution

APP backend, Codex CLI. Base 896158fa47f84f9ef921d8a5f037b49bcca984bc.
Mesa handoff #22: P0 before durable recovery. Existing LAB source and APP
federated reader remain the producers; no new router, UI or service.

Before: a catalog reporting NO_DATA could appear VERIFIED; a manifest renamed
to another node could be attributed there. Baseline directed suite 54 tests x2
passed despite both negative controls demonstrating these failures.

After: validate manifest/part identities, bounded counts, complete model
digests, duplicate parts and finite JSON; reject node/catalog contradictions.
Fresh metadata is OBSERVED, with integrity VERIFIED only in its explicit scope;
inference/admission remain NO_DATA without independent witnesses. STALE retains
its age, source reference and expiry. Resolve the LAB git ref to a commit before
reading all parts so one projection cannot combine mutable branch revisions.
Talk uses the same state and says metadata observed, inference untested.

No live deployment, inference, device access, automatic model selection or
human grant. A self-hash proves integrity, not authenticity. Unknown completion
and process-restart recovery remain P2; Session currently keeps runs in memory.
Rollback: revert this PR; no migration or database write. Claude consumes the
state changes through existing response shapes; no UI files changed here.
