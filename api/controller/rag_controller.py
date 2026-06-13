"""RAG 控制器：文件上传入库"""
from fastapi import APIRouter, UploadFile, File, Depends
from api.service.rag_service import RagService, get_rag_service
from api.schemas.rag import FileDTO
from api.schemas.response import Response

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


@rag_router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    rag_service: RagService = Depends(get_rag_service),
):
    """
    上传文档入库。
    @param file: 上传的文件
    @param rag_service: RAG 服务（依赖注入）
    @return: 入库结果
    """
    # 一、构建 FileDTO，Pydantic 校验 filename 非空
    assert file.filename is not None
    # 二、调用 service 入库
    count = rag_service.ingest(FileDTO(filename=file.filename, content=await file.read()))
    return Response.success({"chunk_count": count})
