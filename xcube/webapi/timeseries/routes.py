# Copyright (c) 2018-2025 by xcube team and contributors
# Permissions are hereby granted under the terms of the MIT License:
# https://opensource.org/licenses/MIT.

from typing import Any, Optional, Sequence

import pandas as pd

from xcube.server.api import ApiError, ApiHandler

from ..datasets import PATH_PARAM_DATASET_ID, PATH_PARAM_VAR_NAME
from .api import api
from .context import TimeSeriesContext
from .controllers import get_time_series

RESPONSE_FORMATS = {"raw", "contract"}


def _validate_response_format(response_format: Optional[str]) -> str:
    value = (response_format or "raw").strip().lower()
    if value not in RESPONSE_FORMATS:
        raise ApiError.BadRequest(
            "Query parameter 'responseFormat' must be one of: raw, contract."
        )
    return value


def _timeseries_has_data(result: Any) -> bool:
    if isinstance(result, list):
        if not result:
            return False
        first = result[0]
        if isinstance(first, list):
            return any(len(series) > 0 for series in result if isinstance(series, list))
        return len(result) > 0
    return bool(result)


def _timeseries_summary(result: Any) -> dict[str, Any]:
    if not isinstance(result, list):
        return {"rows": 0, "collections": 0, "isCollection": False}
    if not result:
        return {"rows": 0, "collections": 0, "isCollection": False}

    first = result[0]
    if isinstance(first, list):
        rows = sum(len(series) for series in result if isinstance(series, list))
        return {"rows": rows, "collections": len(result), "isCollection": True}

    return {"rows": len(result), "collections": 1, "isCollection": False}


def _serialize_timestamp(value: Any) -> Optional[str]:
    if value is None:
        return None
    return pd.Timestamp(value).isoformat()


def _extract_geojson_type(geo_json_object: Any) -> Optional[str]:
    if isinstance(geo_json_object, dict):
        geo_type = geo_json_object.get("type")
        if isinstance(geo_type, str):
            return geo_type
    return None


def _make_contract_response(
    dataset_id: str,
    var_name: str,
    result: Any,
    agg_methods: Optional[Sequence[str]],
    start_date: Any,
    end_date: Any,
    tolerance: Optional[float],
    max_valids: Optional[int],
    geo_json_object: Any,
) -> dict[str, Any]:
    return {
        "contract": "xcube-calculations/v1",
        "operation": "timeseries",
        "datasetId": dataset_id,
        "varName": var_name,
        "hasData": _timeseries_has_data(result),
        "summary": _timeseries_summary(result),
        "query": {
            "aggMethods": agg_methods,
            "startDate": _serialize_timestamp(start_date),
            "endDate": _serialize_timestamp(end_date),
            "tolerance": tolerance,
            "maxValids": max_valids,
        },
        "input": {
            "geoJsonType": _extract_geojson_type(geo_json_object),
        },
        "result": result,
    }


# noinspection PyPep8Naming
@api.route("/timeseries/{datasetId}/{varName}")
class TimeseriesHandler(ApiHandler[TimeSeriesContext]):
    @api.operation(
        operation_id="getTimeSeries",
        summary="Get the time-series for a variable and given GeoJSON object.",
        parameters=[
            PATH_PARAM_DATASET_ID,
            PATH_PARAM_VAR_NAME,
            {
                "name": "aggMethods",
                "in": "query",
                "description": "Comma-separated list of"
                " aggregation methods."
                " Valid methods are"
                ' "mean", "median", "std",'
                ' "min", "max", "count"',
                "schema": {
                    "type": "string",
                },
            },
            {
                "name": "startDate",
                "in": "query",
                "description": "Start timestamp",
                "schema": {"type": "string", "format": "datetime"},
            },
            {
                "name": "endDate",
                "in": "query",
                "description": "End timestamp",
                "schema": {"type": "string", "format": "datetime"},
            },
            {
                "name": "tolerance",
                "in": "query",
                "description": "Time tolerance in seconds that"
                " expands the given time range",
                "schema": {
                    "type": "string",
                    "default": 1.0,
                },
            },
            {
                "name": "maxValids",
                "in": "query",
                "description": "Maximum number of valid"
                " time-series values"
                " to be returned.",
                "schema": {
                    "type": "integer",
                },
            },
            {
                "name": "responseFormat",
                "in": "query",
                "description": "Response format. Use 'raw' for existing"
                " payload ({result: [...]}) or 'contract' for a"
                " unified calculations contract response.",
                "schema": {
                    "type": "string",
                    "default": "raw",
                    "enum": ["raw", "contract"],
                },
            },
        ],
    )
    async def post(self, datasetId: str, varName: str):
        geo_json_object = self.request.json
        agg_methods = self.request.get_query_arg("aggMethods", type=str, default=None)
        agg_methods = agg_methods.split(",") if agg_methods else None
        start_date = self.request.get_query_arg(
            "startDate", type=pd.Timestamp, default=None
        )
        end_date = self.request.get_query_arg(
            "endDate", type=pd.Timestamp, default=None
        )
        tolerance = self.request.get_query_arg("tolerance", type=float, default=1.0)
        max_valids = self.request.get_query_arg("maxValids", type=int, default=None)
        response_format = _validate_response_format(
            self.request.get_query_arg("responseFormat", type=str, default="raw")
        )
        result = await self.ctx.run_in_executor(
            None,
            get_time_series,
            self.ctx,
            datasetId,
            varName,
            geo_json_object,
            agg_methods,
            start_date,
            end_date,
            tolerance,
            max_valids,
        )
        self.response.set_header("Content-Type", "application/json")
        if response_format == "contract":
            await self.response.finish(
                _make_contract_response(
                    datasetId,
                    varName,
                    result,
                    agg_methods,
                    start_date,
                    end_date,
                    tolerance,
                    max_valids,
                    geo_json_object,
                )
            )
        else:
            await self.response.finish(dict(result=result))
