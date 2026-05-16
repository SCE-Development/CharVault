import logging

import httpx
from fastapi import Header, HTTPException, status

from modules.constants import (
    CLARK_API_URL,
    MEMBERSHIP_ADMIN,
    MEMBERSHIP_MEMBER,
    MEMBERSHIP_NON_MEMBER,
    MEMBERSHIP_OFFICER,
)


logger = logging.getLogger(__name__)


def _role_for_access_level(access_level: int) -> str:
    if access_level >= MEMBERSHIP_ADMIN:
        return "admin"
    if access_level >= MEMBERSHIP_OFFICER:
        return "officer"
    if access_level >= MEMBERSHIP_MEMBER:
        return "member"
    return "non_member"


def verify_auth_header(authorization: str) -> dict:
    try:
        resp = httpx.post(
            f"{CLARK_API_URL}/api/Auth/verify",
            headers={"Authorization": authorization},
            timeout=5.0,
        )
    except httpx.HTTPError:
        logger.exception("Clark verify request failed")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token verification failed")

    if resp.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token verification failed")

    try:
        user = resp.json()
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Clark response")

    access_level = user.get("accessLevel")
    if not isinstance(access_level, (int, float)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user data from Clark")
    access_level = int(access_level)

    return {
        "user_id": user.get("_id"),
        "email": user.get("email"),
        "access_level": access_level,
        "role": _role_for_access_level(access_level),
    }


def require_auth(min_level: int = MEMBERSHIP_MEMBER):
    def dependency(authorization: str = Header(default=None)) -> dict:
        if not authorization:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No authorization header")
        user = verify_auth_header(authorization)
        if user["access_level"] < min_level:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient privileges")
        return user

    return dependency
