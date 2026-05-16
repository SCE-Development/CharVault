import os

SQLITE_FILE = os.environ.get("SQLITE_FILE", "charlendar.db")
ROOT_PATH = os.environ.get("ROOT_PATH", "/bookings")
HMAC_SECRET = os.environ.get("HMAC_SECRET", "dev-secret-change-me")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "dev-admin-key-change-me")

EVENT_NAME = "SCE Internship Interview"
BOOKING_DURATION_MINUTES = int(os.environ.get("BOOKING_DURATION_MINUTES", "60"))
