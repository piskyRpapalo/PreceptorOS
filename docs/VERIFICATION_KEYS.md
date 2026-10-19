# SSHSIG verification-key ceremony · PROPUESTA REQUIERE_FIRMA

`VERIFICATION_KEYS.txt` is an allowlist of public SSH keys for the `preceptoros` namespace. Private signing keys stay on the Sovereign's device and never enter this repository.

1. The Sovereign creates the payload and signs it locally with `ssh-keygen -Y sign -f <private-key-path> -n preceptoros <payload-path>`.
2. The Sovereign checks the detached signature locally before adding the matching public key line to `VERIFICATION_KEYS.txt`.
3. A reviewer checks the signer and namespace with `ssh-keygen -Y verify -f VERIFICATION_KEYS.txt -I <principal> -n preceptoros -s <signature-path> < <payload-path>`.
4. Only the Sovereign authorizes additions, rotations, or removals. A commit or a valid proposal is not itself a sign-off.

The current branch carries no active signer entry: `NO_DATA`, cause: no public verification key was supplied for this proposal. No key material or private principal is invented.
