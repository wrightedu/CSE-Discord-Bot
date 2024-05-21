import os
import sqlite3




def initialize_db(db_location) -> None:
    """
    Create a new database file in SQLITE3 with Tables. 
    The tables created are empty when first initialized

    Args: 
        db_location(string): Path to where the database file is stored. 
            Usually project directory
    
    Output: 
        An error if raised
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
    u_help_id INTEGER PRIMARY KEY AUTOINCREMENT,
    remark TEXT, 
    pomo_id INTEGER,
    FOREIGN KEY(pomo_id) REFERENCES pomodoro(pomo_id)
    )"""
    
    try:
        cursor.execute(create_user_table_query)
        cursor.execute(create_timesheet_table_query)
        cursor.execute(create_pomodoro_table_query)
        cursor.execute(create_u_help_table_query)
        conn.commit()
        print("All tables created")
    except Exception as e:
        print(f'Could not create table because {e} occured')
    conn.close()



def insert_user(conn, discord_id: str, discord_name: str, 
                date_registered:str ) -> None:
    pass

def insert_timesheet(conn, time_id: str, discord_id: str, 
                     time_in: str, time_out: str, total_hours: int) -> None:
    pass

def insert_pomodoro(conn, p_id: int, timsheet: str, )