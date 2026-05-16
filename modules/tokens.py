import hashlib
import hmac

from modules.constants import HMAC_SECRET


def sign_booking_token(booking_id: int) -> str:
    msg = str(booking_id).encode()
    return hmac.new(HMAC_SECRET.encode(), msg, hashlib.sha256).hexdigest()


def verify_booking_token(booking_id: int, token: str) -> bool:
    expected = sign_booking_token(booking_id)
    return hmac.compare_digest(expected, token)
