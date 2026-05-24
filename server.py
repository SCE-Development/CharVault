import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from modules import google_services
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
    get_admin_time_slots,
    get_all_bookings,
    get_alternate_interviewers,
    get_available_time_slots,
    get_booking,
    insert_booking_for_time,
    insert_time_slots,
    maybe_create_tables,
    reassign_booking,
    reschedule_booking,
    set_booking_calendar_event_id,
)
from modules.tokens import sign_booking_token, verify_booking_token

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    maybe_create_tables(SQLITE_FILE)
    yield


app = FastAPI(root_path=ROOT_PATH, lifespan=lifespan)


class TimeWindow(BaseModel):
    start_time: str
    end_time: str


class AddTimeSlotsBody(BaseModel):
    interviewer_name: str = Field(min_length=1, max_length=128)
    interviewer_email: str = Field(min_length=3, max_length=255)
    interviewer_discord_username: str = Field(min_length=1, max_length=64)
    slots: list[TimeWindow] = Field(min_length=1)


class RemoveTimeSlotsBody(BaseModel):
    slot_ids: list[int] = Field(min_length=1)


class CreateBookingBody(BaseModel):
    start_time: str
    end_time: str
    name: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=255)
    discord_username: str = Field(min_length=1, max_length=64)
    acknowledged_git_workshop: bool


class RescheduleBookingBody(BaseModel):
    new_start_time: str
    new_end_time: str
    token: str | None = None


class CancelBookingBody(BaseModel):
    token: str | None = None


class ReassignBookingBody(BaseModel):
    new_interviewer_email: str = Field(min_length=3, max_length=255)


def _authorize_manage(booking_id: int, token: str | None, x_admin_key: str | None):
    if token and verify_booking_token(booking_id, token):
        return
    if is_admin_key(x_admin_key):
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to modify this booking")


def _public_booking_view(booking: dict) -> dict:
    return {
        k: v for k, v in booking.items()
        if k not in ("interviewer_name", "interviewer_email")
    }


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


@app.get("/api/admin/timeslots", dependencies=[Depends(require_admin_key)])
def admin_list_timeslots(interviewer_email: str | None = None):
    return {"slots": get_admin_time_slots(SQLITE_FILE, interviewer_email)}


@app.post("/api/timeslots/add", dependencies=[Depends(require_admin_key)])
def add_timeslots(body: AddTimeSlotsBody):
    pairs = [(s.start_time, s.end_time) for s in body.slots]
    inserted = insert_time_slots(
        SQLITE_FILE,
        body.interviewer_name,
        body.interviewer_email,
        body.interviewer_discord_username,
        pairs,
    )
    return {"inserted": inserted}


@app.post("/api/timeslots/remove", dependencies=[Depends(require_admin_key)])
def remove_timeslots(body: RemoveTimeSlotsBody):
    deleted = delete_time_slots(SQLITE_FILE, body.slot_ids)
    return {"deleted": deleted}


@app.post("/api/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(body: CreateBookingBody):
    if not body.acknowledged_git_workshop:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You must complete the git proficiency check before booking",
        )
    booking_id = insert_booking_for_time(
        SQLITE_FILE,
        body.start_time,
        body.end_time,
        body.name,
        body.email,
        body.discord_username,
        body.acknowledged_git_workshop,
    )
    if booking_id is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Time slot unavailable or already booked"
        )
    booking = get_booking(SQLITE_FILE, booking_id)
    manage_token = sign_booking_token(booking_id)

    if google_services.is_enabled():
        try:
            event_id = google_services.create_calendar_event(
                start_time=booking["start_time"],
                end_time=booking["end_time"],
                attendee_name=booking["name"],
                attendee_email=booking["email"],
                attendee_discord=booking["discord_username"],
                interviewer_name=booking["interviewer_name"],
                interviewer_email=booking["interviewer_email"],
                interviewer_discord=booking["interviewer_discord_username"],
                manage_link=google_services.build_manage_link(booking_id, manage_token),
            )
        except Exception:
            logger.exception("Calendar event create failed; rolling back booking %s", booking_id)
            delete_booking(SQLITE_FILE, booking_id)
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                "Failed to create calendar event; please try again",
            )
        set_booking_calendar_event_id(SQLITE_FILE, booking_id, event_id)
        try:
            google_services.send_confirmation_email(
                to=booking["email"],
                booking_id=booking_id,
                token=manage_token,
                start_time=booking["start_time"],
                interviewer_name=booking["interviewer_name"],
            )
        except Exception:
            logger.exception("Confirmation email failed for booking %s", booking_id)

    return {
        "booking": _public_booking_view(booking),
        "manage_token": manage_token,
    }


