from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, JSON
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.db.session import Base

# 帖子标签关联表
post_tag_association = Table(
    'post_tag',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('tag_name', String, ForeignKey('tags.name'), primary_key=True)
)

# 帖子媒体类型枚举
class MediaType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    LINK = "LINK"
    NONE = "NONE"

media_type_enum = PgEnum(MediaType, name="mediatype", create_type=False)

# 帖子可见性枚举
class Visibility(str, enum.Enum):
    PUBLIC = "PUBLIC"      # 所有人可见
    FOLLOWERS = "FOLLOWERS" # 仅关注者可见
    PRIVATE = "PRIVATE"    # 仅自己可见

visibility_enum = PgEnum(Visibility, name="visibility", create_type=False)

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=True)
    media_type = Column(media_type_enum, nullable=False, server_default='NONE')
    media_urls = Column(JSON, nullable=True)
    location = Column(String, nullable=True)
    visibility = Column(visibility_enum, nullable=False, server_default='PUBLIC')
    is_edited = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    comment_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    tags = relationship("Tag", secondary=post_tag_association, back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Tag(Base):
    __tablename__ = "tags"

    name = Column(String, primary_key=True)
    post_count = Column(Integer, default=0)
    posts = relationship("Post", secondary=post_tag_association, back_populates="tags")
    created_at = Column(DateTime(timezone=True), server_default=func.now())