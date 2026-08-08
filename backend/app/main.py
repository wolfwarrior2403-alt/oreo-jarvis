from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.logging_config import configure_logging, get_logger
from app.routers import actions, auth, context, health, search, train, voice

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    logger.info("oreo_backend_started")
    yield
    logger.info("oreo_backend_stopped")


app = FastAPI(
    title="Oreo Backend",
    description="Personal AI assistant backend — gateway, STT, context engine, reasoning agent, TTS.",
    version="0.1.0",
    lifespan=lifespan,
)

# Local-first default (section 6): CORS is wide open here for LAN/dev
# convenience. Lock this down to your actual mobile app origin(s) — or put
# the API behind a reverse proxy that does — before exposing it publicly
# (Deployment Option B).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(voice.router)
app.include_router(context.router)
app.include_router(actions.router)
app.include_router(search.router)
app.include_router(train.router)
