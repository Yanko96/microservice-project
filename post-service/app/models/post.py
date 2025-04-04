from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base

# 帖子标签关联表
post_tag_association = Table(
    'post_tag',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('tag_name', String, primary_key=True)
)

# 帖子媒体类型枚举
class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    NONE = "none"

# 帖子可见性枚举
class Visibility(str, enum.Enum):
    PUBLIC = "public"      # 所有人可见
    FOLLOWERS = "followers" # 仅关注者可见
    PRIVATE = "private"    # 仅自己可见

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # 外部用户ID，不是外键
    
    # 帖子内容
    content = Column(Text, nullable=True)
    media_type = Column(Enum(MediaType), nullable=False, default=MediaType.NONE)
    media_urls = Column(JSON, nullable=True)  # 存储媒体URL的JSON数组
    
    # 元数据
    location = Column(String, nullable=True)
    visibility = Column(Enum(Visibility), nullable=False, default=Visibility.PUBLIC)
    is_edited = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    
    # 统计数据（冗余存储，方便查询）
    comment_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # 标签（多对多关系）
    tags = relationship("Tag", secondary=post_tag_association, back_populates="posts")
    
    # 评论（一对多关系）
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    # 反应（一对多关系）
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 标签模型
class Tag(Base):
    __tablename__ = "tags"
    
    name = Column(String, primary_key=True)
    post_count = Column(Integer, default=0)
    
    # 多对多关系
    posts = relationship("Post", secondary=post_tag_association, back_populates="tags")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())