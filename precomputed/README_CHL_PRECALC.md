# CHL Precomputed Areas

This folder stores precomputed CHL timeseries for reference inland-water areas.

## Area definitions

- File: `precomputed/chl_reference_areas.json`
- Current areas:
  - `kyiv_reservoir`
  - `kremenchuk_reservoir`
  - `svityaz_lake`
  - `yalpuh_lake`
- Core areas with validated rows:
  - File: `precomputed/chl_reference_areas_core.json`
  - `kyiv_reservoir`
  - `kremenchuk_reservoir`

## Generated results

- Output directory: `precomputed/chl_results`
- Results are now namespaced by product under:
  - `precomputed/chl_results/<product_key>/`
- Filename format:
  - raw: `<product_key>__<area_id>__<start>_<end>.json`
  - daily/monthly: `<product_key>__<area_id>__<start>_<end>__<time_grain>.json`
- HTTP path (recommended):
  - raw: `/precomputed/<product_key>/<product_key>__<area_id>__<start>_<end>.json`
  - monthly example: `/precomputed/<product_key>/<product_key>__<area_id>__<start>_<end>__monthly.json`
- Current generated files:
  - `ua_chl/manifest_2023-01-02_2026-02-12.json`
  - `ua_chl/manifest_2023-01-02_2026-02-12_monthly.json`
  - `ua_chl/ua_chl__kyiv_reservoir__2023-01-02_2026-02-12.json`
  - `ua_chl/ua_chl__kyiv_reservoir__2023-01-02_2026-02-12__monthly.json`
  - `ua_chl/ua_chl__kremenchuk_reservoir__2023-01-02_2026-02-12.json`
  - `ua_chl/ua_chl__kremenchuk_reservoir__2023-01-02_2026-02-12__monthly.json`
  - `ua_chl/ua_chl__svityaz_lake__2023-01-02_2026-02-12.json`
  - `ua_chl/ua_chl__svityaz_lake__2023-01-02_2026-02-12__monthly.json`
  - `ua_chl/ua_chl__yalpuh_lake__2023-01-02_2026-02-12.json`
  - `ua_chl/ua_chl__yalpuh_lake__2023-01-02_2026-02-12__monthly.json`
  - `ua_chl/ua_chl__kyiv_reservoir__2024-01-01_2024-02-01.json`
  - `ua_chl/ua_chl__kremenchuk_reservoir__2024-01-01_2024-02-01.json`

- Manifest format (namespaced):
  - raw: `precomputed/chl_results/<product_key>/manifest_<start>_<end>.json`
  - daily/monthly: `precomputed/chl_results/<product_key>/manifest_<start>_<end>_<time_grain>.json`
  - Includes item-level `hasData`, `rows`, `requestsFailed`

## Frontend fallback

Recommended client flow:

1. Try precomputed JSON first:
   - `/precomputed/<product_key>/<product_key>__<area_id>__<start>_<end>__monthly.json` (or `__daily`)
   - fallback to raw: `/precomputed/<product_key>/<product_key>__<area_id>__<start>_<end>.json`
2. If not found (HTTP 404), fallback to xcube:
   - `POST /timeseries/<dataset_id>/<variable>`

Using `<product_key>` in path and filename avoids collisions when two products
share the same `<area_id>`.

## Regenerate

From repository root:

```bash
python3 scripts/precompute_chl_reference_areas.py \
  --start-date auto \
  --end-date auto \
  --time-grain monthly \
  --days-per-request 7 \
  --max-valids 50 \
  --timeout-secs 180 \
  --output-dir precomputed/chl_results
```

`auto` resolves against xcube dataset metadata (`/datasets/<dataset_id>/coords/time`):
- start = first available sensing timestamp date
- end = last available sensing timestamp date + 1 day (inclusive coverage)

For long periods where some windows may fail intermittently:

```bash
python3 scripts/precompute_chl_reference_areas.py \
  --start-date auto \
  --end-date auto \
  --time-grain daily \
  --days-per-request 7 \
  --max-valids 60 \
  --timeout-secs 240 \
  --continue-on-error \
  --output-dir precomputed/chl_results
```
