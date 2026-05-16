from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from modules.auth import require_auth, verify_auth_header
from modules.constants import (
    BOOKING_DURATION_MINUTES,
    CLARK_LOGIN_URL,
    EVENT_NAME,
    MEMBERSHIP_ADMIN,
    MEMBERSHIP_MEMBER,
    ROOT_PATH,
    SQLITE_FILE,
)
from modules.sqlite_helpers import (
    delete_booking,
    delete_time_slots,
    get_all_bookings,
    get_available_time_slots,
    get_booking,
    insert_booking,
    insert_time_slots,
    maybe_create_tables,
    update_booking_slot,
)
from modules.tokens import sign_booking_token, verify_booking_token


@asynccontextmanager
async def lifespan(_: FastAPI):
    maybe_create_tables(SQLITE_FILE)
    yield


app = FastAPI(root_path=ROOT_PATH, lifespan=lifespan)


class TimeSlotIn(BaseModel):
    start_time: str
    end_time: str


class AddTimeSlotsBody(BaseModel):
    slots: list[TimeSlotIn] = Field(min_length=1)


class RemoveTimeSlotsBody(BaseModel):
    slot_ids: list[int] = Field(min_length=1)


class CreateBookingBody(BaseModel):
    time_slot_id: int
    email: str = Field(min_length=3, max_length=255)
    discord_username: str = Field(min_length=1, max_length=64)


class RescheduleBookingBody(BaseModel):
    new_time_slot_id: int
    token: str | None = None


class CancelBookingBody(BaseModel):
    token: str | None = None


def _authorize_manage(booking_id: int, token: str | None, authorization: str | None):
    if token and verify_booking_token(booking_id, token):
        return
    if authorization:
        user = verify_auth_header(authorization)
        if user["access_level"] >= MEMBERSHIP_ADMIN:
            return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to modify this booking")


@app.get("/api/health")
def health():
    return {"status": "ok", "event": EVENT_NAME}


@app.get("/api/config")
def config():
    return {
        "event_name": EVENT_NAME,
        "booking_duration_minutes": BOOKING_DURATION_MINUTES,
        "clark_login_url": CLARK_LOGIN_URL,
    }


@app.get("/api/timeslots")
def list_timeslots(_user: dict = Depends(require_auth(MEMBERSHIP_MEMBER))):
    return {"slots": get_available_time_slots(SQLITE_FILE)}


@app.post("/api/timeslots/add")
def add_timeslots(
    body: AddTimeSlotsBody,
    _admin: dict = Depends(require_auth(MEMBERSHIP_ADMIN)),
):
    pairs = [(s.start_time, s.end_time) for s in body.slots]
    inserted = insert_time_slots(SQLITE_FILE, pairs)
    return {"inserted": inserted}


@app.post("/api/timeslots/remove")
def remove_timeslots(
    body: RemoveTimeSlotsBody,
    _admin: dict = Depends(require_auth(MEMBERSHIP_ADMIN)),
):
    deleted = delete_time_slots(SQLITE_FILE, body.slot_ids)
    return {"deleted": deleted}


@app.post("/api/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(
    body: CreateBookingBody,
    _user: dict = Depends(require_auth(MEMBERSHIP_MEMBER)),
):
    booking_id = insert_booking(
        SQLITE_FILE, body.time_slot_id, body.email, body.discord_username
    )
    if booking_id is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Time slot unavailable or already booked"
        )
    return {
        "booking": get_booking(SQLITE_FILE, booking_id),
        "manage_token": sign_booking_token(booking_id),
    }


@app.get("/api/admin/bookings")
def admin_list_bookings(_admin: dict = Depends(require_auth(MEMBERSHIP_ADMIN))):
    return {"bookings": get_all_bookings(SQLITE_FILE)}


@app.get("/api/bookings/{booking_id}")
def fetch_booking(
    booking_id: int,
    token: str | None = None,
    authorization: str | None = Header(default=None),
):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    _authorize_manage(booking_id, token, authorization)
    return {"booking": booking}


@app.post("/api/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    body: CancelBookingBody,
    authorization: str | None = Header(default=None),
):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    _authorize_manage(booking_id, body.token, authorization)
    if not delete_booking(SQLITE_FILE, booking_id):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to cancel booking")
    return {"cancelled": True, "booking": booking}


@app.post("/api/bookings/{booking_id}/reschedule")
def reschedule_booking(
    booking_id: int,
    body: RescheduleBookingBody,
    authorization: str | None = Header(default=None),
):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    _authorize_manage(booking_id, body.token, authorization)
    if not update_booking_slot(SQLITE_FILE, booking_id, body.new_time_slot_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "New time slot unavailable or already booked"
        )
    return {"booking": get_booking(SQLITE_FILE, booking_id)}


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="static",
)
