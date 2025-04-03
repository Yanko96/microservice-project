from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    
    # 用户信息（外部引用）
    user_id = Column(Integer, nullable=False, index=True)  # 外部用户ID，不是外键
    
    # 帖子ID（外键关联到Post）
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    post = relationship("Post", back_populates="comments")
    
    # 父评论ID（自引用，用于回复）
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    parent = relationship("Comment", remote_side=[id], backref="replies")
    
    # 统计数据
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # 状态
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)  # 软删除标记
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())