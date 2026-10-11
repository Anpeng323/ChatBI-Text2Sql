"""FastAPI 入口：CORS、lifespan、挂载路由。"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import chat, export, schema, sessions
from .core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("chatbi")


def create_app() -> FastAPI:
    app = FastAPI(title="ChatBI 通用数据分析平台", version="0.1.0")

    origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(schema.router)
    app.include_router(export.router)

    # 生产环境可直接托管前端构建产物（frontend/dist）
    # backend/app/main.py → 上溯两级到项目根目录，再进 frontend/dist
    _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    _dist = os.path.join(_root, "frontend", "dist")
    if os.path.isdir(_dist):
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=_dist, html=True), name="static")
    else:

        @app.get("/")
        async def root() -> dict:
            return {"service": "ChatBI", "status": "ok", "docs": "/docs"}

    return app


app = create_app()
