import logging
import sqlite3
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


def maybe_create_tables(sqlite_file: str) -> bool:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                interviewer_name TEXT NOT NULL,
                UNIQUE (start_time, end_time, interviewer_name)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_slot_id INTEGER NOT NULL UNIQUE,
                email TEXT NOT NULL,
                discord_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                calendar_event_id TEXT,
                FOREIGN KEY (time_slot_id) REFERENCES time_slots(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_slots_start ON time_slots(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_slots_interviewer ON time_slots(interviewer_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_email ON bookings(email)")
        db.commit()
        return True
    except Exception:
        logger.exception("Unable to create tables")
        return False
    finally:
        cursor.close()
        db.close()


def insert_time_slots(
    sqlite_file: str,
    interviewer_name: str,
    slots: list[tuple[str, str]],
) -> int:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    inserted = 0
    try:
        for start, end in slots:
            try:
                cursor.execute(
                    "INSERT INTO time_slots (start_time, end_time, interviewer_name) VALUES (?, ?, ?)",
                    (start, end, interviewer_name),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                continue
        db.commit()
        return inserted
    except Exception:
        logger.exception("Inserting time slots failed")
        db.rollback()
        return inserted
    finally:
        cursor.close()
        db.close()


def delete_time_slots(sqlite_file: str, slot_ids: list[int]) -> int:
    if not slot_ids:
        return 0
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        placeholders = ",".join("?" for _ in slot_ids)
        cursor.execute(f"DELETE FROM time_slots WHERE id IN ({placeholders})", slot_ids)
        db.commit()
        return cursor.rowcount
    except Exception:
        logger.exception("Deleting time slots failed")
        return 0
    finally:
        cursor.close()
        db.close()


def get_available_time_slots(sqlite_file: str) -> list[dict]:
    """Return distinct (start_time, end_time) windows that have at least one unbooked slot."""
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor.execute(
            """
            SELECT DISTINCT ts.start_time, ts.end_time
            FROM time_slots ts
            LEFT JOIN bookings b ON b.time_slot_id = ts.id
            WHERE b.id IS NULL AND ts.start_time > ?
            ORDER BY ts.start_time ASC
            """,
            (now,),
        )
        return [
            {"start_time": row[0], "end_time": row[1]}
            for row in cursor.fetchall()
        ]
    except Exception:
        logger.exception("Fetching available time slots failed")
        return []
    finally:
        cursor.close()
        db.close()


def get_admin_time_slots(sqlite_file: str, interviewer_name: str | None = None) -> list[dict]:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        if interviewer_name is not None:
            cursor.execute(
                """
                SELECT id, start_time, end_time, interviewer_name
                FROM time_slots
                WHERE interviewer_name = ?
                ORDER BY start_time ASC
                """,
                (interviewer_name,),
            )
        else:
            cursor.execute(
                """
                SELECT id, start_time, end_time, interviewer_name
                FROM time_slots
                ORDER BY start_time ASC
                """
            )
        return [
            {
                "id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "interviewer_name": row[3],
            }
            for row in cursor.fetchall()
        ]
    except Exception:
        logger.exception("Fetching admin time slots failed")
        return []
    finally:
        cursor.close()
        db.close()


def insert_booking_for_time(
    sqlite_file: str,
    start_time: str,
    end_time: str,
    email: str,
    discord_username: str,
) -> int | None:
    """Atomically book any unbooked slot at the given time window. Returns booking id or None."""
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        created_at = datetime.now(tz=timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT INTO bookings (time_slot_id, email, discord_username, created_at)
            SELECT ts.id, ?, ?, ?
            FROM time_slots ts
            LEFT JOIN bookings b ON b.time_slot_id = ts.id
            WHERE ts.start_time = ? AND ts.end_time = ? AND b.id IS NULL
            ORDER BY ts.id
            LIMIT 1
            """,
            (email, discord_username, created_at, start_time, end_time),
        )
        if cursor.rowcount == 0:
            return None
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    except Exception:
        logger.exception("Inserting booking failed")
        return None
    finally:
        cursor.close()
        db.close()


def get_booking(sqlite_file: str, booking_id: int) -> dict | None:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            SELECT b.id, b.time_slot_id, b.email, b.discord_username, b.created_at,
                   ts.start_time, ts.end_time, ts.interviewer_name
            FROM bookings b
            JOIN time_slots ts ON ts.id = b.time_slot_id
            WHERE b.id = ?
            """,
            (booking_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "time_slot_id": row[1],
            "email": row[2],
            "discord_username": row[3],
            "created_at": row[4],
            "start_time": row[5],
            "end_time": row[6],
            "interviewer_name": row[7],
        }
    except Exception:
        logger.exception("Fetching booking failed")
        return None
    finally:
        cursor.close()
        db.close()


def get_all_bookings(sqlite_file: str) -> list[dict]:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT b.id, b.time_slot_id, b.email, b.discord_username, b.created_at,
                   ts.start_time, ts.end_time, ts.interviewer_name
            FROM bookings b
            JOIN time_slots ts ON ts.id = b.time_slot_id
            ORDER BY ts.start_time ASC
        """)
        return [
            {
                "id": row[0],
                "time_slot_id": row[1],
                "email": row[2],
                "discord_username": row[3],
                "created_at": row[4],
                "start_time": row[5],
                "end_time": row[6],
                "interviewer_name": row[7],
            }
            for row in cursor.fetchall()
        ]
    except Exception:
        logger.exception("Fetching all bookings failed")
        return []
    finally:
        cursor.close()
        db.close()


def delete_booking(sqlite_file: str, booking_id: int) -> bool:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        db.commit()
        return cursor.rowcount > 0
    except Exception:
        logger.exception("Deleting booking failed")
        return False
    finally:
        cursor.close()
        db.close()


def get_alternate_interviewers(sqlite_file: str, booking_id: int) -> list[str]:
    """Names of interviewers with unbooked slots at this booking's time window."""
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT ts.interviewer_name
            FROM time_slots ts
            LEFT JOIN bookings b ON b.time_slot_id = ts.id AND b.id != ?
            JOIN bookings target ON target.id = ?
            JOIN time_slots target_ts ON target_ts.id = target.time_slot_id
            WHERE ts.start_time = target_ts.start_time
              AND ts.end_time = target_ts.end_time
              AND b.id IS NULL
              AND ts.id != target.time_slot_id
            ORDER BY ts.interviewer_name
            """,
            (booking_id, booking_id),
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        logger.exception("Fetching alternate interviewers failed")
        return []
    finally:
        cursor.close()
        db.close()


def reassign_booking(
    sqlite_file: str,
    booking_id: int,
    new_interviewer_name: str,
) -> bool:
    """Move a booking to the given interviewer's unbooked slot at the same time."""
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            SELECT ts.start_time, ts.end_time
            FROM bookings b JOIN time_slots ts ON ts.id = b.time_slot_id
            WHERE b.id = ?
            """,
            (booking_id,),
        )
        row = cursor.fetchone()
        if not row:
            return False
        start_time, end_time = row

        cursor.execute(
            """
            SELECT ts.id FROM time_slots ts
            LEFT JOIN bookings b ON b.time_slot_id = ts.id AND b.id != ?
            WHERE ts.start_time = ? AND ts.end_time = ?
              AND ts.interviewer_name = ?
              AND b.id IS NULL
            LIMIT 1
            """,
            (booking_id, start_time, end_time, new_interviewer_name),
        )
        new_slot = cursor.fetchone()
        if not new_slot:
            return False

        cursor.execute(
            "UPDATE bookings SET time_slot_id = ? WHERE id = ?",
            (new_slot[0], booking_id),
        )
        db.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    except Exception:
        logger.exception("Reassigning booking failed")
        return False
    finally:
        cursor.close()
        db.close()


def reschedule_booking(
    sqlite_file: str,
    booking_id: int,
    new_start_time: str,
    new_end_time: str,
) -> bool:
    """Atomically move a booking to any unbooked slot at the new time window."""
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            UPDATE bookings
            SET time_slot_id = (
                SELECT ts.id FROM time_slots ts
                LEFT JOIN bookings b ON b.time_slot_id = ts.id AND b.id != ?
                WHERE ts.start_time = ? AND ts.end_time = ? AND b.id IS NULL
                ORDER BY ts.id
                LIMIT 1
            )
            WHERE id = ? AND EXISTS (
                SELECT 1 FROM time_slots ts
                LEFT JOIN bookings b ON b.time_slot_id = ts.id AND b.id != ?
                WHERE ts.start_time = ? AND ts.end_time = ? AND b.id IS NULL
            )
            """,
            (
                booking_id, new_start_time, new_end_time,
                booking_id,
                booking_id, new_start_time, new_end_time,
            ),
        )
        db.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    except Exception:
        logger.exception("Rescheduling booking failed")
        return False
    finally:
        cursor.close()
        db.close()
