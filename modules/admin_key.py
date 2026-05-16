import hmac

from fastapi import Header, HTTPException, status

from modules.constants import ADMIN_API_KEY


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    if not x_admin_key or not hmac.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid or missing admin key")


def is_admin_key(x_admin_key: str | None) -> bool:
    return bool(x_admin_key) and hmac.compare_digest(x_admin_key, ADMIN_API_KEY)
