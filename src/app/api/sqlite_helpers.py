import sqlite3

# TABLES OR SQLITE FUNCTIONS TO ADD
# creating table for stored events
# table to store users
# adding, deleting, and rescheduling event
# display events that will occur in the next two weeks
# display events on calendar?

# NOT DONE SORRY - char
def create_event_table(sqlite_file : str) -> bool:
    with sqlite3.connect(sqlite_file) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS events
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        time_period INTEGER DEFAULT 1
                    )
                """
            )
        except Exception:
            print("yo what am i doing")
            return False
    return True