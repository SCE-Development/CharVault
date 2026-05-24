import os

SQLITE_FILE = os.environ.get("SQLITE_FILE", "charlendar.db")
ROOT_PATH = os.environ.get("ROOT_PATH", "")
HMAC_SECRET = os.environ.get("HMAC_SECRET", "dev-secret-change-me")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "dev-admin-key-change-me")

EVENT_NAME = "SCE Internship Interview"
BOOKING_DURATION_MINUTES = int(os.environ.get("BOOKING_DURATION_MINUTES", "60"))

GOOGLE_TOKEN_FILE = os.environ.get("GOOGLE_TOKEN_FILE", "")
GOOGLE_SENDER_EMAIL = os.environ.get("GOOGLE_SENDER_EMAIL", "")
GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:9191")