@app.get("/api/admin/bookings", dependencies=[Depends(require_admin_key)])
def admin_list_bookings():
    return {"bookings": get_all_bookings(SQLITE_FILE)}


@app.get(
    "/api/admin/bookings/{booking_id}/alternates",
    dependencies=[Depends(require_admin_key)],
)
def admin_booking_alternates(booking_id: int):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    return {"alternates": get_alternate_interviewers(SQLITE_FILE, booking_id)}


@app.post(
    "/api/admin/bookings/{booking_id}/reassign",
    dependencies=[Depends(require_admin_key)],
)
def admin_reassign_booking(booking_id: int, body: ReassignBookingBody):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if not reassign_booking(SQLITE_FILE, booking_id, body.new_interviewer_email):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{body.new_interviewer_email} is not available at this time",
        )
    updated = get_booking(SQLITE_FILE, booking_id)

    if google_services.is_enabled() and booking["calendar_event_id"]:
        try:
            google_services.update_calendar_event_interviewer(
                booking["calendar_event_id"],
                attendee_name=updated["name"],
                attendee_email=updated["email"],
                attendee_discord=updated["discord_username"],
                new_interviewer_name=updated["interviewer_name"],
                new_interviewer_email=updated["interviewer_email"],
                new_interviewer_discord=updated["interviewer_discord_username"],
                manage_link=google_services.build_manage_link(
                    booking_id, sign_booking_token(booking_id)
                ),
            )
        except Exception:
            logger.exception(
                "Calendar interviewer update failed for booking %s", booking_id
            )

    return {"booking": updated}


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
    if is_admin_key(x_admin_key):
        return {"booking": booking}
    return {"booking": _public_booking_view(booking)}


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

    if google_services.is_enabled():
        if booking["calendar_event_id"]:
            try:
                google_services.delete_calendar_event(booking["calendar_event_id"])
            except Exception:
                logger.exception(
                    "Calendar event delete failed for booking %s", booking_id
                )
        try:
            google_services.send_cancellation_email(
                to=booking["email"], start_time=booking["start_time"]
            )
        except Exception:
            logger.exception("Cancellation email failed for booking %s", booking_id)

    return {"cancelled": True, "booking": _public_booking_view(booking)}


@app.post("/api/bookings/{booking_id}/reschedule")
def reschedule_booking_route(
    booking_id: int,
    body: RescheduleBookingBody,
    x_admin_key: str | None = Header(default=None),
):
    booking = get_booking(SQLITE_FILE, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    _authorize_manage(booking_id, body.token, x_admin_key)
    if not reschedule_booking(SQLITE_FILE, booking_id, body.new_start_time, body.new_end_time):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "New time slot unavailable or already booked"
        )
    updated = get_booking(SQLITE_FILE, booking_id)

    if google_services.is_enabled():
        if booking["calendar_event_id"]:
            try:
                google_services.update_calendar_event_time(
                    booking["calendar_event_id"],
                    body.new_start_time,
                    body.new_end_time,
                )
            except Exception:
                logger.exception(
                    "Calendar event time update failed for booking %s", booking_id
                )
        token_for_email = body.token or sign_booking_token(booking_id)
        try:
            google_services.send_reschedule_email(
                to=updated["email"],
                booking_id=booking_id,
                token=token_for_email,
                new_start_time=updated["start_time"],
                interviewer_name=updated["interviewer_name"],
            )
        except Exception:
            logger.exception("Reschedule email failed for booking %s", booking_id)

    return {"booking": _public_booking_view(updated)}


_STATIC_DIR = Path(__file__).parent / "static"


@app.get("/admin")
def admin_page():
    return FileResponse(_STATIC_DIR / "admin.html")


@app.get("/manage")
def manage_page():
    return FileResponse(_STATIC_DIR / "manage.html")


app.mount(
    "/",
    StaticFiles(directory=_STATIC_DIR, html=True),
    name="static",
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9191, reload=True)
