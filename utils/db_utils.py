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


def create_connection(db_file: str):
    """
    Takes the location of the db file and creates a connection to the database
    Args:
        db_file (str): The name and path to the database file
    Outputs:
        returns an object `conn` that represents the connection the database
    """
    conn = None
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            print(f'Connected to the Database {db_file}')
            return conn
        except sqlite3.Error as e:
            print(f'Could not connect to database because {e}')
        return conn
    else:
        print("Error! database file does not exist")
        return conn


def insert_user(conn, discord_id: str, discord_name: str,
                date_registered: str) -> None:
    """
    Takes the arguments to create a new record in the User Table
    discord_id and date_registered are NOT NULL in the database and must be provided

    Args:
        conn: Connection object returned by the `create_connection` function
        discord_id (str): The discord user id of the user
        discord_name (str): The name of the user
        date_registered(str): The date and time when the user hits the register button
    """

    if conn is not None:
        try:
            c = conn.cursor()
            insert_user_query = """ INSERT INTO user(discord_id, discord_name,
            date_registered) VALUES(?,?,?)"""
            c.execute(insert_user_query, (discord_id, discord_name,
                                          date_registered))
            print(f"User {discord_id} has been inserted into the datasbase.")
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                print(f"{discord_id} already exists in the database.")
            else:
                print(e)
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
        conn.commit()
    else:
        # this check should be redundunt
        print("Error! Cannot create database connection")
