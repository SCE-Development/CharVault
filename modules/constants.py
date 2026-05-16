import os

SQLITE_FILE = os.environ.get("SQLITE_FILE", "charlendar.db")
CLARK_API_URL = os.environ.get("CLARK_API_URL", "http://localhost:8080")
ROOT_PATH = os.environ.get("ROOT_PATH", "/bookings")
HMAC_SECRET = os.environ.get("HMAC_SECRET", "dev-secret-change-me")

EVENT_NAME = "SCE Internship Interview"
BOOKING_DURATION_MINUTES = int(os.environ.get("BOOKING_DURATION_MINUTES", "60"))

MEMBERSHIP_BANNED = -2
MEMBERSHIP_PENDING = -1
MEMBERSHIP_NON_MEMBER = 0
MEMBERSHIP_MEMBER = 1
MEMBERSHIP_OFFICER = 2
MEMBERSHIP_ADMIN = 3
