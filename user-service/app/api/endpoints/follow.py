from fastapi import APIRouter, Depends, HTTPException, status
import asyncio
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.follow import Follow
from app.api.deps import get_current_user  # 假设你已有认证依赖
from app.core.kafka_producer import send_follow_event

router = APIRouter()

@router.post("/users/{user_id}/follow", status_code=201)
async def follow_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")

    exists = db.query(Follow).filter_by(follower_id=current_user.id, followee_id=user_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="已关注该用户")

    new_follow = Follow(follower_id=current_user.id, followee_id=user_id)
    db.add(new_follow)
    db.commit()
    asyncio.create_task(send_follow_event(follower_id=current_user.id, followee_id=user_id))
    return {"msg": "关注成功"}

@router.delete("/users/{user_id}/unfollow", status_code=200)
def unfollow_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    follow = db.query(Follow).filter_by(follower_id=current_user.id, followee_id=user_id).first()
    if not follow:
        raise HTTPException(status_code=404, detail="未关注该用户")

    db.delete(follow)
    db.commit()
    return {"msg": "取消关注成功"}

@router.get("/users/{user_id}/followers")
def get_followers(user_id: int, db: Session = Depends(get_db)):
    followers = db.query(Follow).filter_by(followee_id=user_id).all()
    return {"followers": [f.follower_id for f in followers]}

@router.get("/users/{user_id}/following")
def get_following(user_id: int, db: Session = Depends(get_db)):
    following = db.query(Follow).filter_by(follower_id=user_id).all()
    return {"following": [f.followee_id for f in following]}
