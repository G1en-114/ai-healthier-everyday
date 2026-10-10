"""FastAPI application entry — AI Healthier Every Day.

Serves both the model-service API (``/api/*``) and the browser self-care web
app (static files from ``webapp/`` mounted at ``/``). Registers the global
``MissingSecretError`` handler: missing third-party credentials map to HTTP
503 with only the key name exposed, never the value.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.model_service import router as model_service_router
from app.core.logging import configure_logging
from app.core.secrets import MissingSecretError

# 应用启动时安装全局日志配置与敏感数据脱敏（任务 2.2，需求 11.4）。
configure_logging()

app = FastAPI(
    title="AI Healthier Every Day — Self-Care Companion",
    description=(
        "Intelligent support for long-term self-care: in-browser pose AI, "
        "deterministic safety guardrails and a tool-calling self-care agent. "
        "Tencent Cloud AI CAN DO IT Hackathon Singapore 2026, Healthcare Track."
    ),
    version="0.3.0",
)

app.include_router(model_service_router)


@app.exception_handler(MissingSecretError)
async def missing_secret_handler(
    request: Request, exc: MissingSecretError
) -> JSONResponse:
    """将凭证缺失映射为 503，响应仅含错误标识与缺失键名，不回显密钥值。"""
    return JSONResponse(
        status_code=503,
        content={"detail": "service_unavailable", "missing": exc.secret_name},
    )


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查接口，用于探活。"""
    return {"status": "ok"}


# 浏览器 Web App：纯静态 SPA（无构建步骤），与 API 同源部署——
# 「Project Web Link」评委打开一个地址即可体验完整产品。
# 注意：不能把 StaticFiles 挂在 "/"（catch-all 会吞掉之后注册的路由），
# 改为显式 "/" 返回 index.html + 按子目录挂载静态资源。
from fastapi.responses import FileResponse

_webapp_dir = Path(__file__).resolve().parent.parent.parent / "webapp"
if _webapp_dir.is_dir():

    @app.get("/", include_in_schema=False)
    def webapp_index() -> FileResponse:
        return FileResponse(_webapp_dir / "index.html")

    for _sub in ("css", "js", "assets"):
        _dir = _webapp_dir / _sub
        if _dir.is_dir():
            app.mount(f"/{_sub}", StaticFiles(directory=str(_dir)), name=f"webapp-{_sub}")
