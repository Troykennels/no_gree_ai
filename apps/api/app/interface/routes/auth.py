"""Authentication endpoints: register, login, current user."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

import jwt

from app.application.use_cases.auth import AuthenticateUser, RegisterUser
from app.core import security
from app.core.rate_limit import limiter
from app.domain.entities import User
from app.interface.dependencies import (
    get_authenticate_user,
    get_current_user,
    get_register_user,
)
from app.interface.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_user)],
) -> UserResponse:
    user = use_case.execute(
        email=payload.email, full_name=payload.full_name, password=payload.password
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    payload: LoginRequest,
    use_case: Annotated[AuthenticateUser, Depends(get_authenticate_user)],
) -> TokenResponse:
    tokens = use_case.execute(email=payload.email, password=payload.password)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
def refresh(request: Request, payload: RefreshRequest) -> TokenResponse:
    """Exchange a valid refresh token for a fresh access + refresh token pair."""
    try:
        claims = security.decode_token(payload.refresh_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token") from exc
    if claims.get("type") != security.REFRESH_TOKEN or "sub" not in claims:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")
    subject = claims["sub"]
    return TokenResponse(
        access_token=security.create_access_token(subject),
        refresh_token=security.create_refresh_token(subject),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(_: Annotated[User, Depends(get_current_user)]) -> None:
    """Stateless logout: the client discards its tokens. (Full server-side
    revocation needs a jti denylist in Redis — see the scaling notes.)"""
    return None


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(user)
