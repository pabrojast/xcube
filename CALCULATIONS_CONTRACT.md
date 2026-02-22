# xcube Calculations Contract (`xcube-calculations/v1`)

This document defines a stable response contract for calculation endpoints used by
Terria integrations (time series and statistics).

The contract is enabled by adding:

- `responseFormat=contract`

to existing xcube endpoints.

## Endpoints

- `POST /timeseries/{datasetId}/{varName}`
- `GET /statistics/{datasetId}/{varName}`
- `POST /statistics/{datasetId}/{varName}`

## Backward Compatibility

- `responseFormat=raw` (default):
  Keeps current payload shape:
  - timeseries: `{ "result": [...] }`
  - statistics: `{ "result": { ... } }`
- `responseFormat=contract`:
  Returns unified envelope described below.

## Contract Envelope

```json
{
  "contract": "xcube-calculations/v1",
  "operation": "timeseries | statistics",
  "datasetId": "string",
  "varName": "string",
  "hasData": true,
  "summary": {
    "...": "operation-specific summary"
  },
  "query": {
    "...": "normalized query parameters"
  },
  "input": {
    "...": "input descriptor"
  },
  "result": {}
}
```

## Timeseries Contract

`operation = "timeseries"`

`summary`:

- `rows`: total number of rows returned
- `collections`: number of series in collection mode
- `isCollection`: true if result is a collection of series

`query`:

- `aggMethods`
- `startDate`
- `endDate`
- `tolerance`
- `maxValids`

`input`:

- `geoJsonType`

`result`:

- Same payload returned previously in `result`.

## Statistics Contract

`operation = "statistics"`

`summary`:

- `count`: derived count (`result.count`, or 1 for non-null point `result.value`)
- `keys`: sorted keys available in `result`

`query`:

- `time`

`input`:

- For GET point queries:
  - `mode = "point"`
  - `lon`
  - `lat`
- For POST geometry queries:
  - `mode = "geojson"`
  - `geoJsonType`

`result`:

- Same payload returned previously in `result`.

## Examples

### Timeseries

```bash
curl -X POST \
  "https://data.dev-wins.com/xcube/timeseries/ukraine_lwq300_pyramid/tsm_mean?aggMethods=mean,min,max&maxValids=200&responseFormat=contract" \
  -H "Content-Type: application/json" \
  -d '{ "type": "Point", "coordinates": [30.5, 50.45] }'
```

### Statistics

```bash
curl -X POST \
  "https://data.dev-wins.com/xcube/statistics/ukraine_lwq300_pyramid/tsm_mean?time=2024-09-01T00:00:00Z&responseFormat=contract" \
  -H "Content-Type: application/json" \
  -d '{ "type": "Point", "coordinates": [30.5, 50.45] }'
```
