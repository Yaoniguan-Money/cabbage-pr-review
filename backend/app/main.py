from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import client_meta, diagram_meta, examples, health, input_page_meta, llm_mode, review_depth, rules_meta, tasks

app = FastAPI(title="AI PR Review 助手", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(client_meta.router)
app.include_router(diagram_meta.router)
app.include_router(input_page_meta.router)
app.include_router(review_depth.router)
app.include_router(llm_mode.router)
app.include_router(rules_meta.router)
app.include_router(examples.router)
app.include_router(tasks.router)
