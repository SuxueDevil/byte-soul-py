"""数据结构定义"""
from dataclasses import dataclass, field
from enum import Enum


class FileType(Enum):
    """支持的文件类型"""
    MD = ".md"
    PDF = ".pdf"
    DOCX = ".docx"
    TXT = ".txt"


class ChunkMode(Enum):
    """切割模式"""
    GENERAL = "general"           # 通用模式：单层切割
    PARENT_CHILD = "parent_child" # 父子模式：双层切割


@dataclass
class ParentChunk:
    """父块：提供完整上下文"""
    doc_hash: str           # 文档哈希
    chunk_index: int        # 父块序号
    content: str            # 父块内容
    section_title: str      # 章节标题
    metadata: dict = field(default_factory=dict)  # 元数据


@dataclass
class ChildChunk:
    """子块：精准匹配查询"""
    doc_hash: str           # 文档哈希
    parent_index: int       # 关联的父块序号
    chunk_index: int        # 子块序号（全局）
    content: str            # 子块内容
    metadata: dict = field(default_factory=dict)  # 元数据
