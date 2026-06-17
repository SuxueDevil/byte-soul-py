"""
Milvus 建集合脚本
执行：python data/milvus.py
"""
from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema

# 零、TODO milvus的连接地址+端口
URL = "http://localhost:19530"
COLLECTION_NAME = "bs_rag"
DIMENSION = 1024

client = MilvusClient(uri=URL)

# 一、定义字段
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="pg_id", dtype=DataType.INT64),
    FieldSchema(name="doc_hash", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
]

# 二、创建集合
schema = CollectionSchema(fields=fields)
client.create_collection(
    collection_name=COLLECTION_NAME,
    schema=schema,
)
print(f"集合 {COLLECTION_NAME} 创建成功")

# 三、创建向量索引
index_params = client.prepare_index_params()
index_params.add_index(
    field_name="vector",
    index_type="AUTOINDEX",
    metric_type="COSINE",
)
client.create_index(
    collection_name=COLLECTION_NAME,
    index_params=index_params,
)
print(f"索引创建成功")
