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
                UNIQUE (start_time, end_time)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_slot_id INTEGER NOT NULL UNIQUE,
                email TEXT NOT NULL,
                discord_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (time_slot_id) REFERENCES time_slots(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_slots_start ON time_slots(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookings_email ON bookings(email)")
        db.commit()
        return True
    except Exception:
        logger.exception("Unable to create tables")
        return False
    finally:
        cursor.close()
        db.close()


def insert_time_slots(sqlite_file: str, slots: list[tuple[str, str]]) -> int:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    inserted = 0
    try:
        for start, end in slots:
            try:
                cursor.execute(
                    "INSERT INTO time_slots (start_time, end_time) VALUES (?, ?)",
                    (start, end),
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
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor.execute(
            """
            SELECT ts.id, ts.start_time, ts.end_time
            FROM time_slots ts
            LEFT JOIN bookings b ON b.time_slot_id = ts.id
            WHERE b.id IS NULL AND ts.start_time > ?
            ORDER BY ts.start_time ASC
            """,
            (now,),
        )
        return [
            {"id": row[0], "start_time": row[1], "end_time": row[2]}
            for row in cursor.fetchall()
        ]
    except Exception:
        logger.exception("Fetching available time slots failed")
        return []
    finally:
        cursor.close()
        db.close()


def insert_booking(
    sqlite_file: str,
    time_slot_id: int,
    email: str,
    discord_username: str,
) -> int | None:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO bookings (time_slot_id, email, discord_username, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                time_slot_id,
                email,
                discord_username,
                datetime.now(tz=timezone.utc).isoformat(),
            ),
        )
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
                   ts.start_time, ts.end_time
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
                   ts.start_time, ts.end_time
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


def update_booking_slot(sqlite_file: str, booking_id: int, new_slot_id: int) -> bool:
    db = sqlite3.connect(sqlite_file)
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE bookings SET time_slot_id = ? WHERE id = ?",
            (new_slot_id, booking_id),
        )
        db.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    except Exception:
        logger.exception("Updating booking slot failed")
        return False
    finally:
        cursor.close()
        db.close()
