############################################################
# File for all of our SQL statements.
############################################################
from typing import Tuple
from utils.logger import log, logger


def create_users_or_follower_table(table_name: str) -> str:
    """SQL for the UserFollowerDriver class, creating either a table of
    users or followers. Error handling for incorrect table specification
    should be done by the caller.

    Args:
        table_name (str): name of the table to be created: users || followers"""
    if table_name == "users":
        user_id = "user_id"
    else:
        user_id = "follower_id"
    return f"""
    CREATE TABLE IF NOT EXISTS
        {table_name} (
                {user_id} BIGINT PRIMARY KEY,
                name TEXT,
                screen_name TEXT,
                location TEXT,
                description TEXT,
                url TEXT,
                entities JSON,
                protected BOOL,
                followers_count INT,
                friends_count INT,
                listed_count INT,
                created_at TIMESTAMP,
                favorites_count INT,
                verified BOOL,
                statuses_count INT,
                status JSON,
                withheld_in_countries TEXT,
                collected TIMESTAMPTZ);

    CREATE INDEX ON {table_name} ({user_id});"""


def create_join_table(
        table_name: str,
        first_table: Tuple[str, str],
        second_table: Tuple[str, str]
) -> str:
    """SQL for creating our join table.
    :param table_name: the name you want assigned to the join table.
    :param first_table: name of first table and foreign key
    :param second_table: name of second table and foreign key
    :return: sql for query
    """
    return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            {second_table[1]} BIGINT,
            {first_table[1]} BIGINT,
            FOREIGN KEY 
                ({second_table[1]})
            REFERENCES 
                {second_table[0]}({second_table[1]})
            ON DELETE CASCADE,
            FOREIGN KEY 
                ({first_table[1]})
            REFERENCES
                {first_table[0]}({first_table[1]})
            ON DELETE CASCADE
        );
        CREATE INDEX ON {table_name} ({second_table[1]}, {first_table[1]});"""


def get_all_tables():
    return f"""
    SELECT 
        * 
    FROM 
        pg_catalog.pg_tables
    WHERE
        schemaname = 'public';"""


def check_table_exists(table: str) -> str:
    """SQL for checking that a table exists.
    :param table: the name of the table to check"""
    return f"SELECT to_regclass('public.{table}');"


def check_user_exists(username: str, table: str) -> str:
    """SQL for checking that a user exists in
    the database.
    :param username: name of the user to check.
    :param table: name of the table to check."""
    return f"""
        SELECT 
            *
        FROM
            {table}
        WHERE
            screen_name = '{username}';"""


def drop_table(table: str) -> str:
    """SQL for deleting a table.
    :param table: the name of the table you want to drop."""
    return f"""
        DROP TABLE IF EXISTS
            {table}
        CASCADE;"""


def get_table_row_count(table: str) -> str:
    """SQL for getting a count of rows in a table.
    :param table: name of table"""
    return f"""
        SELECT COUNT(1) as {table}
        FROM
            {table};"""


def get_current_timestamp() -> str:
    """SQL for getting the current timestamp from the database."""
    return "SELECT CURRENT_TIMESTAMP;"


def get_all_users_followers(user_id: int) -> str:
    """SQL for grabbing all data from the join table users_followers."""
    return f"""
        SELECT 
            follower_id
        FROM
            users_followers
        WHERE
            user_id = {user_id};"""


def get_all_follower_ids() -> str:
    """SQL fro grabbing all rows in follower_id column of followers table."""
    return """
        SELECT
            follower_id
        FROM
            followers;"""


def get_users_row(username=None) -> str:
    """SQL for grabbing all columns in users table for specified user"""
    return f"""
        SELECT
            *
        FROM
            users
        WHERE
            LOWER(screen_name) = '{username}';"""


def insert_user_data(table: str) -> str:
    """SQL for inserting user data into the table specified in the parameter. Error
    handling for incorrect specification should be done by the caller.
    :param table: name of the table to be updated"""
    if table == "users":
        user_id = "user_id"
    else:
        user_id = "follower_id"
    return f"""
        INSERT INTO
            {table} (
                {user_id},
                name,
                screen_name,
                location,
                description,
                url,
                entities,
                protected,
                followers_count,
                friends_count,
                listed_count,
                created_at,
                favorites_count,
                verified,
                statuses_count,
                status,
                withheld_in_countries,
                collected
            )
        VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, CURRENT_TIMESTAMP);"""


def update_join_table() -> str:
    """SQL for updating the join table."""
    return f"""
        INSERT INTO users_followers (
            follower_id, 
            user_id
        )
        VALUES (%s, %s);
    """


def copy_in_ids() -> str:
    return "COPY followers (follower_id) FROM STDIN (FORMAT TEXT);"


def copy_in_join_table() -> str:
    return "COPY users_followers (follower_id, user_id) FROM STDIN;"


def copy_in_lookup_users(table_name: str = "followers") -> str:
    return f"COPY {table_name} FROM STDIN;"


def copy_all_follower_ids() -> str:
    """SQL for copying all rows in follower_id column of followers table."""
    return "COPY followers (follower_id) TO STDOUT;"


def copy_out_user_sn() -> str:
    """SQL for copying just the username from the users table."""
    return "COPY users (screen_name) TO STDOUT;"


def copy_out_ids(table_name) -> str:
    """SQL for copying just the username from the users table."""
    ids = "follower_id" if table_name == "followers" else "user_id"
    return f"COPY {table_name} ({ids}) TO STDOUT;"


def copy_out_all(table_name) -> str:
    """SQL for copying all columns and rows from <table_name>"""
    return f"COPY {table_name} TO STDOUT;"
