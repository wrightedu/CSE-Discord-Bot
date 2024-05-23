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
    help_count REAL,
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
                date_registered: str) -> str:
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
                return "User already exists"
            else:
                print(e)
                return "Error"
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return "Error"
        conn.commit()
        return None # No error
    else:
        # this check should be redundunt
        print("Error! Cannot create database connection")
        return "Could not connect to database"


def insert_timesheet(conn, discord_id: str, time_in: str, time_out: str = None, total_time: str = None) -> int:
    """
    Takes the arguments to create a new record in the timesheet Table
    discord_id and time_in are NOT NULL in the database and must be provided

    Args:
        conn: Connection object returned by the `create_connection` function
        discord_id (str): The discord user id of the user
        time_in (str): The datetime object converted into String of when the user checks-in
        time_out (str): The datetime object converted into String of when the user checks-out
        time_out (float): The time delta of time in and time out from user checks in and check out

    Output:
        Returns timesheet_id of the last/current inserted record
    """
    if conn is not None:
        try:
            c = conn.cursor()
            insert_timesheet_query = """ INSERT INTO timesheet(discord_id, time_in,
            time_out, total_time) VALUES(?,?,?,?)"""
            c.execute(insert_timesheet_query, (discord_id, time_in,
                                               time_out, total_time))
            print(f"User {discord_id} has been checked in at {time_in}")
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
        conn.commit()
        return c.lastrowid  # returns the id of the new record
    else:
        # this check should be redundunt
        print("Error! Cannot create database connection")


def insert_pomodoro(conn, timesheet_id: int, issue: str, time_start: str, time_finish: str = None,
                    time_delta: float = None, status: int = None, help_count: float = None) -> int:
    """
    Takes the arguments to create a new record in the pomodoro Table
    timesheet_id, issue, and time_start are NOT NULL in the database and must be provided

    Args:
        conn: Connection object returned by the `create_connection` function
        timesheet_id (int): The current timesheet_id of the user who's invoking the pomodoro function for a given day
        issue (str): Description of the issue the user is having as entered by the user.
        time_start (str): The datetime object converted into String of when the user starts pomodoro
        time_finish (str): The datetime object converted into String of when the user stops pomo
        time_delta (float): The time delta of time start and time finish from when user starts the pomodoro and stops it
        status (int): 1 or 0 as flag for completion of the pomodoro
        help_count (float): number of times the user has requested help/hit the help button

    Output:
        Returns pomo_id of the last/current inserted record
    """
    if conn is not None:
        try:
            c = conn.cursor()
            insert_pomodoro_query = """ INSERT INTO pomodoro(timesheet_id, issue,
            time_start, time_finish, time_delta, status, help_count) VALUES(?,?,?,?,?,?,?)"""
            c.execute(insert_pomodoro_query, (timesheet_id, issue, time_start, time_finish,
                                              time_delta, status, help_count))
            print(
                f"New pomodoro for Timesheet id {timesheet_id} recorded on {time_start}")
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
        conn.commit()
        return c.lastrowid  # returns the id of the new record
    else:
        # this check should be redundunt
        print("Error! Cannot create database connection")


def insert_user_help(conn, remark: str, pomo_id: int) -> int:
    """
    Takes the arguments to create a new record in the u_help Table

    Args:
        conn: Connection object returned by the `create_connection` function
        remark (str): Remarks for help as entered by the user
        pomo_id (str): References to the of when the user 
    Output:
        Returns pomo_id of the last/current inserted record
    """
    if conn is not None:
        try:
            c = conn.cursor()
            insert_user_help_query = """ INSERT INTO u_help(remark, pomo_id) VALUES(?,?)"""
            c.execute(insert_user_help_query, (remark, pomo_id))
            print(
                f"New help record for Pomo id {pomo_id} recorded.")
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
        conn.commit()
        return c.lastrowid  # returns the id of the new record
    else:
        # this check should be redundunt
        print("Error! Cannot create database connection")
