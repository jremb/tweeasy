############################################################
# The following is only intended as a rough template.
# It assumes you write your SQL in a separate file,
# stored in the same directory as this file, called
# pg_sql.
#
# Storing the SQL in its own file is just a quick-fix
# preference, since right now there is no out-of-the-box
# compatibility with SQLAlchemy and Psycopg3.
############################################################
import asyncio
import json
import time
import logging
from typing import Set, Union, List

import psycopg
from rich.console import Console

from db_handler import pg_sql
from utils import exceptions
from utils.models import UserModel
from db_handler.db_config import DbConnection as DbC
from utils.logger import log, log_setter


log_setter(__name__, format="\t%(lineno)d - %(message)s")
logger = logging.getLogger(__name__)

# Create rich console instance:
console = Console()


class UserFollowerDriver:
    """Class for handling data that will have a user-follower relationship. E.g.,
    performing analysis on a user or group of users based on follower data."""

    def __init__(self):
        # When starting the containers with docker-compose, the database
        # may not be ready to accept connections right away. In that case,
        # we sleep and try again.
        try:
            self._init()
        except psycopg.OperationalError as e:
            console.log(f"{e}\n\nSleeping for 5 seconds...")
            time.sleep(5)
            console.log(f"Trying connection again...")
            try:
                self._init()
            except psycopg.OperationalError as e:
                logger.critical(
                    "Unable to connect to the\ndatabase after two attempts.")
                raise

    @log
    def _init(self):
        """Method that allows us to repeatedly
        try to initialize instance."""
        if not self.check_table_exists("users"):
            self.create_table("users")
            console.log("`users_followers` table not found :exclamation: \nCreating table")
        if not self.check_table_exists("followers"):
            self.create_table("followers")
            console.log("`followers` table not found :exclamation: \nCreating table")
        if not self.check_table_exists("users_followers"):
            self.create_join_table()
            console.log("`users_followers` table not found :exclamation: \nCreating table")

    @DbC.with_async_connection
    @log
    async def reset_all_tables(self, cursor) -> None:
        sql = pg_sql.get_all_tables()
        await cursor.execute(sql)
        res_list: List[dict] = await cursor.fetchall()
        table_list: List[str] = [table["tablename"] for table in res_list]
        logger.info(f"Result of fetchall: {res_list}")
        logger.info(f"Table list: {table_list}")
        for table in table_list:
            drop_task = asyncio.create_task(self.drop_table(table))
            await drop_task
            if table == "users_followers":
                self.create_join_table()
            else:
                self.create_table(table)

    @DbC.with_connection
    @log
    def create_table(self, cursor, table) -> None:
        """Creates the users table, which will hold
        the account information for users of interest."""
        sql = pg_sql.create_users_or_follower_table(table)
        cursor.execute(sql)
        console.log(f"  {table}... :white_check_mark:")

    @DbC.with_connection
    @log
    def create_join_table(self, cursor) -> None:
        """Creates our join table."""
        sql = pg_sql.create_join_table(
            "users_followers",
            ("users", "user_id"),
            ("followers", "follower_id"),
        )
        cursor.execute(sql)
        console.log(f"  users_followers... :white_check_mark: \n\n")

    @DbC.with_connection
    @log
    def check_table_exists(self, cursor, table: str) -> bool:
        """Checks whether a table exists in the database.
        :param table: the name of the table to check.
        :return: True/False
        """
        sql = pg_sql.check_table_exists(table)
        cursor.execute(sql)
        exists = cursor.fetchone()["to_regclass"]
        if exists:
            return True
        else:
            return False

    @DbC.with_connection
    @log
    def check_user_exists(self, cursor, username: str, table: str) -> bool:
        """Checks whether a user exists in a specific table.
        :param username: the username of the person to check.
        :param table: which table to check for the username.
        :return: True/False"""
        sql = pg_sql.check_user_exists(username, table)
        cursor.execute(sql)
        res = cursor.fetchone()
        if res:
            return True
        else:
            return False

    @DbC.with_async_connection
    @log
    async def drop_table(self, cursor, table: str) -> None:
        """Deletes table given as argument for table parameter.
        :param table: name of the table we want to drop.
        """
        logger.info(f"dropping {table}")
        if table == "all":
            for t in ["followers", "users", "users_followers"]:
                logger.info(f"dropping table {t}")
                sql = pg_sql.drop_table(t)
                await cursor.execute(sql)
        else:
            logger.info(f"dropping table {table}")
            sql = pg_sql.drop_table(table)
            await cursor.execute(sql)

    @DbC.with_async_connection
    @log
    async def get_table_row_count(self, cursor, table: Union[str, list]) -> Union[dict, int]:
        count_dict = {}
        if isinstance(table, list):
            for t in table:
                sql = pg_sql.get_table_row_count(t)
                try:
                    await cursor.execute(sql)
                    res = await cursor.fetchone()
                    count_dict.update(res)
                except psycopg.errors.UndefinedTable:
                    console.log(f"{table} table could not be found in the database")
            return count_dict
        else:
            sql = pg_sql.get_table_row_count(table)
            try:
                await cursor.execute(sql)
                return await cursor.fetchone()
            except psycopg.errors.UndefinedTable:
                console.log(f"{table} table could not be found in the database")

    @DbC.with_async_connection
    @log
    async def get_all_followers_ids(self, cursor) -> Union[Set[int], None]:
        console.log("Loading pre-existing followers data...")
        sql = pg_sql.get_all_follower_ids()
        await cursor.execute(sql)
        return set(v["follower_id"] for v in await cursor.fetchall())

    @DbC.with_async_connection
    @log
    async def get_all_users_followers(self, cursor, user_id: int) -> Union[Set[int], None]:
        """Grabs all entries from `users_followers` that have specified `user_id`
        in `user_id` column of table. Returns just the follower_id data in a set."""
        sql = pg_sql.get_all_users_followers(user_id)
        await cursor.execute(sql)
        return set(v["follower_id"] for v in await cursor.fetchall())

    @DbC.with_connection
    @log
    def get_users_row(self, cursor, screen_name):
        sql = pg_sql.get_users_row(username=screen_name)
        cursor.execute(sql)
        return cursor.fetchall()

    @DbC.with_async_connection
    @log
    async def insert_user_data(self, cursor, table: str, user_data: UserModel) -> None:
        """Inserts user data into the database.
        :param cursor:
        :param table: name of the table must be either users
        or followers.
        :param user_data: the object returned from a Tweepy query
        """
        if table != "users" and table != "followers":
            raise exceptions.TableSpecifierError(
                table, "The table name must be either `users` or `followers`"
            )
        sql = pg_sql.insert_user_data(table)
        # With text fields, possible to run into NUL (0x00) bytes.
        # To avoid DataError:
        name = user_data.name.replace(u"\x00", "")
        screen_name = user_data.screen_name.replace(u"\x00", "")
        location = user_data.location.replace(u"\x00", "")
        description = user_data.description.replace(u"\x00", "")
        try:
            await cursor.execute(
                sql,
                (
                    user_data.id,
                    name,
                    screen_name,
                    location,
                    description,
                    user_data.url,
                    json.dumps(user_data.entities),
                    user_data.protected,
                    user_data.followers_count,
                    user_data.friends_count,
                    user_data.listed_count,
                    user_data.created_at,
                    user_data.favourites_count,
                    user_data.verified,
                    user_data.statuses_count,
                    json.dumps(user_data.status),
                    user_data.withheld_in_countries,
                ),
            )
            console.print(f"[green]{name}[/] added to {table} database")
        except psycopg.errors.UniqueViolation as e:
            return

    @DbC.with_async_connection
    @log
    async def update_join_table(self, cursor, user_id, follower_id) -> None:
        sql = pg_sql.update_join_table()
        await cursor.execute(
            sql,
            (
                follower_id,
                user_id,
            )
        )

    @DbC.with_copy
    @log
    def copy_out_user_sn(self, connection) -> set:
        sql = pg_sql.copy_out_user_sn()
        user_sns = set()
        with connection.cursor().copy(sql) as copy:
            for row in copy.rows():
                user_sns.add(row[0].lower())
        return user_sns

    @DbC.with_copy
    @log
    def copy_out_ids(self, connection, table_name: str = "followers") -> Set[int]:
        follower_ids: set = set()
        sql = pg_sql.copy_out_ids(table_name)
        with connection.cursor().copy(sql) as copy:
            while data := copy.read():
                follower_ids.add(int(data))
        return follower_ids

    # TODO: Fix indirect approach (return)!
    @DbC.with_copy
    @log
    def copy_out_all(self, connection, table_name: str = ""):
        out_data = bytearray()
        sql = pg_sql.copy_out_all(table_name)
        with open(f"./src/data/copy_out_all_{table_name}.out", "wb") as out_file:
            with connection.cursor().copy(sql) as copy:
                for data in copy:
                    out_file.write(data)
                    out_data += bytearray(data)
        return out_data

    @DbC.with_copy
    @log
    def copy_in_ids(self, connection, file):
        sql = pg_sql.copy_in_ids()
        with connection.cursor() as cursor:
            with open(file, "rb") as in_file:
                # Copy in to follower's table:
                with cursor.copy(sql) as copy:
                    while data := in_file.read():
                        copy.write(data)

    @DbC.with_copy
    @log
    def copy_in_join(self, connection, join_data: str):
        try:
            sql = pg_sql.copy_in_join_table()
            with connection.cursor() as cursor:
                with cursor.copy(sql) as copy:
                    copy.write(join_data)
        except psycopg.errors.BadCopyFileFormat:
            # Set up log:
            log_file = "./src/data/pg_driver_critical.log"
            log_setter(__name__, file_name=log_file)
            pg_logger = logging.getLogger(__name__)
            pg_logger.critical("BadCopyFileFormat error.\n")
            pg_logger.critical(f"join_data: {join_data}\n")
            raise

    @DbC.with_copy
    @log
    def copy_in_lookup_users(self, connection, table_name: str, user_data: str):
        try:
            sql = pg_sql.copy_in_lookup_users(table_name)
            with connection.cursor() as cursor:
                with cursor.copy(sql) as copy:
                    copy.write(user_data[:-3])
        except psycopg.errors.BadCopyFileFormat:
            data_list = user_data.split("\n")
            # Grab first element of list, which is user's Twitter id:
            id_list = [user.split("\t")[0] for user in data_list]
            # Set up log:
            log_file = "./src/data/pg_driver_critical.log"
            log_setter(__name__, file_name=log_file)
            pg_logger = logging.getLogger(__name__)
            pg_logger.critical(f"BadCopyFileFormat error. id_list: {id_list}\n")
            pg_logger.critical(f"data_list: {data_list}\n")
            raise
