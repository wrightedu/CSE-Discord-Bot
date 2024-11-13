import os
import sqlite3
import datetime


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
        return None  # No error
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
        time_out (float): The time delta of time in and time out when the user checks out

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


def update_timesheet(conn, time_id: int, discord_id: str, time_in: str, time_out: str, total_time: float) -> bool:
    """
        Takes the arguments to update an existing record in the timesheet Table
        discord_id and time_in are NOT NULL in the database and must be provided

        Args:
            conn: Connection object returned by the `create_connection` function
            time_id (int): The timesheed id of the user that needs to be updated
            discord_id (str): The discord id of the user
            time_in (str): The datetime object coverted into String of when the user checks-in.
                            Not used when updating the record
            time_out (str): The datetime object converted into String of when the user checks-out
            total_time (float): The time delta of time in and time out
                                obtained after user checks out

        Output:
            Returns boolean value to signify if
                the update operatation was Completed(True) or failed(False)
     """
    if conn is not None:
        try:
            c = conn.cursor()
            update_timesheet_query = """ UPDATE timesheet SET time_out = ?, total_time = ? where discord_id = ? and time_id = ?"""
            c.execute(update_timesheet_query,
                      (time_out, total_time, discord_id, time_id))
            print(
                f"User {discord_id} has been updated with checkout entry @ {time_out}")
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return False
        conn.commit()
        return True
    else:
        print("Error! Cannot create database connection.")
        return False


def get_timesheet_id(conn, discord_id: str):
    """
    Given a Discord ID, find the timesheet ID that has been opened by that user

    Args:
        conn: Connection object returned by the `create_connection` function
        discord_id (str): A Discord user ID
    Outputs:
        timesheet_id (int): the timesheet ID open for a particular user
    """
    if conn is not None:
        try:
            c = conn.cursor()

            timesheet_query = """SELECT time_id FROM timesheet WHERE discord_id = ? AND time_out is NULL AND total_time is NULL"""
            c.execute(timesheet_query, (discord_id,))

            timesheet = c.fetchall()

            if (len(timesheet) > 1):
                print("Error! Multiple open timesheets for user.")
                return None
            elif (len(timesheet) != 1):
                print("Error! No timesheet open for user.")
            else:
                return timesheet[0][0]
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")


def update_pomodoro(conn, pomo_id: int,  timesheet_id: int, issue: str, time_start: str, time_finish: str = None,
                    time_delta: float = None, status: int = None, help_count: float = None):
    """
        Takes the arguments to update an existing record in the pomoodoro Table
        timesheet_id, issue, and time_start are NOT NULL in the database and must be provided

    Args:
        conn: Connection object returned by the `create_connection` function
        pomo_id (int): The `int` pomodoro_id of the pomodoro user is working through
        timesheet_id (int): The current timesheet_id of the user who's invoking the pomodoro function for a given day
        issue (str): Description of the issue the user is having as entered by the user.
        time_start (str): The datetime object converted into String of when the user starts pomodoro
        time_finish (str): The datetime object converted into String of when the user stops pomo
        time_delta (float): The time delta of time start and time finish from when user starts the pomodoro and stops it
        status (int): 0 for not checked, 1 for checked, 2 for completed as "not done", 3 for completed as "done"
        help_count (float): number of times the user has requested help/hit the help buttonime out
                                obtained after user checks out

        Output:
            Returns boolean value to signify if
                the update operatation was Completed(True) or failed(False)
    """
    if conn is not None:
        try:
            c = conn.cursor()
            update_pomodoro_query = """ UPDATE pomodoro SET time_finish = ?, time_delta = ?, status = ?, help_count = ? where pomo_id = ? and timesheet_id = ?"""
            c.execute(update_pomodoro_query,
                      (time_finish, time_delta, status, help_count, pomo_id, timesheet_id))
            print(
                f"Pomodoro {pomo_id} has been updated for timesheet {timesheet_id}")
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return False
        conn.commit()
        return True
    else:
        print("Error! Cannot create database connection.")
        return False


def get_timesheet(conn, timesheet_id: int, discord_id: str):
    """
    Given a Discord ID, find the timesheet ID that has been opened by that user

    Args:
        conn: Connection object returned by the `create_connection` function
        timesheet_id (int): A timesheet ID
        discord_id (str): A Discord user ID
    Outputs:
        timesheet (list): the timesheet open for a particular user
    """
    if conn is not None:
        try:
            c = conn.cursor()

            timesheet_query = """SELECT * FROM timesheet WHERE time_id = ? AND discord_id = ?"""
            c.execute(timesheet_query, (timesheet_id, discord_id,))

            timesheet = c.fetchall()

            if (len(timesheet) > 1):
                print("Error! Multiple open timesheets for user.")
                return None
            elif (len(timesheet) != 1):
                print("Error! No timesheet open for user.")
            else:
                return timesheet[0]
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")


def get_pomodoro_id(conn, discord_id: str):
    """
    Given a Discord ID, find the pomodoro ID that has been opened by that user

    Args:
        conn: Connection object returned by the `create_connection` function
        timesheet_id (int): A timesheet ID
        discord_id (str): A Discord user ID
    Outputs:
        timesheet (list): the pomodoro open for a particular user
    """
    if conn is not None:
        try:
            c = conn.cursor()

            timesheet_query = """SELECT pomo_id FROM pomodoro INNER JOIN timesheet ON pomodoro.timesheet_id = timesheet.time_id WHERE timesheet.discord_id = ? AND pomodoro.time_finish is NULL AND pomodoro.time_delta is NULL"""
            c.execute(timesheet_query, (discord_id,))

            timesheet = c.fetchall()

            if (len(timesheet) > 1):
                print("Error! Multiple open pomodoros for user.")
                return None
            elif (len(timesheet) != 1):
                print("Error! No pomodoro open for user.")
                return None
            else:
                return timesheet[0][0]
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")


