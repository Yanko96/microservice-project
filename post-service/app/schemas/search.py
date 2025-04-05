# app/schemas/search.py

from typing import List, Optional, Any, Dict
from datetime import date
from pydantic import BaseModel

from app.schemas.post import UserBrief

# 搜索请求模型
class SearchRequest(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    user_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None

# 搜索结果项模型
class SearchResultItem(BaseModel):
    id: int
    user_id: int
    content: Optional[str] = None
    tags: List[str] = []
    location: Optional[str] = None
    media_type: str
    visibility: str
    comment_count: int
    like_count: int
    created_at: str
    updated_at: Optional[str] = None
    
    # 可选字段，由API填充
    user: Optional[UserBrief] = None

# 搜索响应模型
class SearchResponse(BaseModel):
    total: int
    items: List[Dict[str, Any]]
    page: int
    size: int
    pages: int