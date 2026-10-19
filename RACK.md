# RACK.md · the rack of the PreceptorOS ecosystem

> Status: SIGNED by the architect. Merged 2026-10-13 (PR #6, 05:47 UTC),
> the rack's public card.

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

## Propuesta de frescura para observaciones · 2026-10-19

`TTL_DAYS = 7` (entero exacto; 604800 segundos). En cada lectura, una observación cuyo sello guardado sea `LIVE` pasa automáticamente a `STALE` cuando su edad alcanza 604800 segundos. La función pura vive en `rack_freshness.py`; invocación: `python3 rack_freshness.py --observed-at <ISO-8601-UTC>`. La transición es de lectura y no reescribe el recibo firmado. `NO_DATA`, `STATIC`, `SIMULATED` y `ERROR` conservan su estado y causa.

Recibo de esta sesión: `NO_DATA` para los endpoints locales de inferencia y PWA, causa: la política de sockets del sandbox bloqueó las conexiones loopback. Rutas sysfs y comandos medidos están en el PR del LAB; este entorno no certifica el estado live de la máquina física fuera del sandbox.

## Re-medición · 2026-10-19T12:04:41Z

- `http://127.0.0.1:11434/api/tags`: `LIVE`, HTTP 200, 45 entradas; se excluyeron los nombres.
- `http://127.0.0.1:11434/api/version`: `LIVE`, HTTP 200.
- `http://127.0.0.1:8740/`: `LIVE`, HTTP 200.
- El contador de tokens sigue `NO_DATA`, causa: `/metrics` devuelve HTTP 404. La energía neta por token sigue `NO_DATA`: la lectura RAPL devuelve `PermissionError` y no hay contador de tokens correlacionado.
- Comando exacto para los tres endpoints: `python3 -c 'import datetime as dt,json,urllib.request; print("observed_at="+dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")); p="/api/tags"; r=urllib.request.urlopen("http://127.0.0.1:11434"+p,timeout=3); print(p+" HTTP "+str(r.status)+" models="+str(len(json.load(r).get("models",[])))); r=urllib.request.urlopen("http://127.0.0.1:11434/api/version",timeout=3); print("/api/version HTTP "+str(r.status)); r=urllib.request.urlopen("http://127.0.0.1:8740/",timeout=3); print("PWA / HTTP "+str(r.status))'`.
