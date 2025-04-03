from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
import logging
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class ElasticsearchService:
    """Elasticsearch服务类，用于索引和搜索帖子"""
    
    def __init__(self):
        """初始化Elasticsearch客户端"""
        self.client = None
        self.index_name = settings.ELASTICSEARCH_INDEX_POSTS
        self.is_ready = False
    
    async def connect(self):
        """连接到Elasticsearch服务器"""
        if self.client is not None:
            return
        
        try:
            self.client = AsyncElasticsearch(
                [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
                request_timeout=10,
                retry_on_timeout=True
            )
            # 检查连接
            await self.client.info()
            self.is_ready = True
            logger.info("成功连接到Elasticsearch")
            
            # 确保索引存在
            await self.ensure_index()
        except Exception as e:
            logger.error(f"连接Elasticsearch失败: {str(e)}")
            self.is_ready = False
    
    async def close(self):
        """关闭连接"""
        if self.client is not None:
            await self.client.close()
            self.client = None
            self.is_ready = False
            logger.info("已关闭Elasticsearch连接")
    
    async def ensure_index(self):
        """确保索引存在，不存在则创建"""
        try:
            # 检查索引是否存在
            exists = await self.client.indices.exists(index=self.index_name)
            if not exists:
                # 创建索引
                await self.create_index()
            return True
        except Exception as e:
            logger.error(f"确保索引存在失败: {str(e)}")
            return False
    
    async def create_index(self):
        """创建帖子索引，设置映射"""
        # 帖子索引映射
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "user_id": {"type": "integer"},
                    "username": {"type": "keyword"},
                    "full_name": {"type": "text"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "tags": {"type": "keyword"},
                    "location": {"type": "text"},
                    "media_type": {"type": "keyword"},
                    "visibility": {"type": "keyword"},
                    "comment_count": {"type": "integer"},
                    "like_count": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
        
        try:
            await self.client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"已创建索引: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            return False
    
    async def index_post(self, post_data: Dict[str, Any]) -> bool:
        """
        索引帖子数据
        
        参数:
            post_data: 帖子数据
        
        返回:
            是否成功索引
        """
        if not self.is_ready:
            await self.connect()
            if not self.is_ready:
                return False
        
        try:
            # 准备索引文档
            document = {
                "id": post_data.get("id"),
                "user_id": post_data.get("user_id"),
                "username": post_data.get("user", {}).get("username", ""),
                "full_name": post_data.get("user", {}).get("full_name", ""),
                "content": post_data.get("content", ""),
                "tags": [tag["name"] if isinstance(tag, dict) else tag.name for tag in post_data.get("tags", [])],
                "location": post_data.get("location", ""),
                "media_type": post_data.get("media_type", "NONE"),
                "visibility": post_data.get("visibility", "PUBLIC"),
                "comment_count": post_data.get("comment_count", 0),
                "like_count": post_data.get("like_count", 0),
                "created_at": post_data.get("created_at"),
                "updated_at": post_data.get("updated_at")
            }
            
            # 只索引公开帖子
            if document["visibility"] != "PUBLIC":
                return True
            
            await self.client.index(
                index=self.index_name,
                id=document["id"],
                body=document
            )
            
            logger.debug(f"成功索引帖子 ID: {document['id']}")
            return True
        except Exception as e:
            logger.error(f"索引帖子失败: {str(e)}")
            return False
    
    async def update_post_index(self, post_data: Dict[str, Any]) -> bool:
        """
        更新帖子索引
        
        参数:
            post_data: 帖子数据
        
        返回:
            是否成功更新
        """
        if not self.is_ready:
            await self.connect()
            if not self.is_ready:
                return False
        
        try:
            # 准备更新文档
            document = {
                "id": post_data.get("id"),
                "user_id": post_data.get("user_id"),
                "username": post_data.get("user", {}).get("username", ""),
                "full_name": post_data.get("user", {}).get("full_name", ""),
                "content": post_data.get("content", ""),
                "tags": [tag["name"] if isinstance(tag, dict) else tag.name for tag in post_data.get("tags", [])],
                "location": post_data.get("location", ""),
                "media_type": post_data.get("media_type", "NONE"),
                "visibility": post_data.get("visibility", "PUBLIC"),
                "comment_count": post_data.get("comment_count", 0),
                "like_count": post_data.get("like_count", 0),
                "created_at": post_data.get("created_at"),
                "updated_at": post_data.get("updated_at")
            }
            
            # 如果帖子变为非公开，从索引中删除
            if document["visibility"] != "PUBLIC":
                try:
                    await self.delete_post_index(document["id"])
                    return True
                except NotFoundError:
                    # 如果不存在，忽略错误
                    return True
            
            # 更新索引
            await self.client.update(
                index=self.index_name,
                id=document["id"],
                body={"doc": document}
            )
            
            logger.debug(f"成功更新帖子索引 ID: {document['id']}")
            return True
        except NotFoundError:
            # 如果文档不存在，创建新索引
            return await self.index_post(post_data)
        except Exception as e:
            logger.error(f"更新帖子索引失败: {str(e)}")
            return False
    
    async def delete_post_index(self, post_id: int) -> bool:
        """
        删除帖子索引
        
        参数:
            post_id: 帖子ID
        
        返回:
            是否成功删除
        """
        if not self.is_ready:
            await self.connect()
            if not self.is_ready:
                return False
        
        try:
            await self.client.delete(
                index=self.index_name,
                id=post_id
            )
            
            logger.debug(f"成功删除帖子索引 ID: {post_id}")
            return True
        except NotFoundError:
            # 如果不存在，视为成功
            return True
        except Exception as e:
            logger.error(f"删除帖子索引失败: {str(e)}")
            return False
    
    async def search_posts(
        self, 
        query: str, 
        tags: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """
        搜索帖子
        
        参数:
            query: 搜索关键词
            tags: 标签过滤
            user_id: 用户ID过滤
            from_date: 起始日期
            to_date: 结束日期
            page: 页码
            size: 每页大小
        
        返回:
            搜索结果
        """
        if not self.is_ready:
            await self.connect()
            if not self.is_ready:
                return {"total": 0, "items": []}
        
        try:
            # 计算分页偏移
            offset = (page - 1) * size
            
            # 构建查询
            must_queries = []
            
            # 内容搜索
            if query:
                must_queries.append({
                    "multi_match": {
                        "query": query,
                        "fields": ["content^2", "tags", "username", "full_name", "location"]
                    }
                })
            
            # 标签过滤
            if tags and len(tags) > 0:
                must_queries.append({
                    "terms": {
                        "tags": tags
                    }
                })
            
            # 用户过滤
            if user_id:
                must_queries.append({
                    "term": {
                        "user_id": user_id
                    }
                })
            
            # 日期范围过滤
            date_range = {}
            if from_date:
                date_range["gte"] = from_date
            if to_date:
                date_range["lte"] = to_date
            
            if date_range:
                must_queries.append({
                    "range": {
                        "created_at": date_range
                    }
                })
            
            # 公开帖子过滤
            must_queries.append({
                "term": {
                    "visibility": "PUBLIC"
                }
            })
            
            # 如果没有任何过滤条件，默认返回所有公开帖子
            search_query = {
                "from": offset,
                "size": size,
                "query": {
                    "bool": {
                        "must": must_queries if must_queries else [{"match_all": {}}]
                    }
                },
                "sort": [
                    {"created_at": {"order": "desc"}}
                ]
            }
            
            # 执行搜索
            response = await self.client.search(
                index=self.index_name,
                body=search_query
            )
            
            # 解析结果
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            
            # 构建返回结果
            items = [hit["_source"] for hit in hits]
            
            return {
                "total": total,
                "items": items,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        except Exception as e:
            logger.error(f"搜索帖子失败: {str(e)}")
            return {"total": 0, "items": [], "page": page, "size": size, "pages": 0}

# 创建Elasticsearch服务单例
es_service = ElasticsearchService()