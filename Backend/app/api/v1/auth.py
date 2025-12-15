from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import err, ok
from app.core.logging import log
from app.db.session import get_db
from app.middleware.rate_limit import forgot_rate_limit, signup_rate_limit
from app.schemas.auth import AuthOut, ForgotIn, LoginIn, LogoutIn, RefreshIn, ResetIn, SignupIn
from app.schemas.user import UserOut
from app.services.auth_service import (
    RefreshError,
    authenticate_user,
    create_user,
    get_user_by_email,
    issue_tokens,
    refresh_tokens,
    revoke_device_tokens,
)
from app.services.events import publish_event
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth")


@router.post("/signup", response_model=AuthOut, dependencies=[signup_rate_limit])
async def signup(
    request: Request,
    body: SignupIn,
    db: AsyncSession = Depends(get_db),
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
):
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=409, detail=err(request, "user_exists", "User already exists"))

    try:
        user = await create_user(db, body.email, body.password, body.full_name, body.timezone)
        device_id = x_device_id or "default"
        access, refresh = await issue_tokens(db, user, device_id)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=err(request, "user_exists", "User already exists"))

    publish_event(
        name="User_SignUp",
        request_id=request.state.request_id,
        user_id=str(user.id),
        payload={"device_id": device_id},
    )

    log.info(
        "auth_signup",
        request_id=request.state.request_id,
        user_id=str(user.id),
        device_id=device_id,
        timezone=user.timezone,
    )

    return ok(
        request,
        {
            "user": UserOut.model_validate(user),
            "access_token": access,
            "refresh_token": refresh,
        },
    )


@router.post("/login", response_model=AuthOut)
async def login(request: Request, body: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail=err(request, "invalid_credentials", "Invalid email or password"))

    access, refresh = await issue_tokens(db, user, body.device_id)
    await db.commit()

    log.info(
        "auth_login",
        request_id=request.state.request_id,
        user_id=str(user.id),
        device_id=body.device_id,
    )

    return ok(
        request,
        {
            "user": UserOut.model_validate(user),
            "access_token": access,
            "refresh_token": refresh,
        },
    )


@router.post("/refresh", response_model=AuthOut)
async def refresh(request: Request, body: RefreshIn, db: AsyncSession = Depends(get_db)):
    try:
        user, access, refresh_token = await refresh_tokens(db, body.refresh_token, body.device_id)
    except RefreshError as e:
        raise HTTPException(status_code=401, detail=err(request, e.code, "Invalid refresh token"))
    await db.commit()

    log.info(
        "auth_refresh",
        request_id=request.state.request_id,
        user_id=str(user.id),
        device_id=body.device_id,
    )

    return ok(
        request,
        {
            "user": UserOut.model_validate(user),
            "access_token": access,
            "refresh_token": refresh_token,
        },
    )


@router.post("/forgot", dependencies=[forgot_rate_limit])
async def forgot(request: Request, body: ForgotIn):
    return ok(request, {"status": "ok"})


@router.post("/reset")
async def reset(request: Request, body: ResetIn):
    return ok(request, {"status": "ok"})


@router.post("/logout")
async def logout(
    request: Request,
    body: LogoutIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await revoke_device_tokens(db, current_user, body.device_id)
    await db.commit()
    log.info(
        "auth_logout",
        request_id=request.state.request_id,
        user_id=str(current_user.id),
        device_id=body.device_id,
    )
    return ok(request, {"status": "ok"})
