import os
import sqlite3




def initialize_db(db_location) -> None:
    """
    Used to initialize database 
    """
    conn = sqlite3.connect(db_location)

    cursor = conn.cursor()

    print("=========Creating database===============")
    create_user_table_query = """ CREATE TABLE IF NOT EXISTS user (
    discord_id TEXT PRIMARY KEY,
    discord_name TEXT,
    date_registered TEXT NOT NULL
    )"""

    create_timesheet_table_query = """ CREATE TABLE IF NOT EXISTS timesheet(
    time_id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT NOT NULL,
    time_in TEXT NOT NULL,
    time_out TEXT,
    total_time REAL,
    FOREIGN KEY (discord_id) REFERENCES user(discord_id)
    )"""

    create_pomodoro_table_query = """ CREATE TABLE IF NOT EXISTS pomodoro(
    pomo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_id INTEGER NOT NULL,
    issue TEXT NOT NULL,
    time_start TEXT NOT NULL, 
    time_finish TEXT,
    time_delta REAL,
    status INTEGER,
    help REAL,
    FOREIGN KEY (timesheet_id) REFERENCES timesheet(time_id)
    )"""

    create_u_help_table_query = """ CREATE TABLE IF NOT EXISTS u_help(
    u_help_id INTEGER PRIMARY KEY AUTO INCREMENT,
    remark TEXT, 
    pomo_id INTEGER,
    FOREIGN KEY(pomo_id) REFERENCES pomodoro(pomo_id)
    )"""

    cursor.execute(create_user_table_query)
    cursor.execute(create_timesheet_table_query)
    cursor.execute(create_pomodoro_table_query)
    cursor.execute(create_u_help_table_query)
    conn.commit()
    conn.close()
