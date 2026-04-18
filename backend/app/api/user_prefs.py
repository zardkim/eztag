"""사용자별 개인 설정 API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional

from app.database import get_db
from app.core.auth import get_current_user
from app.models.user_pref import UserPreference

router = APIRouter(prefix="/api/user/prefs", tags=["user-prefs"])

ALLOWED_KEYS = {"recent_folders"}


class UserPrefsUpdate(BaseModel):
    prefs: Dict[str, Optional[str]]


@router.get("/")
def get_prefs(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """현재 로그인 사용자의 개인 설정 반환."""
    rows = db.query(UserPreference).filter(UserPreference.user_id == user.id).all()
    return {r.key: r.value for r in rows}


@router.post("/")
def update_prefs(
    body: UserPrefsUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """현재 로그인 사용자의 개인 설정 저장 (upsert)."""
    for key, value in body.prefs.items():
        if key not in ALLOWED_KEYS:
            continue
        row = db.query(UserPreference).filter_by(user_id=user.id, key=key).first()
        if row:
            row.value = value
        else:
            db.add(UserPreference(user_id=user.id, key=key, value=value))
    db.commit()
    return {"ok": True}
