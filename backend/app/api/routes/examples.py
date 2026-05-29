from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["examples"])

EXAMPLES = [
    {
        "id": "fastapi-sample",
        "title": "FastAPI 示例 PR",
        "pr_url": "https://github.com/tiangolo/fastapi/pull/1",
        "description": "经典 FastAPI 仓库早期 PR，用于演示结构扫描",
    },
    {
        "id": "vite-sample",
        "title": "Vite 示例 PR",
        "pr_url": "https://github.com/vitejs/vite/pull/10000",
        "description": "前端工具链 PR，用于演示多文件 diff",
    },
]


@router.get("/examples")
async def list_examples():
    return {"examples": EXAMPLES}
