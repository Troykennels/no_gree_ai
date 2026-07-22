"""Authentication endpoints: register, login, current user."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.application.use_cases.auth import AuthenticateUser, RegisterUser
from app.core.rate_limit import limiter
from app.domain.entities import User
from app.interface.dependencies import (
    get_authenticate_user,
    get_current_user,
    get_register_user,
)
from app.interface.schemas import (
    LoginRequest,
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


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(user)
