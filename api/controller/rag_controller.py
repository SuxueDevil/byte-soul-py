"""RAG 控制器：文件上传入库"""
from fastapi import APIRouter, UploadFile, File
from api.service.rag_service import ragService
from api.schemas.rag import FileDTO
from api.schemas.response import Response

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


@rag_router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """
    上传文档入库。
    @param file: 上传的文件
    @return: 入库结果
    """
    # 一、构建 FileDTO，Pydantic 校验 filename 非空
    assert file.filename is not None
    # 二、调用 service 入库
    count = ragService.ingest(FileDTO(filename=file.filename, content=await file.read()))
    return Response.success({"chunk_count": count})