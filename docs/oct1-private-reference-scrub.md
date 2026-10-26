# October app scrub: measured target table

**Scope:** T1 tracked-file grep on the app repository at `origin/main` `b0f0814`, 2026-10-25 UTC. Query: the five private-reference tokens named in the commission. Result: 29 matching lines across 20 tracked files. No values from those lines are copied here. The table records repository path, line, and planned handling before source edits.

| Repository | Path | Line | State |
|---|---|---:|---|
| PreceptorOS | `CIERRE_M3.md` | 263 | Private repository name in prose -> `<private-repo>`. |
| PreceptorOS | `El_Temple.md` | 8 | External path -> `<private-ref>/El_Temple.md`; `sha256=NO_DATA scope_not_signed`. |
| PreceptorOS | `L3_P1_INVENTARIO.md` | 28 | External file reference -> `<private-ref>/ojo.py`; preserve cited lines; hash `NO_DATA scope_not_signed`. |
| PreceptorOS | `L3_P1_INVENTARIO.md` | 29 | External file references -> `<private-ref>/servidor.py` and `<private-ref>/timers.py`; preserve cited lines; hashes `NO_DATA scope_not_signed`. |
| PreceptorOS | `L3_P1_INVENTARIO.md` | 30 | External file reference -> `<private-ref>/rack_instantanea.py`; preserve cited lines; hash `NO_DATA scope_not_signed`. |
| PreceptorOS | `L3_P1_INVENTARIO.md` | 31 | External file reference -> `<private-ref>/ollama-puente.py`; preserve cited lines; hash `NO_DATA scope_not_signed`. |
| PreceptorOS | `L3_P1_INVENTARIO.md` | 33 | External file reference -> `<private-ref>/sala.py`; preserve cited lines; hash `NO_DATA scope_not_signed`. |
| PreceptorOS | `MARCA.md` | 107 | External file reference -> `<private-ref>/README.md`; hash `NO_DATA scope_not_signed`. |
| PreceptorOS | `MCP_CLIENT_WIRING.md` | 40 | Private repository name in prose -> `<private-repo>`. |
| PreceptorOS | `SCRUB_INVENTARIO.md` | 99 | External file references -> `<private-ref>/consejo.py` and `<private-ref>/reconcilia_contratos.py`; preserve cited lines; hashes `NO_DATA scope_not_signed`. |
| PreceptorOS | `SCRUB_INVENTARIO.md` | 100 | External tool/file references -> `<private-ref>/instalar-ganchos` and `<private-ref>/renombrar-empaquetado.py`; preserve cited lines; hashes `NO_DATA scope_not_signed`. |
| PreceptorOS | `canales.py` | 100 | Remove implicit external path discovery; load the optional adapter only from its explicit environment setting. |
| PreceptorOS | `contexto_seguro.md` | 32 | External configuration path -> `<private-ref>/50-<private-repo>.conf`; hash `NO_DATA scope_not_signed`. Preserve other measured fields. |
| PreceptorOS | `docs/route-map-node-gateway.md` | 21 | External file reference -> `<private-ref>/nodos.py`; preserve cited lines; hash `NO_DATA scope_not_signed`. |
| PreceptorOS | `frontera.py` | 21 | Remove private environment name from prose; retain the generic user-local environment statement. |
| PreceptorOS | `herramientas/calibrar_caras.py` | 117 | Replace hard-coded external input path with an explicit environment setting; no private path default. |
| PreceptorOS | `herramientas/calibrar_caras.py` | 118 | Replace hard-coded external output path with an explicit environment setting; no private path default. |
| PreceptorOS | `herramientas/calibrar_caras.py` | 119 | Replace hard-coded external mark path with an explicit environment setting; no private path default. |
| PreceptorOS | `herramientas/medir_tokens.py` | 62 | Replace hard-coded external glossary path with an optional environment setting; absent setting yields no external read. |
| PreceptorOS | `metricas.py` | 53 | Generalize environment variable and replace endpoint literal with `<private-ip>`; require explicit configuration before a request. The IP value is not recorded. |
| PreceptorOS | `test_canales.py` | 179 | Replace private path component with a synthetic in-repo test path. The IP in this test input is functional; leave it unchanged and mark `IP functional, decision by Sovereign`. |
| PreceptorOS | `test_canales.py` | 201 | Replace external registry path with a nonempty local test fixture. T1 lookup of source is `NO_DATA`; fixture scope will be stated explicitly. |
| PreceptorOS | `test_captura.py` | 210 | Replace private path string with a synthetic test path. |
| PreceptorOS | `test_consola.py` | 268 | Replace private path component with a synthetic test path. |
| PreceptorOS | `test_importar.py` | 25 | Replace external checkout path with an in-repo source-status fixture; exact external source is `NO_DATA` from T1. |
| PreceptorOS | `test_medidas.py` | 21 | Replace external checkout path with an in-repo source-status fixture; exact external source is `NO_DATA` from T1. |
| PreceptorOS | `test_nodo_app.py` | 76 | Replace sibling-repository path with the nonempty local source-status fixture; exact external source is `NO_DATA` from T1. |
| PreceptorOS | `test_nodo_app.py` | 78 | Replace private repository name in skip text with the explicit local `NO_DATA` cause. |
| PreceptorOS | `test_normas.py` | 140 | Replace external checkout path with an in-repo source-status fixture; exact external source is `NO_DATA` from T1. |

## Hash scope and IP exception

External-file hashes are not measured because the signed device policies declare no infrastructure scope. Each such reference uses the exact cause `sha256=NO_DATA scope_not_signed`. No rack query is authorized or performed.

The functional IP fixture in `test_canales.py:179,180,184` exercises the app's redaction path. Those inputs are left unchanged pending the Sovereign's decision, as directed. The endpoint literal in `metricas.py:53` is not a test fixture and is replaced with a generic marker without recording its value.

## External test-source availability

T1 GitHub lookup for the external registry and web contract sources returned not found. Their consumers will use nonempty, in-repository fixtures that explicitly declare source provenance as `NO_DATA`; tests must retain that distinction and must not claim current cross-repository parity.