def get_pomodoro(conn, pomodoro_id: int, timesheet_id: int):
    """
    Given a Discord ID, find the timesheet ID that has been opened by that user

    Args:
        conn: Connection object returned by the `create_connection` function
        timesheet_id (int): A timesheet ID
        discord_id (str): A Discord user ID
    Outputs:
        timesheet (list): the timesheet open for a particular user
    """
    if conn is not None:
        try:
            c = conn.cursor()

            timesheet_query = """SELECT * FROM pomodoro WHERE pomo_id = ? AND timesheet_id = ?"""
            c.execute(timesheet_query, (pomodoro_id, timesheet_id,))

            timesheet = c.fetchall()

            if (len(timesheet) > 1):
                print("Error! Multiple open pomodoros for user.")
                return None
            elif (len(timesheet) != 1):
                print("Error! No pomodoro open for user.")
            else:
                return timesheet[0]
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")


def get_all_open_pomodoros(conn):
    """
    Return all open pomodors for comparison

    Args:
        conn: Connection object returned by the `create_connection` function
    Outputs:
        pomodoros (list): a list of all open pomodoros
    """
    if conn is not None:
        try:
            c = conn.cursor()

            pomodoro_query = """SELECT pomodoro.*, timesheet.discord_id FROM pomodoro INNER JOIN timesheet ON pomodoro.timesheet_id = timesheet.time_id WHERE pomodoro.time_finish IS NULL and pomodoro.time_delta IS NULL and pomodoro.status IS NULL AND (pomodoro.status IS 0 OR pomodoro.status IS 1 OR pomodoro.status IS NULL)"""
            c.execute(pomodoro_query)

            pomodoros = c.fetchall()

            if (len(pomodoros) < 1):
                return None
            else:
                return pomodoros
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")


def get_all_open_timesheets(conn):
    """
    Return all open timesheets for comparison

    Args:
        conn: Connection object returned by the `create_connection` function
    Outputs:
        timesheets (list): a list of all open timesheets
    """
    if conn is not None:
        try:
            c = conn.cursor()

            timesheet_query = """SELECT * FROM timesheet WHERE time_out IS NULL and total_time IS NULL"""
            c.execute(timesheet_query)

            timesheets = c.fetchall()

            if (len(timesheets) < 1):
                return None
            else:
                return timesheets
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")


def close_all_pomodoros(conn, time_id: str, end_time: float):
    """
    Close all open pomodoros for a provided time_id

    Args:
        conn: Connection object returned by the `create_connection` function
        time_id: Timesheet ID to close all pomodoros associated with
        end_time: Time epoch of end time
    """
    if conn is not None:
        try:
            c = conn.cursor()

            pomodoro_query = """SELECT * FROM pomodoro WHERE timesheet_id = ? AND time_finish is NULL AND time_delta IS NULL"""
            c.execute(pomodoro_query, (time_id,))

            pomodoros = c.fetchall()

            if (len(pomodoros) > 0):
                for pomodoro in pomodoros:
                    start_time = float(pomodoro[3])
                    total_time = end_time - start_time

                    update_pomodoro(
                        conn, pomodoro[0], pomodoro[1], pomodoro[2], pomodoro[3], end_time, total_time, 2)
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")


def get_user_report(conn, discord_id: str, start_date: str, end_date: str):
    """
    Returns all timesheet record, total hours worked, complete pomodor records.

    Args: 
        conn: Connection object returned by the `create_connection` function
        start_date: The desired start date for the report
        end_date: The desired end date for the report
    """
    # print(discord_id, start_date, end_date)
    if conn is not None:
        try:
            c = conn.cursor()
            record_query = """SELECT * FROM timesheet WHERE discord_id = ?
                                AND time_in BETWEEN ? and ?;"""
            sum_query = """SELECT SUM(total_time) as total_worked FROM timesheet
                            WHERE discord_id = ? AND time_in BETWEEN ? and ?;"""
            complete_pomodoro_query = """SELECT pomodoro.timesheet_id, pomodoro.pomo_id,
                                            pomodoro.status,pomodoro.time_delta 
                                            FROM pomodoro JOIN timesheet ON pomodoro.timesheet_id=timesheet.time_id 
                                            WHERE timesheet.discord_id = ? AND status = 1;"""
            c.execute(record_query, (discord_id, start_date, end_date))
            all_records = c.fetchall()
            # print(all_records)

            c.execute(sum_query, (discord_id, start_date, end_date))
            total_hours = c.fetchall()
            # print(total_hours)

            c.execute(complete_pomodoro_query, (discord_id,))
            complete_pomodoros = c.fetchall()
            # print(complete_pomodoros)

            return all_records, total_hours, complete_pomodoros
        except sqlite3.Error as e:
            print(e)
            conn.rollback()
            return None
    else:
        print("Error! Cannot create database connection")

async def update_pomo_rewards(conn, discord_id: str):
    today = datetime.datetime.today().timestamp()