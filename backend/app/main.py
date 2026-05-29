from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import examples, health, tasks

app = FastAPI(title="AI PR Review 助手", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(examples.router)
app.include_router(tasks.router)
