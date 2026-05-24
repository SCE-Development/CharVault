import base64
import html
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from modules.constants import (
    EVENT_NAME,
    GOOGLE_CALENDAR_ID,
    GOOGLE_SENDER_EMAIL,
    GOOGLE_TOKEN_FILE,
    PUBLIC_BASE_URL,
)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]


def is_enabled() -> bool:
    return bool(GOOGLE_TOKEN_FILE) and os.path.exists(GOOGLE_TOKEN_FILE)


def _load_creds() -> Credentials:
    creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(GOOGLE_TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("Google credentials are not valid and cannot be refreshed")
    return creds


def _calendar():
    return build("calendar", "v3", credentials=_load_creds(), cache_discovery=False)


def _gmail():
    return build("gmail", "v1", credentials=_load_creds(), cache_discovery=False)


def _event_summary(interviewer_name: str) -> str:
    return f"{EVENT_NAME} with {interviewer_name}"


def _event_description(
    *,
    attendee_name: str,
    attendee_discord: str,
    interviewer_name: str,
    interviewer_email: str,
    interviewer_discord: str,
    manage_link: str,
) -> str:
    return (
        f"Interviewee: {html.escape(attendee_name)} "
        f"(Discord: {html.escape(attendee_discord)})<br>"
        f"Interviewer: {html.escape(interviewer_name)} "
        f"&lt;{html.escape(interviewer_email)}&gt; "
        f"(Discord: {html.escape(interviewer_discord)})<br><br>"
        f"Need to cancel or reschedule? "
        f"<a href=\"{html.escape(manage_link, quote=True)}\">Manage your booking</a>"
    )


def create_calendar_event(
    *,
    start_time: str,
    end_time: str,
    attendee_name: str,
    attendee_email: str,
    attendee_discord: str,
    interviewer_name: str,
    interviewer_email: str,
    interviewer_discord: str,
    manage_link: str,
) -> str:
    event = {
        "summary": _event_summary(interviewer_name),
        "description": _event_description(
            attendee_name=attendee_name,
            attendee_discord=attendee_discord,
            interviewer_name=interviewer_name,
            interviewer_email=interviewer_email,
            interviewer_discord=interviewer_discord,
            manage_link=manage_link,
        ),
        "start": {"dateTime": start_time, "timeZone": "UTC"},
        "end": {"dateTime": end_time, "timeZone": "UTC"},
        "attendees": [
            {"email": attendee_email},
            {"email": interviewer_email},
        ],
        "reminders": {"useDefault": True},
    }
    created = _calendar().events().insert(
        calendarId=GOOGLE_CALENDAR_ID, body=event, sendUpdates="all"
    ).execute()
    return created["id"]


def update_calendar_event_time(event_id: str, new_start: str, new_end: str) -> None:
    body = {
        "start": {"dateTime": new_start, "timeZone": "UTC"},
        "end": {"dateTime": new_end, "timeZone": "UTC"},
    }
    _calendar().events().patch(
        calendarId=GOOGLE_CALENDAR_ID, eventId=event_id, body=body, sendUpdates="all"
    ).execute()


def update_calendar_event_interviewer(
    event_id: str,
    *,
    attendee_name: str,
    attendee_email: str,
    attendee_discord: str,
    new_interviewer_name: str,
    new_interviewer_email: str,
    new_interviewer_discord: str,
    manage_link: str,
) -> None:
    body = {
        "summary": _event_summary(new_interviewer_name),
        "description": _event_description(
            attendee_name=attendee_name,
            attendee_discord=attendee_discord,
            interviewer_name=new_interviewer_name,
            interviewer_email=new_interviewer_email,
            interviewer_discord=new_interviewer_discord,
            manage_link=manage_link,
        ),
        "attendees": [
            {"email": attendee_email},
            {"email": new_interviewer_email},
        ],
    }
    _calendar().events().patch(
        calendarId=GOOGLE_CALENDAR_ID, eventId=event_id, body=body, sendUpdates="all"
    ).execute()


def delete_calendar_event(event_id: str) -> None:
    try:
        _calendar().events().delete(
            calendarId=GOOGLE_CALENDAR_ID, eventId=event_id, sendUpdates="all"
        ).execute()
    except HttpError as e:
        if e.resp.status in (404, 410):
            return
        raise


def _send_email(*, to: str, subject: str, plain_text: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["From"] = formataddr(("SCE Interviews", GOOGLE_SENDER_EMAIL))
    msg["Subject"] = subject
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    _gmail().users().messages().send(userId="me", body={"raw": raw}).execute()


def build_manage_link(booking_id: int, token: str) -> str:
    return f"{PUBLIC_BASE_URL.rstrip('/')}/manage?id={booking_id}&token={token}"


def send_confirmation_email(
    *, to: str, booking_id: int, token: str, start_time: str, interviewer_name: str
) -> None:
    link = build_manage_link(booking_id, token)
    plain = (
        f"Your {EVENT_NAME} is confirmed.\n\n"
        f"When: {start_time}\n"
        f"Interviewer: {interviewer_name}\n\n"
        f"A Google Calendar invitation has also been sent to this address.\n\n"
        f"To cancel or reschedule:\n{link}\n"
    )
    html_body = (
        f"<p>Your {html.escape(EVENT_NAME)} is confirmed.</p>"
        f"<p><strong>When:</strong> {html.escape(start_time)}<br>"
        f"<strong>Interviewer:</strong> {html.escape(interviewer_name)}</p>"
        f"<p>A Google Calendar invitation has also been sent to this address.</p>"
        f"<p><a href=\"{html.escape(link, quote=True)}\">Cancel or reschedule</a></p>"
    )
    _send_email(
        to=to,
        subject=f"{EVENT_NAME} confirmed",
        plain_text=plain,
        html_body=html_body,
    )


def send_cancellation_email(*, to: str, start_time: str) -> None:
    plain = (
        f"Your {EVENT_NAME} scheduled for {start_time} has been cancelled.\n\n"
        f"If this was a mistake, you can book a new time on the booking page.\n"
    )
    html_body = (
        f"<p>Your {html.escape(EVENT_NAME)} scheduled for "
        f"{html.escape(start_time)} has been cancelled.</p>"
        f"<p>If this was a mistake, you can book a new time on the booking page.</p>"
    )
    _send_email(
        to=to,
        subject=f"{EVENT_NAME} cancelled",
        plain_text=plain,
        html_body=html_body,
    )


def send_reschedule_email(
    *, to: str, booking_id: int, token: str, new_start_time: str, interviewer_name: str
) -> None:
    link = build_manage_link(booking_id, token)
    plain = (
        f"Your {EVENT_NAME} has been rescheduled.\n\n"
        f"New time: {new_start_time}\n"
        f"Interviewer: {interviewer_name}\n\n"
        f"Your calendar invitation has been updated to reflect the new time.\n\n"
        f"To cancel or reschedule again:\n{link}\n"
    )
    html_body = (
        f"<p>Your {html.escape(EVENT_NAME)} has been rescheduled.</p>"
        f"<p><strong>New time:</strong> {html.escape(new_start_time)}<br>"
        f"<strong>Interviewer:</strong> {html.escape(interviewer_name)}</p>"
        f"<p>Your calendar invitation has been updated to reflect the new time.</p>"
        f"<p><a href=\"{html.escape(link, quote=True)}\">Cancel or reschedule again</a></p>"
    )
    _send_email(
        to=to,
        subject=f"{EVENT_NAME} rescheduled",
        plain_text=plain,
        html_body=html_body,
    )
