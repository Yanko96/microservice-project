from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import httpx

from app.api.deps import get_current_user, check_ownership, get_pagination_params, get_user_service_client
from app.db.session import get_db
from app.models.post import Post, Tag, MediaType, Visibility
from app.models.reaction import Reaction
from app.schemas.post import (
    PostCreate, PostUpdate, Post as PostSchema, PostDetail, PostPage, PostFilter, 
    TagInDB, UserBrief
)
from app.utils.storage import storage
from app.core.config import settings

router = APIRouter()


def build_post_schema(post: Post, user_info: Optional[Dict[str, Any]] = None, reaction: Optional[Reaction] = None) -> PostSchema:
    return PostSchema(
        id=post.id,
        user_id=post.user_id,
        content=post.content,
        visibility=post.visibility,
        location=post.location,
        media_type=post.media_type,
        media_urls=post.media_urls,
        is_edited=post.is_edited,
        is_pinned=post.is_pinned,
        comment_count=post.comment_count,
        like_count=post.like_count,
        share_count=post.share_count,
        view_count=post.view_count,
        tags=[tag.name for tag in post.tags],
        created_at=post.created_at,
        updated_at=post.updated_at,
        user=user_info,
        current_user_reaction=reaction.type.value if reaction else None
    )


@router.post("/", response_model=PostSchema)
async def create_post(
    *,
    db: Session = Depends(get_db),
    post_in: PostCreate = None,
    content: str = Form(None),
    visibility: Visibility = Form(Visibility.PUBLIC),
    media_type: MediaType = Form(MediaType.NONE),
    location: str = Form(None),
    tag_names: str = Form(""),
    files: List[UploadFile] = File(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    if post_in:
        post_data = post_in.dict()
    else:
        post_data = {
            "content": content,
            "visibility": visibility,
            "location": location,
            "tag_names": tag_names.split(",") if tag_names else []
        }

    if not post_data.get("content") and not files:
        raise HTTPException(status_code=400, detail="必须提供内容或媒体文件")

    post = Post(
        user_id=current_user["id"],
        content=post_data.get("content"),
        visibility=post_data.get("visibility", Visibility.PUBLIC),
        location=post_data.get("location"),
        media_type=post_data.get("media_type", MediaType.NONE),
        media_urls=[]
    )
    print("**************", post.visibility)
    print("**************", post.media_type)

    if files and any(file.filename for file in files):
        file_list = []
        media_type = post_data.get("media_type", MediaType.NONE)

        for file in files:
            if not file.filename:
                continue

            if file.content_type in settings.ALLOWED_IMAGE_TYPES:
                if media_type and media_type != MediaType.IMAGE:
                    raise HTTPException(status_code=400, detail="不能混合上传不同类型的媒体文件")
                media_type = MediaType.IMAGE
            elif file.content_type in settings.ALLOWED_VIDEO_TYPES:
                if media_type and media_type != MediaType.VIDEO:
                    raise HTTPException(status_code=400, detail="不能混合上传不同类型的媒体文件")
                media_type = MediaType.VIDEO
            else:
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")

            object_name = f"user_{current_user['id']}/post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(file_list)}"
            file_url = await storage.upload_file(file=file, folder="posts", object_name=object_name, tags={"user_id": str(current_user["id"])})
            file_info = {"url": file_url, "type": media_type}
            file_list.append(file_info)

        if file_list:
            post.media_type = media_type
            post.media_urls = file_list
        print("**********************", media_type)

    if "tag_names" in post_data and post_data["tag_names"]:
        for tag_name in post_data["tag_names"]:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, post_count=1)
                db.add(tag)
            else:
                tag.post_count += 1
            post.tags.append(tag)
    db.add(post)
    db.commit()
    db.refresh(post)

    return build_post_schema(post, user_info=current_user)
