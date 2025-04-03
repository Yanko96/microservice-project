from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.post import UserBrief

# 评论基础Schema
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)

# 创建评论的Schema
class CommentCreate(CommentBase):
    post_id: int
    parent_id: Optional[int] = None

# 更新评论的Schema
class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=500)

# 评论过滤条件
class CommentFilter(BaseModel):
    post_id: Optional[int] = None
    user_id: Optional[int] = None
    parent_id: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# 返回给前端的评论Schema
class Comment(CommentBase):
    id: int
    user_id: int
    post_id: int
    parent_id: Optional[int] = None
    like_count: int
    reply_count: int
    is_edited: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 扩展字段（可能通过API调用填充）
    user: Optional[UserBrief] = None
    current_user_reaction: Optional[str] = None  # 当前用户的反应类型
    
    class Config:
        from_attributes = True

# 评论详情（包含回复等）
class CommentDetail(Comment):
    replies: Optional[List['CommentDetail']] = None
    
    class Config:
        from_attributes = True

# 避免循环引用问题
CommentDetail.model_rebuild()

# 用于数据库操作的评论Schema
class CommentInDB(Comment):
    is_deleted: bool
    
    class Config:
        from_attributes = True

# 分页结果
class CommentPage(BaseModel):
    items: List[Comment]
    total: int
    page: int
    size: int
    pages: int