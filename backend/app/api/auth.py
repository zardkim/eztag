"""인증 API: 초기 설정, 로그인, 현재 사용자."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.core.auth import hash_password, verify_password, create_token, get_current_user, validate_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SetupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/check-setup")
def check_setup(db: Session = Depends(get_db)):
    """계정이 하나도 없으면 needs_setup=True 반환."""
    count = db.query(User).count()
    return {"needs_setup": count == 0}


@router.post("/setup")
def setup(req: SetupRequest, db: Session = Depends(get_db)):
    """최초 관리자 계정 생성 (계정이 없을 때만 가능)."""
    if db.query(User).count() > 0:
        raise HTTPException(status_code=400, detail="Setup already completed")
    if not req.username.strip():
        raise HTTPException(status_code=422, detail="Username required")
    validate_password(req.password)

    user = User(
        username=req.username.strip(),
        password_hash=hash_password(req.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id)
    return {"token": token, "username": user.username, "role": user.role}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """로그인 → JWT 토큰 반환."""
    from app.core.log_writer import write_activity_log
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        write_activity_log(db, "login", f"로그인 실패: {req.username}",
                           action="login_failed", username=req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id)
    write_activity_log(db, "login", f"로그인: {user.username}",
                       action="login_success", username=user.username)
    return {"token": token, "username": user.username, "role": user.role}


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    """현재 로그인 사용자 정보."""
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """비밀번호 변경."""
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")
    validate_password(req.new_password)
    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"ok": True}
