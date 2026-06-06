import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

app = FastAPI(
    title="PDF 文档结构化抽取 API",
    description="一个功能完整的PDF文档结构化抽取服务，支持文本抽取、布局还原、表格识别、目录提取和元信息获取",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "PDF 文档结构化抽取 API 服务",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "port": 8011
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8011,
        reload=True
    )
