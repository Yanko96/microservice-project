from typing import Any, Dict, List, Optional
from datetime import datetime, date

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

from app.api.endpoints.search import search_posts as original_search_posts, search_posts_advanced as original_search_posts_advanced
from app.schemas.search import SearchResponse, SearchRequest

router = APIRouter()

@router.get("/search", response_model=SearchResponse)
async def search_posts_endpoint(
    query: str = Query(None, description="搜索关键词"),
    tags: List[str] = Query(None, description="按标签筛选"),
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
    from_date: Optional[date] = Query(None, description="起始日期"),
    to_date: Optional[date] = Query(None, description="结束日期"),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    搜索帖子 (重定向到search.py中的功能)
    """
    return await original_search_posts(
        query=query,
        tags=tags,
        user_id=user_id,
        from_date=from_date,
        to_date=to_date,
        pagination=pagination,
        current_user=current_user,
        user_client=user_client
    )

@router.post("/search", response_model=SearchResponse)
async def search_posts_advanced_endpoint(
    search_request: SearchRequest,
    pagination: Dict[str, int] = Depends(get_pagination_params),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    高级搜索帖子
    """
    return await original_search_posts_advanced(
        search_request=search_request,
        pagination=pagination,
        current_user=current_user,
        user_client=user_client,
    )


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

@router.post("/text", response_model=PostSchema)
async def create_text_post(
    *,
    db: Session = Depends(get_db),
    content: str = Form(...),
    visibility: Visibility = Form(Visibility.PUBLIC),
    location: Optional[str] = Form(None),
    tag_names: Optional[str] = Form(""),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    if not content.strip():
        raise HTTPException(status_code=400, detail="文本内容不能为空")

    post = Post(
        user_id=current_user["id"],
        content=content,
        visibility=visibility,
        location=location,
        media_type=MediaType.NONE,
        media_urls=[]
    )

    for tag_name in tag_names.split(","):
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

@router.post("/media", response_model=PostSchema)
async def create_media_post(
    *,
    db: Session = Depends(get_db),
    visibility: Visibility = Form(Visibility.PUBLIC),
    location: Optional[str] = Form(None),
    tag_names: Optional[str] = Form(""),
    files: List[UploadFile] = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    if not files or not any(file.filename for file in files):
        raise HTTPException(status_code=400, detail="请上传至少一个有效文件")

    post = Post(
        user_id=current_user["id"],
        visibility=visibility,
        location=location,
        content=None,
        media_type=MediaType.NONE,
        media_urls=[]
    )

    file_list = []
    media_type = None

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
        file_info = {"url": file_url, "type": media_type.value}
        file_list.append(file_info)

    post.media_type = media_type or MediaType.NONE
    post.media_urls = file_list

    for tag_name in tag_names.split(","):
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


# @router.post("/", response_model=PostSchema)
# async def create_post(
#     *,
#     db: Session = Depends(get_db),
#     post_in: PostCreate = None,
#     content: str = Form(None),
#     visibility: Visibility = Form(Visibility.PUBLIC),
#     location: str = Form(None),
#     tag_names: str = Form(""),
#     files: List[UploadFile] = File(None),
#     current_user: Dict[str, Any] = Depends(get_current_user),
# ) -> Any:
#     if post_in:
#         post_data = post_in.dict()
#     else:
#         post_data = {
#             "content": content,
#             "visibility": visibility,
#             "location": location,
#             "tag_names": tag_names.split(",") if tag_names else []
#         }

#     if not post_data.get("content") and not files:
#         raise HTTPException(status_code=400, detail="必须提供内容或媒体文件")

#     post = Post(
#         user_id=current_user["id"],
#         content=post_data.get("content"),
#         visibility=post_data.get("visibility", Visibility.PUBLIC),
#         location=post_data.get("location"),
#         media_type=MediaType.NONE,
#         media_urls=[]
#     )

#     if files and any(file.filename for file in files):
#         file_list = []
#         media_type = None

#         for file in files:
#             if not file.filename:
#                 continue

#             if file.content_type in settings.ALLOWED_IMAGE_TYPES:
#                 if media_type and media_type != MediaType.IMAGE:
#                     raise HTTPException(status_code=400, detail="不能混合上传不同类型的媒体文件")
#                 media_type = MediaType.IMAGE
#             elif file.content_type in settings.ALLOWED_VIDEO_TYPES:
#                 if media_type and media_type != MediaType.VIDEO:
#                     raise HTTPException(status_code=400, detail="不能混合上传不同类型的媒体文件")
#                 media_type = MediaType.VIDEO
#             else:
#                 raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")

#             object_name = f"user_{current_user['id']}/post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(file_list)}"
#             file_url = await storage.upload_file(file=file, folder="posts", object_name=object_name, tags={"user_id": str(current_user["id"])})
#             file_info = {"url": file_url, "type": media_type.value}
#             file_list.append(file_info)

#         if file_list:
#             post.media_type = media_type
#             post.media_urls = file_list

#     if "tag_names" in post_data and post_data["tag_names"]:
#         for tag_name in post_data["tag_names"]:
#             tag_name = tag_name.strip().lower()
#             if not tag_name:
#                 continue
#             tag = db.query(Tag).filter(Tag.name == tag_name).first()
#             if not tag:
#                 tag = Tag(name=tag_name, post_count=1)
#                 db.add(tag)
#             else:
#                 tag.post_count += 1
#             post.tags.append(tag)

#     db.add(post)
#     db.commit()
#     db.refresh(post)

#     return build_post_schema(post, user_info=current_user)


@router.get("/", response_model=PostPage)
async def read_posts(
    db: Session = Depends(get_db),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    user_id: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    visibility: Optional[Visibility] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client),
) -> Any:
    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size

    query = db.query(Post)

    if user_id:
        query = query.filter(Post.user_id == user_id)
    if tag:
        query = query.join(Post.tags).filter(Tag.name == tag)
    if visibility:
        if visibility == Visibility.PRIVATE and not (current_user["id"] == user_id or current_user.get("is_superuser")):
            raise HTTPException(status_code=403, detail="无权查看私有帖子")
        query = query.filter(Post.visibility == visibility)
    else:
        query = query.filter((Post.visibility == Visibility.PUBLIC) | (Post.user_id == current_user["id"]))

    query = query.order_by(Post.created_at.desc())
    total = query.count()
    posts = query.offset(skip).limit(size).all()

    user_ids = list(set(post.user_id for post in posts))
    users = {}
    if user_ids:
        try:
            response = await user_client.get("/users/batch", params={"ids": ",".join(map(str, user_ids))})
            if response.status_code == 200:
                users = {user["id"]: user for user in response.json()}
        except httpx.RequestError:
            pass

    items = []
    for post in posts:
        reaction = db.query(Reaction).filter(Reaction.post_id == post.id, Reaction.user_id == current_user["id"]).first()
        post_dict = build_post_schema(post, user_info=users.get(post.user_id), reaction=reaction)
        items.append(post_dict)

    pages = (total + size - 1) // size
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.get("/{post_id}", response_model=PostDetail)
async def read_post(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client),
) -> Any:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if post.visibility != Visibility.PUBLIC and post.user_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="无权查看该帖子")

    post.view_count += 1
    db.commit()

    user_info = None
    try:
        response = await user_client.get(f"/users/id/{post.user_id}")
        if response.status_code == 200:
            user_info = response.json()
    except httpx.RequestError:
        pass

    reaction = db.query(Reaction).filter(Reaction.post_id == post.id, Reaction.user_id == current_user["id"]).first()
    post_detail = build_post_schema(post, user_info=user_info, reaction=reaction)
    return post_detail


@router.put("/{post_id}", response_model=PostSchema)
async def update_post(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    post_in: PostUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if not await check_ownership(post.user_id, current_user):
        raise HTTPException(status_code=403, detail="无权修改该帖子")

    update_data = post_in.dict(exclude_unset=True)

    if "tag_names" in update_data:
        for tag in post.tags:
            tag.post_count -= 1
            if tag.post_count <= 0:
                db.delete(tag)
        post.tags = []

        for tag_name in update_data["tag_names"]:
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

        del update_data["tag_names"]

    for field, value in update_data.items():
        setattr(post, field, value)

    post.is_edited = True
    db.add(post)
    db.commit()
    db.refresh(post)

    return build_post_schema(post, user_info=current_user)


@router.post("/{post_id}/pin", response_model=PostSchema)
async def pin_post(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if not await check_ownership(post.user_id, current_user):
        raise HTTPException(status_code=403, detail="无权置顶该帖子")

    post.is_pinned = not post.is_pinned
    db.add(post)
    db.commit()
    db.refresh(post)

    return build_post_schema(post, user_info=current_user)
