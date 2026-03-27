import logging

from .logging_config import get_logger
from .health import health_check, readiness_check, get_server_info, get_metrics_endpoint
from .tools import mcp as tools_mcp

logger = get_logger(__name__)


class SQLMCPServer:

    def __init__(self, transport: str = "stdio", bind: str = "127.0.0.1:8080") -> None:
        self.transport = transport
        self.bind = bind

    async def run(self) -> None:
        if self.transport == "stdio":
            await tools_mcp.run_stdio_async()
        elif self.transport == "http":
            await self._run_http()
        else:
            raise ValueError(f"Unknown transport: {self.transport}")

    async def _run_http(self) -> None:
        from starlette.responses import Response, JSONResponse
        from starlette.requests import Request

        host, port_str = self.bind.rsplit(":", 1)
        tools_mcp.settings.host = host
        tools_mcp.settings.port = int(port_str)

        @tools_mcp.custom_route("/health", methods=["GET"])
        async def health_endpoint(request: Request) -> Response:
            return JSONResponse(await health_check())

        @tools_mcp.custom_route("/ready", methods=["GET"])
        async def ready_endpoint(request: Request) -> Response:
            result = await readiness_check()
            return JSONResponse(result, status_code=200 if result["status"] == "ready" else 503)

        @tools_mcp.custom_route("/info", methods=["GET"])
        async def info_endpoint(request: Request) -> Response:
            return JSONResponse(await get_server_info())

        @tools_mcp.custom_route("/metrics", methods=["GET"])
        async def metrics_endpoint(request: Request) -> Response:
            return Response(await get_metrics_endpoint(), media_type="text/plain")

        logger.info("Starting HTTP transport on %s", self.bind)
        await tools_mcp.run_streamable_http_async()
