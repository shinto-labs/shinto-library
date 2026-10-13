# QC compute optimization — overview for DevOps

How we cut Limburg-scale QC from **tens of seconds (~60s reported)** to **~few seconds**, and what to ship.

Branch name (all three repos): **`qc_compute_optimization`**

---

## Agent brief (read this first)

**Goal:** Ship three coordinated changes so a new backend image + FE deploy make QC startup fast. Do **not** re-implement from scratch; use the branches/files below.

**Done when:**
1. Backend image depends on a **shinto** release that includes Limburg helpers **and** stock AST compile cache in `expression_eval` (helpers are in **v1.5.7+**; AST cache lands in the next bump after that).
2. Bifrost image serves `GET /juno/qc_report_lean` (slim payload). Prefer **no** monkey-patch of `evaluate` once the library AST cache is available — lean should call stock `run_qc` / `evaluate`.
3. juno-react build from `qc_compute_optimization` calls lean on load (network tab proves it).
4. Target tenant has valid pin + correct pack; smoke checklist passes.
5. No local Docker bind-mount hacks in production compose.

**Concrete key files**

| Repo | Paths |
|------|--------|
| shinto-library | `shinto/qc/expression_eval.py` (helpers + AST cache), `tests/test_qc_expression_helpers_limburg.py`, `integration_tests/qc_expression_helpers.py`, `integration_tests/qc_run_perf.py`, `docs/QC_COMPUTE_OPTIMIZATION.md` |
| bifrost | `backend/module/qc_report_lean.py`, `backend/config/router_config.json`, `docs/QC.md`, `docs/QC_COMPUTE_OPTIMIZATION.md` |
| juno-react | `src/services/DataService.js` (`getQcReportLean`), `src/store/storeUtils.js` (lean + parallel load), `src/components/gemeente-qc/*` (meta/Overzicht), `docs/QC_COMPUTE_OPTIMIZATION.md` |

**Do not:**
- Hijack `/juno/qc_report` instead of adding lean
- Drop `project.data.qc` / map popup support (lean uses `findings` → FE apply)
- Forget pin/pack on the tenant
- Keep bifrost monkey-patching private `_validate_ast` / `_eval` after shinto owns the AST cache

**Optional follow-ups (out of scope for this ship):** result caching table; `run_qc(..., include_project_qc_by_id=False)` for lean; remove bifrost `_install_ast_cache` once the library release with stock cache is pinned.

---

## Repos & status

| Repo | Branch | Status | Doc in repo |
|------|--------|--------|-------------|
| [shinto-labs/shinto-library](https://github.com/shinto-labs/shinto-library) | `qc_compute_optimization` / `development` | **Helpers in v1.5.7.** Stock AST cache + thicker tests/docs on the follow-up change (version bump left to release owner). | `docs/QC_COMPUTE_OPTIMIZATION.md` |
| [shinto-labs/bifrost](https://github.com/shinto-labs/bifrost) | `qc_compute_optimization` | Lean endpoint + (legacy) process AST monkey-patch until library cache is pinned | `docs/QC_COMPUTE_OPTIMIZATION.md` |
| [shinto-labs/juno-react](https://github.com/shinto-labs/juno-react) | `qc_compute_optimization` | Lean on load + parallel `project_list` | `docs/QC_COMPUTE_OPTIMIZATION.md` |

---

## What to ship (order)

### 1. shinto-library — Limburg helpers + stock AST cache

**Helpers** (since **v1.5.7**) used by `qc_pack_limburg.json`:

- `all_equal`, `sum_num`, `sum_num_if`, `has_polygon_geometry`

Without these, Limburg pack rules that call them log `Unknown helper` and fail closed.

**AST compile cache** (stock `evaluate` / `evaluate_bool` in `expression_eval.py`):

- Each unique expression string is `ast.parse` + safety-validated **once** per process
- Reused on every project/stage eval (`clear_expression_cache()` for tests)
- Full `/juno/qc_report` and lean both benefit — no bifrost private-API patch required after this release is pinned

**Action:** Release the library bump that includes the stock AST cache, then point the backend image at that version (helpers alone are already in 1.5.7).

### 2. bifrost — lean QC endpoint (+ drop monkey-patch after shinto bump)

New endpoints:

- `GET /juno/qc_report_lean`
- `POST /juno/qc_report_lean`

Same pin resolve + `run_qc` as full QC, with:

- **Pinned pack as-is** (no hard-coded rule skips). Keep heavy rules out of the pack (Limburg already omits base64/HTML detection + matrix-style D15/D25)
- Slim JSON: `findings` / `overzicht` / `dashboard` — **no** fat `projectQcById` blob
- AST: rely on **stock shinto cache** once available; until then lean may still install a temporary monkey-patch

Full `/juno/qc_report` stays for admin/complete runs.

**Action:** Rebuild backend image (new shinto + lean module).

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

Library integration smoke: `integration_tests/qc_run_perf.py` (large synthetic pack using the Limburg helpers; soft wall-clock budget).

Further win (future): persist per-project QC keyed by project timestamp + pack version; recompute only dirty / time-sensitive rules.

---

## Smoke checklist

1. Backend image includes shinto with Limburg helpers (no `Unknown helper` in logs on Limburg pack).
2. Prefer image with stock AST cache; bifrost should not need `evaluate` monkey-patch.
3. `GET /juno/qc_report_lean` → 200, `checkOverview` present, `mode` lean.
4. FE network tab on load: **`/juno/qc_report_lean`** (not only full `/juno/qc_report`).
5. `/datakwaliteit` Overzicht populated; project map “Data kwaliteit” popup still shows issues.
6. Pin validate OK for the tenant.

---

## Mental model

```text
shinto helpers + stock AST cache ──► backend image ──► lean API (slim JSON)
 bifrost lean shaping only ────────┘         │
                                             ▼
                                juno-react calls lean (+ parallel project_list)
                                             │
                                             ▼
                                UI: findings → project.data.qc + Overzicht tabs
```

Fresh QC every startup (Zustand in-memory only; no localStorage QC cache yet).
