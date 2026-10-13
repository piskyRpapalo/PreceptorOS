# RACK.md · the rack of the PreceptorOS ecosystem

> Status: PROPOSAL, unsigned. It becomes the rack's public card when the
> architect signs it.

This is the public card of the rack: the small fleet of machines that runs
this ecosystem. It exists so a visitor — human or AI — knows what the hardware
is, what runs on it, and what has actually been measured on it. Every figure
below was measured; anything not measured is `NO_DATA` with its cause. No
addresses, no ports, no keys: those are not public facts.

## The fleet

- **soberano** (Beelink mini PC) — the main node. AMD Ryzen 7 255 with a
  Radeon 780M iGPU; the GPU was measured running Vulkan (RADV PHOENIX) with
  32,193 MiB free in the benchmark session. It runs Colibri 2.0.0 (llama.cpp,
  Vulkan backend) serving a dense Qwen3.8-27B — verified. The embedding
  benchmark of embeddinggemma-2 ran here: 6,459 tok/s at prompt-pair 512. The
  raw JSON of that benchmark is public in the LAB, with its sha256
  (`26e61fb7…`).
- **la-fragua** (Orange Pi) — the ecosystem's storage vault (a 4 TB NVMe
  drive).
- **la-torre** (Jetson) — part of the fleet. Current state: **NO_DATA** — not
  re-measured this week.
- **el-vigia** — daily watch: it reports once a day that all is well.

## What runs, and what does not

The main node runs local inference (llama.cpp through Vulkan) and the
measurement sessions whose results are published in the LAB. What runs on the
other machines, beyond the roles named above, is `NO_DATA` here: this card
publishes only what was measured, with its source.

Every measured figure of this ecosystem lives in the LAB
([lab](https://github.com/piskyRpapalo/lab)) — benchmarks and counters, each
with its machine, its date and the command that produced it. The companion
application lives in [PreceptorOS](https://github.com/piskyRpapalo/PreceptorOS);
the public gateway and the game live in
[preceptoros-web](https://github.com/piskyRpapalo/preceptoros-web), served at
[preceptoros.org](https://preceptoros.org). The ecosystem's state card is
`STATE.md` in both public repositories.

Measured or NO_DATA.
