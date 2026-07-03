from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.graph.checkpointer import init_checkpointer
from app.graph.builder import get_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 SQLite checkpointer 并预构建图"""
    await init_checkpointer()
    get_graph()
    yield


app = FastAPI(title="Smart Travel Planning API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import router as plan_router
from app.api.chat_routes import router as chat_router

app.include_router(plan_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
