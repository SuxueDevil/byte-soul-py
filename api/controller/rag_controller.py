"""RAG 控制器：文档入库 + 查询"""
from fastapi import APIRouter, UploadFile, File
from api.service.rag_service import ragService
from api.schemas.response import Response

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


@rag_router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """上传文档入库"""
    return Response.success({
        "chunk_count": await ragService.ingest(filename=file.filename, content=await file.read())
    })


@rag_router.get("/documents")
async def list_documents():
    """文档列表"""
    return Response.success(await ragService.list_documents())


@rag_router.get("/documents/{doc_hash}/chunks")
async def get_chunks(doc_hash: str):
    """获取文档的 chunk 列表"""
    return Response.success(await ragService.get_chunks(doc_hash))


@rag_router.delete("/documents/{doc_hash}")
async def delete_document(doc_hash: str):
    """删除文档（三库联删）"""
    return Response.success({"deleted_count": await ragService.delete_document(doc_hash)})
