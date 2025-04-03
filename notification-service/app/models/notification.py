from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, JSON
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from app.db.session import Base

class NotificationType(str, enum.Enum):
    FOLLOW = "FOLLOW"            # 有人关注了你
    POST_LIKE = "POST_LIKE"      # 有人点赞了你的帖子
    POST_COMMENT = "POST_COMMENT" # 有人评论了你的帖子
    COMMENT_LIKE = "COMMENT_LIKE" # 有人点赞了你的评论
    COMMENT_REPLY = "COMMENT_REPLY" # 有人回复了你的评论
    MENTION = "MENTION"          # 有人在帖子或评论中提到了你
    SYSTEM = "SYSTEM"            # 系统通知

notification_type_enum = PgEnum(NotificationType, name="notificationtype", create_type=False)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # 接收通知的用户ID
    user_id = Column(Integer, nullable=False, index=True)
    
    # 通知类型
    type = Column(notification_type_enum, nullable=False)
    
    # 通知标题和正文
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    
    # 通知发送者信息
    sender_id = Column(Integer, nullable=True)  # 可能是系统通知，没有发送者
    sender_name = Column(String, nullable=True)
    sender_avatar = Column(String, nullable=True)
    
    # 通知相关资源（例如帖子ID、评论ID等）
    resource_type = Column(String, nullable=True)  # post, comment, etc.
    resource_id = Column(Integer, nullable=True)
    
    # 通知元数据（存储任何其他相关信息）
    meta_data = Column(JSON, nullable=True)
    
    # 通知状态
    is_read = Column(Boolean, default=False)
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"