from typing import List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, validator

from app.models.reaction import ReactionType
from app.schemas.post import UserBrief

# 创建反应的Schema
class ReactionCreate(BaseModel):
    type: ReactionType = ReactionType.LIKE
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    
    @validator('post_id', 'comment_id')
    def validate_target(cls, v, values):
        # 确保至少指定了一个目标（帖子或评论）
        if 'post_id' in values and values['post_id'] is None and v is None:
            raise ValueError('必须指定post_id或comment_id')
        return v

# 更新反应的Schema
class ReactionUpdate(BaseModel):
    type: Optional[ReactionType] = None

# 返回给前端的反应Schema
class Reaction(BaseModel):
    id: int
    user_id: int
    type: ReactionType
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    created_at: datetime
    
    # 扩展字段（可能通过API调用填充）
    user: Optional[UserBrief] = None
    
    class Config:
        from_attributes = True

# 用于数据库操作的反应Schema
class ReactionInDB(Reaction):
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 反应统计
class ReactionCount(BaseModel):
    type: ReactionType
    count: int

# 反应统计结果
class ReactionSummary(BaseModel):
    total: int
    counts: List[ReactionCount]
    # 是否包含当前用户的反应
    has_reacted: bool = False
    # 当前用户的反应类型
    current_user_reaction: Optional[ReactionType] = None