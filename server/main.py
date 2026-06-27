"""
FastAPI 服务端入口

提供：
- GET  /health         健康检查
- POST /api/generate   主接口：UserRequest → FinalPost

启动：
  uvicorn server.main:app --reload --port 8000

访问 Swagger UI：http://localhost:8000/docs

负责人：B · 后端工程师
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.orchestrator import run
from core.schemas import FinalPost, UserRequest

app = FastAPI(
    title="Interior Design Agent",
    description="AI 家装设计 Agent · 5 Agent 编排系统",
    version="0.0.1",
)

# 开发期允许所有跨域；上线前收紧
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/generate", response_model=FinalPost)
async def generate(request: UserRequest) -> FinalPost:
    return await run(request)
