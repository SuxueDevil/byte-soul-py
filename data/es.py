"""
Elasticsearch 建索引脚本
执行：python data/es.py
"""
from elasticsearch import Elasticsearch

# 零、TODO es的连接地址+端口
URL = "http://localhost:9200"
INDEX_NAME = "bs_rag"

es = Elasticsearch([URL])

# 一、定义 mapping
mapping = {
    "mappings": {
        "properties": {
            "pg_id":    {"type": "integer"},
            "doc_hash": {"type": "keyword"},
            "content":  {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
        }
    }
}

# 二、创建索引
es.indices.create(index=INDEX_NAME, body=mapping)
print(f"索引 {INDEX_NAME} 创建成功")
