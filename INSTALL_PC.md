# Download and start PreceptorOS

[Open the published v1.3 release](https://github.com/piskyRpapalo/PreceptorOS/releases/tag/v1.3).

**Measured on 2026-10-26:** this release has installation scripts and model data.
It has no attached desktop executable or Android APK. The earlier version of
this guide described a 14 MB executable; that is not an available v1.3 download.
A build recipe does not establish that an executable has been published.

The checklist below is a five-minute reading and setup guide, not a measured
installation time. Download time, missing prerequisites, and a fresh installation
on your computer remain `NO_DATA` until exercised there.

## Choose the download

| Platform | Published asset | What is measured |
|---|---|---|
| Linux | [install.sh](https://github.com/piskyRpapalo/PreceptorOS/releases/download/v1.3/install.sh) | 4,529 bytes; downloaded and SHA-256 checked on 2026-10-26. The release records a historical Linux installation test dated 2026-08-31. A new clean installation was not run for this guide. |
| macOS | The same `install.sh` | The asset exists; macOS execution is `NO_DATA: not exercised`. |
| Windows | [install.ps1](https://github.com/piskyRpapalo/PreceptorOS/releases/download/v1.3/install.ps1) | 2,638 bytes; downloaded and SHA-256 checked on 2026-10-26. Windows execution is `NO_DATA: not exercised`. |
| Android | [Published Termux guide](https://github.com/piskyRpapalo/PreceptorOS/releases/download/v1.3/INSTALACION_ANDROID.md), or [the current English guide](INSTALL_ANDROID.md) | A guide is attached. No APK is attached. A current physical installation was not exercised for this guide. |

There are 13 attached assets: two installation scripts, one Android guide,
five model files, and five companion model checksum files. The small model
files are optional data; they are not an application executable or a requirement
to replace an AI you already run locally.

## First-run checklist on Linux

1. Check the prerequisites in a terminal:

   ```sh
   python3 --version
   git --version
   ```

   The current source requires Python 3.10 or newer. If a prerequisite is
   missing, install it through your operating system's normal package tools.
   The release installer checks prerequisites; it does not obtain administrator
   privileges or install system packages for you.

2. Download `install.sh` using the link above. In the download directory, verify
   the exact published asset:

   ```sh
   printf '%s  install.sh\n' '2bd8666979a67ea1ec8b01a01aac240acfc2cef6165b93e558d0b836d3df6e74' | sha256sum -c -
   ```

   Continue only if the result is `OK`. Read the script before running it:

   ```sh
   less install.sh
   bash install.sh
   ```

   The script clones the repository's current default branch into your user
   directory. It does **not** pin the application source to the v1.3 tag. Record
   the cloned commit when reporting an installation result. This mutable source
   dependency is an outstanding release-packaging issue.

3. Use the destination reported by the installer. With its default destination:

   ```sh
   cd "$HOME/preceptoros"
   git rev-parse HEAD
   bin/preceptoros-servicio arranca
   bin/preceptoros-servicio estado
   ```

4. Open [the local application](http://localhost:8740) in your browser. Keep the
   service running while using it. To stop it from that repository:

   ```sh
   bin/preceptoros-servicio para
   ```

5. If the service reports a busy port, use `estado` to identify the existing
   instance before stopping or replacing anything. A web page answering does
   not establish which application version is serving it.

Opening the local interface does not establish model compatibility. The release
installer checks whether Ollama is present but does not install or validate a
model engine for you. Reuse of an existing local AI is `NO_DATA` until its engine
and model are configured and exercised with the application. No model download is requested by this checklist.

## Windows and macOS limits

For Windows, download and inspect `install.ps1`. Its measured SHA-256 is:

```text
b10d7b8ade7ea0f301fd325336ae97dba6fd954786956703a3c1c6a80641f19b
```

Compare the result of `Get-FileHash .\install.ps1 -Algorithm SHA256` with that
value. Follow the script's prerequisite checks and your operating system's
execution policy. This guide does not claim that the Windows installation has
passed a clean-machine test.

The macOS branch of the shell installer is also unverified. Use the source
instructions below if you want to inspect the application first, and report the
platform and exact failure rather than treating an untested path as working.

## Install from the current source

```sh
git clone --depth 1 https://github.com/piskyRpapalo/PreceptorOS
cd PreceptorOS
python3 preceptoros.py
bin/preceptoros-servicio arranca
```

This is a source installation, not a packaged desktop application. Record
`git rev-parse HEAD` with any result. The local service state is reported by
`bin/preceptoros-servicio estado`.

If you want an applications-menu entry, run `bin/instalar-pc` from the installed
repository. `bin/instalar-pc --desinstalar` removes that entry and preserves the
local memory. Neither command was executed as part of this documentation audit.

## Creating a node on the public website

**The inspected application does not yet complete public node creation.**
Its Settings flow prepares an unsigned charter and asks for local consent.
The signer is explicitly a stub. The local preview receiver returns
`persisted: false` and a synthetic catalog count; that is not a registered public
node. See [the implemented receiver](node_registration.py),
[the browser adapter](interface/node_registration.js), and
[the registration sequence](docs/node-registration-sequence.md).

A pending, unsigned, or untrusted result must stay labeled that way. Opening the
app or accepting a preview does not replace the signing ceremony, a pinned trust
anchor, or acceptance by the public receiver and catalog.

## Measured gaps and proposed next pieces

| Piece | Evidence on 2026-10-26 | Reviewable next action |
|---|---|---|
| Release packaging | v1.3 was published on 2026-08-31. No desktop executable or APK is attached; its installers clone unpinned current source. | Publish only reproducible builds that passed a fresh-install check, with platform, source commit, size, and checksum manifest. Until then expose the scripts as source installers. |
| Web download door | No app release/installer URL was found in the inspected public HTML/JavaScript source; the fetched apex HTML had no explicit app download link. Dynamic browser rendering was not exercised. | A separate web-lane piece should add a visible Download app link to this guide and the release, with platform and node-registration limits visible before download. |
| Five-minute onboarding | The existing guide promised an unattached executable. This file now links the assets that exist and supplies a bounded first-run checklist. | Measure a clean Linux installation; test each other platform before changing its `NO_DATA` status. Setup duration and existing-model compatibility must be measured separately. |
| Public registration | `node_registration.py` is a nonpersistent test receiver with an explicit stub signer. Public route HEAD and OPTIONS both returned 404; POST behavior was not measured and cannot be inferred from those methods. | Complete the receiver, ceremony, anchor, and catalog pieces under their own review boundaries, then exercise a real consent-to-catalog sequence without presenting a stub as a created node. |

The release asset inventory came from the GitHub release API. Both installer
files were downloaded without executing them, and their bytes matched the API's
SHA-256 digests. Source observations use app main `08e6374` and web main
`c03228c4cf5f`; release metadata, static source inspection, and HTTP observations
are separate evidence. The public page was fetched; browser rendering, service
worker delivery, a physical fresh install, and completed public registration
remain `NO_DATA` with the causes above.
