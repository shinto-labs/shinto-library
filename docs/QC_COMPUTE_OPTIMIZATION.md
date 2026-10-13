# QC compute optimization — overview for DevOps

How we cut Limburg-scale QC from **tens of seconds (~60s reported)** to **~few seconds**, and what to ship.

Branch name (all three repos): **`qc_compute_optimization`**

---

## Agent brief (read this first)

**Goal:** Ship three coordinated changes so a new backend image + FE deploy make QC startup fast. Do **not** re-implement from scratch; use the branches/files below.

**Done when:**
1. `shinto-library` helpers are on GitHub `main` or a released version, and the backend image depends on that version.
2. Bifrost image serves `GET /juno/qc_report_lean` with AST cache (from branch `qc_compute_optimization`).
3. juno-react build from `qc_compute_optimization` calls lean on load (network tab proves it).
4. Target tenant has valid pin + correct pack; smoke checklist passes.
5. No local Docker bind-mount hacks in production compose.

**Concrete key files**

| Repo | Paths |
|------|--------|
| shinto-library | `shinto/qc/expression_eval.py`, `tests/test_qc_expression_helpers_limburg.py`, `docs/QC_COMPUTE_OPTIMIZATION.md` |
| bifrost | `backend/module/qc_report_lean.py`, `backend/config/router_config.json`, `docs/QC.md`, `docs/QC_COMPUTE_OPTIMIZATION.md` |
| juno-react | `src/services/DataService.js` (`getQcReportLean`), `src/store/storeUtils.js` (lean + parallel load), `src/components/gemeente-qc/*` (meta/Overzicht), `docs/QC_COMPUTE_OPTIMIZATION.md` |

**Do not:**
- Hijack `/juno/qc_report` instead of adding lean
- Drop `project.data.qc` / map popup support (lean uses `findings` → FE apply)
- Forget pin/pack on the tenant
- Treat AST cache as already in upstream shinto (it lives in bifrost lean module only)

**Optional follow-ups (out of scope for this ship):** result caching table; upstream AST cache into shinto; create GitHub PRs if not opened yet.

---

## Repos & status

| Repo | Branch | Remote | Doc in repo |
|------|--------|--------|-------------|
| [shinto-labs/shinto-library](https://github.com/shinto-labs/shinto-library) | `qc_compute_optimization` | **Pushed** — [open PR](https://github.com/shinto-labs/shinto-library/pull/new/qc_compute_optimization) | `docs/QC_COMPUTE_OPTIMIZATION.md` |
| [shinto-labs/bifrost](https://github.com/shinto-labs/bifrost) | `qc_compute_optimization` | **Pushed** — [open PR](https://github.com/shinto-labs/bifrost/pull/new/qc_compute_optimization) | `docs/QC_COMPUTE_OPTIMIZATION.md` |
| [shinto-labs/juno-react](https://github.com/shinto-labs/juno-react) | `qc_compute_optimization` | **Pushed** — [open PR](https://github.com/shinto-labs/juno-react/pull/new/qc_compute_optimization) | `docs/QC_COMPUTE_OPTIMIZATION.md` |

---

## What to ship (order)

### 1. shinto-library — Limburg dialect helpers
Add helpers used by `qc_pack_limburg.json`:

- `all_equal`, `sum_num`, `sum_num_if`, `has_polygon_geometry`

Without these, Limburg rules fail closed (`Unknown helper`) and runs are wrong/noisy.

**Action:** Merge/release this branch, then bump the backend image’s shinto dependency.

### 2. bifrost — lean QC endpoint + AST cache
New endpoints:

- `GET /juno/qc_report_lean`
- `POST /juno/qc_report_lean`

Same pin resolve + `run_qc` as full QC, but:

- Runs the **pinned pack as-is** (no hard-coded rule skips). Keep heavy rules out of the pack (Limburg already omits base64/HTML detection + matrix-style D15/D25)
- **AST compile cache** (in the lean module, not in stock `/juno/qc_report`)
- Slim JSON: `findings` / `overzicht` / `dashboard` — **no** fat `projectQcById` blob

Full `/juno/qc_report` stays for admin/complete runs.

**Action:** Rebuild backend image from this bifrost branch (with new shinto).

### 3. juno-react — call lean on load, in parallel
- App load uses **`getQcReportLean()`**, not full QC
- Starts **`project_list` and lean QC in parallel** (wall-clock ≈ max, not sum)
- Maps lean `findings` → per-project `data.qc` (map popup / tabs still work)
- Small Overzicht/meta hardenings (prioriteit normalize, basisset+provincie, list rules with 0 hits)

**Action:** Deploy this FE build with the new backend.

### 4. Tenant data (not code)
- Load correct pack (e.g. Limburg `qc_pack_limburg`)
- **schema_package pin** must point at a pack revision that exists (`schema_package_validate` → `ok: true`)

---

## What we did *not* put in these branches

Local-only experiments — do **not** ship:

- Bind-mount overwriting `/module/juno/qc_runner.py`
- Bind-mount of a local `expression_eval.py`
- Empty stub that disables full QC

---

## Perf picture (indicative, Limburg ~4k projects)

| Path | Order of magnitude |
|------|--------------------|
| Old: full QC on every app load | tens of seconds |
| Full QC compute only (fixed pin) | ~7s locally |
| Lean + AST + helpers | **~2.5–5s** |

Further win (future): persist per-project QC keyed by project timestamp + pack version; recompute only dirty / time-sensitive rules.

---

## Smoke checklist

1. Backend image includes new shinto helpers (no `Unknown helper` in logs on Limburg pack).
2. `GET /juno/qc_report_lean` → 200, `checkOverview` present, `mode` lean.
3. FE network tab on load: **`/juno/qc_report_lean`** (not only full `/juno/qc_report`).
4. `/datakwaliteit` Overzicht populated; project map “Data kwaliteit” popup still shows issues.
5. Pin validate OK for the tenant.

---

## Mental model

```text
shinto helpers  ─┐
                 ├──► backend image ──► lean API
bifrost lean/AST─┘         │
                           ▼
              juno-react calls lean (+ parallel project_list)
                           │
                           ▼
              UI: findings → project.data.qc + Overzicht tabs
```

Fresh QC every startup (Zustand in-memory only; no localStorage QC cache yet).
