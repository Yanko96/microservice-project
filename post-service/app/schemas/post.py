from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator

from app.models.post import MediaType, Visibility

# 标签相关Schema
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class TagUpdate(BaseModel):
    post_count: Optional[int] = None

class TagInDB(BaseModel):
    name: str
    post_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 帖子媒体相关Schema
class PostMedia(BaseModel):
    url: str
    type: str  # 媒体类型: image, video, thumbnail等
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None  # 视频时长（秒）

# 帖子基础Schema
class PostBase(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    visibility: Visibility = Visibility.PUBLIC
    location: Optional[str] = None

# 创建帖子的Schema
class PostCreate(PostBase):
    tag_names: Optional[List[str]] = []
    
    @validator('tag_names')
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError('标签数量不能超过10个')
        return v

# 更新帖子的Schema
class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    visibility: Optional[Visibility] = None
    location: Optional[str] = None
    tag_names: Optional[List[str]] = None
    is_pinned: Optional[bool] = None

# 用于搜索和筛选的Schema
class PostFilter(BaseModel):
    user_id: Optional[int] = None
    tag_name: Optional[str] = None
    visibility: Optional[Visibility] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# 用户简要信息（帖子中包含的）
class UserBrief(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

# 返回给前端的帖子Schema
class Post(PostBase):
    id: int
    user_id: int
    media_type: MediaType
    media_urls: Optional[List[PostMedia]] = None
    is_edited: bool
    is_pinned: bool
    comment_count: int
    like_count: int
    share_count: int
    view_count: int
    tags: List[str] = []  # 简化为标签名列表
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 扩展字段（可能通过API调用填充）
    user: Optional[UserBrief] = None
    current_user_reaction: Optional[str] = None  # 当前用户的反应类型
    
    class Config:
        from_attributes = True

# 帖子详情（包含更多信息）
class PostDetail(Post):
    # 可能包含热门评论等额外信息
    top_comments: Optional[List[Any]] = None  # 将在API中填充
    
    class Config:
        from_attributes = True

# 用于数据库操作的帖子Schema
class PostInDB(Post):
    class Config:
        from_attributes = True

# 分页结果
class PostPage(BaseModel):
    items: List[Post]
    total: int
    page: int
    size: int
    pages: int