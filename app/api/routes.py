from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response, Path as FastAPIPath
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from app.pdf_utils.extractor import extract_pdf

router = APIRouter(prefix="/api/v1", tags=["PDF Extraction"])

SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"


@router.get("/", summary="API健康检查")
async def root():
    return {
        "status": "ok",
        "service": "PDF Structured Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/v1/extract/text": "Extract plain text from PDF",
            "POST /api/v1/extract/layout": "Extract text with layout and font info",
            "POST /api/v1/extract/tables": "Extract tables from PDF",
            "POST /api/v1/extract/toc": "Extract table of contents",
            "POST /api/v1/extract/metadata": "Extract PDF metadata",
            "POST /api/v1/extract/all": "Extract all information",
            "GET /api/v1/samples": "List available sample PDFs",
            "GET /api/v1/samples/{name}": "Download a sample PDF",
            "GET /api/v1/samples/{name}/extract/{type}": "Extract from a sample PDF"
        }
    }


@router.post("/extract/text", summary="提取PDF文本内容")
async def extract_text_endpoint(
    file: UploadFile = File(..., description="PDF文件"),
    page: Optional[int] = Query(None, description="页码（从1开始），不指定则提取所有页")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        pdf_bytes = await file.read()
        page_num = page - 1 if page else None
        result = extract_pdf(pdf_bytes, "text", page_num)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/extract/layout", summary="提取PDF布局信息（含位置、字体、多栏）")
async def extract_layout_endpoint(
    file: UploadFile = File(..., description="PDF文件"),
    page: Optional[int] = Query(None, description="页码（从1开始），不指定则提取所有页")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        pdf_bytes = await file.read()
        page_num = page - 1 if page else None
        result = extract_pdf(pdf_bytes, "layout", page_num)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/extract/tables", summary="识别并提取PDF表格")
async def extract_tables_endpoint(
    file: UploadFile = File(..., description="PDF文件"),
    page: Optional[int] = Query(None, description="页码（从1开始），不指定则提取所有页")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        pdf_bytes = await file.read()
        page_num = page - 1 if page else None
        result = extract_pdf(pdf_bytes, "tables", page_num)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/extract/toc", summary="提取PDF目录/书签")
async def extract_toc_endpoint(
    file: UploadFile = File(..., description="PDF文件")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        pdf_bytes = await file.read()
        result = extract_pdf(pdf_bytes, "toc")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/extract/metadata", summary="提取PDF元信息")
async def extract_metadata_endpoint(
    file: UploadFile = File(..., description="PDF文件")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        pdf_bytes = await file.read()
        result = extract_pdf(pdf_bytes, "metadata")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/extract/all", summary="提取PDF所有信息（文本+布局+表格+目录+元信息）")
async def extract_all_endpoint(
    file: UploadFile = File(..., description="PDF文件")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        pdf_bytes = await file.read()
        result = extract_pdf(pdf_bytes, "all")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/samples", summary="获取可用的测试样本PDF列表")
async def list_samples():
    try:
        if not SAMPLES_DIR.exists():
            return {"success": True, "samples": [], "count": 0}
        
        pdf_files = list(SAMPLES_DIR.glob("*.pdf"))
        samples = []
        
        for pdf_file in pdf_files:
            file_size = pdf_file.stat().st_size
            samples.append({
                "name": pdf_file.name,
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2),
                "description": get_sample_description(pdf_file.name)
            })
        
        return {
            "success": True,
            "count": len(samples),
            "samples": samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取样本列表失败: {str(e)}")


def get_sample_description(filename: str) -> str:
    descriptions = {
        "sample1_single_column.pdf": "单栏文本PDF - 标准单栏文章格式",
        "sample2_multi_column.pdf": "多栏排版PDF - 双栏学术论文格式",
        "sample3_tables.pdf": "含表格PDF - 包含多个结构化表格",
        "sample4_toc.pdf": "含目录PDF - 带有完整大纲和书签",
        "sample5_scanned.pdf": "扫描转PDF - 模拟扫描件格式"
    }
    return descriptions.get(filename, "测试PDF样本")


@router.get("/samples/{name}", summary="下载指定的测试样本PDF")
async def get_sample(name: str):
    try:
        pdf_path = SAMPLES_DIR / name
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"样本不存在: {name}")
        
        return FileResponse(
            path=pdf_path,
            filename=name,
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取样本失败: {str(e)}")


@router.get("/samples/{name}/extract/{extract_type}", summary="对测试样本执行抽取")
async def extract_sample_endpoint(
    name: str,
    extract_type: str = FastAPIPath(..., description="抽取类型: text, layout, tables, toc, metadata, all"),
    page: Optional[int] = Query(None, description="页码（从1开始）")
):
    valid_types = ["text", "layout", "tables", "toc", "metadata", "all"]
    if extract_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的抽取类型，必须是: {', '.join(valid_types)}")
    
    try:
        pdf_path = SAMPLES_DIR / name
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"样本不存在: {name}")
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        page_num = page - 1 if page else None
        result = extract_pdf(pdf_bytes, extract_type, page_num)
        
        return {"success": True, "sample": name, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
