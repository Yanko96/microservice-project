from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.db.session import Base

# 反应类型枚举
class ReactionType(str, enum.Enum):
    LIKE = "like"           # 喜欢
    LOVE = "love"           # 爱心
    HAHA = "haha"           # 笑脸
    WOW = "wow"             # 惊讶
    SAD = "sad"             # 悲伤
    ANGRY = "angry"         # 生气

reaction_enum = PgEnum(ReactionType, name="reactiontype", create_type=False)

class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(reaction_enum, nullable=False, server_default="like")
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True)
    post = relationship("Post", back_populates="reactions")
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        # 限制一个用户对同一帖子或评论只能有一个反应
        UniqueConstraint('user_id', 'post_id', name='uix_user_post_reaction'),
        UniqueConstraint('user_id', 'comment_id', name='uix_user_comment_reaction'),
    )