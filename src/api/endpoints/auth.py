import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthStatus(BaseModel):
    authenticated: bool
    message: str


def get_api_key_secret() -> str:
    """Get the API key secret from environment."""
    return os.getenv("API_KEY_SECRET", "")


async def validate_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Dependency to validate API key from X-API-Key header.
    Use this as a dependency on protected endpoints.
    """
    expected_key = get_api_key_secret()

    if not expected_key:
        # If no API key is configured, allow all requests (development mode)
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key


@router.post("/validate", response_model=AuthStatus)
async def validate_key(api_key: str = Depends(validate_api_key)):
    """Validate an API key and return authentication status."""
    return AuthStatus(
        authenticated=True,
        message="API key is valid.",
    )
