from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from app.database import init_db
from app.routes import agent, audit, policy, secrets
from app.auth import auth_router
from app.routes import connect

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Vanguard — Secure Execution Gateway",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(audit.router)
app.include_router(policy.router)
app.include_router(secrets.router)
app.include_router(connect.router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {
        "service": "Vanguard Secure Execution Gateway",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "vanguard-gateway"}
