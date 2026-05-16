from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from modules.admin_key import is_admin_key, require_admin_key
from modules.constants import (
    BOOKING_DURATION_MINUTES,
    EVENT_NAME,
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


def _authorize_manage(booking_id: int, token: str | None, x_admin_key: str | None):
    if token and verify_booking_token(booking_id, token):
        return
    if is_admin_key(x_admin_key):
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
    }


@app.get("/api/timeslots")
def list_timeslots():
    return {"slots": get_available_time_slots(SQLITE_FILE)}


@app.post("/api/timeslots/add", dependencies=[Depends(require_admin_key)])
def add_timeslots(body: AddTimeSlotsBody):
    pairs = [(s.start_time, s.end_time) for s in body.slots]
    inserted = insert_time_slots(SQLITE_FILE, pairs)
    return {"inserted": inserted}


@app.post("/api/timeslots/remove", dependencies=[Depends(require_admin_key)])
def remove_timeslots(body: RemoveTimeSlotsBody):
    deleted = delete_time_slots(SQLITE_FILE, body.slot_ids)
    return {"deleted": deleted}


@app.post("/api/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(body: CreateBookingBody):
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


@app.get("/api/admin/bookings", dependencies=[Depends(require_admin_key)])
def admin_list_bookings():
    return {"bookings": get_all_bookings(SQLITE_FILE)}


@app.get("/api/bookings/{booking_id}")
def fetch_booking(
    booking_id: int,
    token: str | None = None,
    x_admin_key: str | None = Header(default=None),
):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    _authorize_manage(booking_id, token, x_admin_key)
    return {"booking": booking}


@app.post("/api/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    body: CancelBookingBody,
    x_admin_key: str | None = Header(default=None),
):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    _authorize_manage(booking_id, body.token, x_admin_key)
    if not delete_booking(SQLITE_FILE, booking_id):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to cancel booking")
    return {"cancelled": True, "booking": booking}


@app.post("/api/bookings/{booking_id}/reschedule")
def reschedule_booking(
    booking_id: int,
    body: RescheduleBookingBody,
    x_admin_key: str | None = Header(default=None),
):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    _authorize_manage(booking_id, body.token, x_admin_key)
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9191, reload=True)
