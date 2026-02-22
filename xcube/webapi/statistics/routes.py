# Copyright (c) 2018-2025 by xcube team and contributors
# Permissions are hereby granted under the terms of the MIT License:
# https://opensource.org/licenses/MIT.

from typing import Any, Optional

from xcube.server.api import ApiError, ApiHandler

from ...util.undefined import UNDEFINED
from ..datasets.routes import PATH_PARAM_DATASET_ID, PATH_PARAM_VAR_NAME
from .api import api
from .context import StatisticsContext
from .controllers import compute_statistics

RESPONSE_FORMATS = {"raw", "contract"}


def _validate_response_format(response_format: Optional[str]) -> str:
    value = (response_format or "raw").strip().lower()
    if value not in RESPONSE_FORMATS:
        raise ApiError.BadRequest(
            "Query parameter 'responseFormat' must be one of: raw, contract."
        )
    return value


def _extract_geojson_type(geo_json_object: Any) -> Optional[str]:
    if isinstance(geo_json_object, dict):
        geo_type = geo_json_object.get("type")
        if isinstance(geo_type, str):
            return geo_type
    return None


def _statistics_has_data(result: Any) -> bool:
    if isinstance(result, dict):
        if "count" in result:
            try:
                return int(result["count"]) > 0
            except (TypeError, ValueError):
                return False
        if "value" in result:
            return result.get("value") is not None
        return bool(result)
    return bool(result)


def _statistics_summary(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        count = 0
        if "count" in result:
            try:
                count = int(result["count"])
            except (TypeError, ValueError):
                count = 0
        elif "value" in result and result.get("value") is not None:
            count = 1
        return {"count": count, "keys": sorted(result.keys())}
    return {"count": 0, "keys": []}


def _make_contract_response(
    dataset_id: str,
    var_name: str,
    result: Any,
    time: Optional[str],
    input_info: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract": "xcube-calculations/v1",
        "operation": "statistics",
        "datasetId": dataset_id,
        "varName": var_name,
        "hasData": _statistics_has_data(result),
        "summary": _statistics_summary(result),
        "query": {
            "time": time,
        },
        "input": input_info,
        "result": result,
    }


QUERY_PARAM_X = {
    "name": "lon",
    "in": "query",
    "description": "Longitude in decimal degree",
    "required": True,
    "schema": {"type": "number", "minimum": -180, "maximum": 180},
}

QUERY_PARAM_Y = {
    "name": "lat",
    "in": "query",
    "description": "Latitude in decimal degree",
    "required": True,
    "schema": {"type": "number", "minimum": -90, "maximum": 90},
}

QUERY_PARAM_TIME = {
    "name": "time",
    "in": "query",
    "description": 'Timestamp using format "YYYY-MM-DD hh:mm:ss"',
    "required": False,
    "schema": {"type": "string", "format": "datetime"},
}

QUERY_PARAM_RESPONSE_FORMAT = {
    "name": "responseFormat",
    "in": "query",
    "description": "Response format. Use 'raw' for existing"
    " payload ({result: {...}}) or 'contract' for a unified"
    " calculations contract response.",
    "required": False,
    "schema": {"type": "string", "default": "raw", "enum": ["raw", "contract"]},
}


# noinspection PyPep8Naming
@api.route("/statistics/{datasetId}/{varName}")
class StatisticsHandler(ApiHandler[StatisticsContext]):
    @api.operation(
        operation_id="getValue",
        summary=(
            "Get the value of a dataset variable for given time stamp and location."
        ),
        parameters=[
            PATH_PARAM_DATASET_ID,
            PATH_PARAM_VAR_NAME,
            QUERY_PARAM_X,
            QUERY_PARAM_Y,
            QUERY_PARAM_TIME,
            QUERY_PARAM_RESPONSE_FORMAT,
        ],
    )
    async def get(self, datasetId: str, varName: str):
        lon = self.request.get_query_arg("lon", type=float, default=UNDEFINED)
        lat = self.request.get_query_arg("lat", type=float, default=UNDEFINED)
        time = self.request.get_query_arg("time", type=str, default=None)
        response_format = _validate_response_format(
            self.request.get_query_arg("responseFormat", type=str, default="raw")
        )
        trace_perf = self.request.get_query_arg(
            "debug", default=self.ctx.datasets_ctx.trace_perf
        )
        result = await self.ctx.run_in_executor(
            None,
            compute_statistics,
            self.ctx,
            datasetId,
            varName,
            (lon, lat),
            time,
            trace_perf,
        )
        if response_format == "contract":
            await self.response.finish(
                _make_contract_response(
                    datasetId,
                    varName,
                    result,
                    time,
                    {"mode": "point", "lon": lon, "lat": lat},
                )
            )
        else:
            await self.response.finish({"result": result})

    @api.operation(
        operation_id="getStatistics",
        summary=(
            "Get statistics of a dataset variable for given time stamp and geometry."
        ),
        description=(
            "The geometry is passed in the request body in"
            " form of a valid GeoJSON geometry object."
            " The operation returns the count, minimum, maximum, mean,"
            " and standard deviation of a data variable. If a 2-D geometry"
            " is passed, a histogram is returned as well."
        ),
        parameters=[
            PATH_PARAM_DATASET_ID,
            PATH_PARAM_VAR_NAME,
            QUERY_PARAM_TIME,
            QUERY_PARAM_RESPONSE_FORMAT,
        ],
    )
    async def post(self, datasetId: str, varName: str):
        time = self.request.get_query_arg("time", type=str, default=None)
        response_format = _validate_response_format(
            self.request.get_query_arg("responseFormat", type=str, default="raw")
        )
        trace_perf = self.request.get_query_arg(
            "debug", default=self.ctx.datasets_ctx.trace_perf
        )
        geometry = self.request.json
        result = await self.ctx.run_in_executor(
            None,
            compute_statistics,
            self.ctx,
            datasetId,
            varName,
            geometry,
            time,
            trace_perf,
        )
        if response_format == "contract":
            await self.response.finish(
                _make_contract_response(
                    datasetId,
                    varName,
                    result,
                    time,
                    {"mode": "geojson", "geoJsonType": _extract_geojson_type(geometry)},
                )
            )
        else:
            await self.response.finish({"result": result})
