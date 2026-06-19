"""RAG 控制器：文件上传入库"""
from fastapi import APIRouter, UploadFile, File
from api.service.rag_service import ragService
from api.schemas.response import Response

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


@rag_router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """
    上传文档入库。
    @param file: 上传的文件
    @return: 入库结果
    """
    return Response.success({
        "chunk_count": ragService.ingest(filename=file.filename, content=await file.read())
    })
