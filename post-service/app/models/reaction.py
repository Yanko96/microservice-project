from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base

# 反应类型枚举
class ReactionType(str, enum.Enum):
    LIKE = "like"           # 喜欢
    LOVE = "love"           # 爱心
    HAHA = "haha"           # 笑脸
    WOW = "wow"             # 惊讶
    SAD = "sad"             # 悲伤
    ANGRY = "angry"         # 生气

class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户信息（外部引用）
    user_id = Column(Integer, nullable=False, index=True)  # 外部用户ID，不是外键
    
    # 反应类型
    type = Column(Enum(ReactionType), nullable=False, default=ReactionType.LIKE)
    
    # 关联帖子（可选，如果是对评论的反应则为null）
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True)
    post = relationship("Post", back_populates="reactions")
    
    # 关联评论（可选，如果是对帖子的反应则为null）
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 确保一个用户对一个帖子或评论只能有一个反应
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='uix_user_post_reaction'),
        UniqueConstraint('user_id', 'comment_id', name='uix_user_comment_reaction'),
    )