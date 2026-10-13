# QC compute optimization — shinto-library

Branch: `qc_compute_optimization`  
Base: `main` (v1.5.6+)

## What changed

Added four QC dialect helpers used by the Limburg rule pack (`qc_pack_limburg.json`):

| Helper | Purpose |
|--------|---------|
| `all_equal(rows, key, value)` | True when every row has `key == value` (empty list → False) |
| `sum_num(rows, key)` | Sum of numeric `key` across rows |
| `sum_num_if(rows, sum_key, filter_key, filter_value)` | Conditional sum |
| `has_polygon_geometry(geo)` | True for Polygon/MultiPolygon with non-empty coordinates |

Registered in `shinto/qc/expression_eval.py` `HELPERS`, with unit coverage in `tests/test_qc_expression_helpers_limburg.py`.

## Why

Without these helpers, Limburg pack rules that call them log `Unknown helper` and fail closed (incorrect QC + noisy/slow runs). The published `main` / `v1.5.6` package did not include them; they lived only on a local unpushed branch.

## DevOps / release notes

1. Merge or release this branch as a new `shinto` version (e.g. bump after 1.5.6).
2. Rebuild the Bifrost / shinto-backend image so it depends on that version.
3. No API break: additive helpers only.
4. Pair with Bifrost branch `qc_compute_optimization` (lean QC endpoint + AST cache) and the juno-react frontend branch of the same name.

## Out of scope here

- Lean HTTP endpoint / AST cache → **bifrost**
- SPA calling lean on load → **juno-react**
- Tenant pin / loading `qc_pack_limburg` → data / ops
