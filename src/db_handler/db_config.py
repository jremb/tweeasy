############################################################
# Contains our credential getter functions and the
# DbConnection class for the database, to handle db
# connection.
#
# It is assumed that credentials are set via environment
# variables.
############################################################
import os

from rich.console import Console
import psycopg
from psycopg.rows import dict_row

# Create rich console instance:
console = Console()


def pg_credentials() -> dict:
    """Dictionary of the parameters you'll need to
    connect to a postgres database with the psycopg driver.
    You'll need to have set the database password as
    an environment variable.
    :return: dictionary of credentials."""
    return {
        "dbname": "postgres",  # Default dbname. Change this as needed.
        "user": "postgres",  # Default user. Change this as needed.
        "password": os.environ["POSTGRES_PASSWORD"],
        "host": "pg",  # If using docker-compose, this needs to match postgres service name
        "port": "5432",  # If using docker-compose, you can leave this set to default
    }


class DbConnection:
    """Decorators for handling connections to postgres container."""
    params = pg_credentials()

    def with_connection(func):
        """Decorator for handling non-async connection.

        The psycopg connection cursor's row_factory is set to work with
        dictionaries."""
        params = pg_credentials()

        def wrapper(self, *args, **kwargs):
            conn = psycopg.connect(**params)
            # To make working with Pydantic a little more straightforward,
            # we'll set the row_factory to work with dicts
            cur = conn.cursor(row_factory=dict_row)
            try:
                res = func(self, cur, *args, **kwargs)
            except Exception as e:
                console.log(e)
                conn.rollback()
                raise
            else:
                conn.commit()
            finally:
                conn.close()
            return res

        return wrapper

    def with_async_connection(func):
        """Decorator for handling async connections.

        The psycopg connection cursor's row_factory is set to work with
        dictionaries."""
        params = pg_credentials()

        async def async_wrapper(self, *args, **kwargs):
            conn = await psycopg.AsyncConnection.connect(**params)
            # To make working with Pydantic a little more straightforward,
            # we'll set the row_factory to work with dicts
            cur = conn.cursor(row_factory=dict_row)
            try:
                res = await func(self, cur, *args, **kwargs)
            except Exception as e:
                console.log(e)
                await conn.rollback()
                raise
            else:
                await conn.commit()
            finally:
                await conn.close()
            return res

        return async_wrapper

    def with_copy(func):
        """Decorator for handling cursor.copy() STDIN/STDOUT"""

        def wrapper(self, *args, **kwargs):
            conn = psycopg.connect(**DbConnection.params)
            try:
                res = func(self, conn, *args, **kwargs)
            except Exception as e:
                console.log(e)
                conn.rollback()
                raise
            else:
                conn.commit()
            finally:
                conn.close()
            return res

        return wrapper

    def with_async_copy(func):
        """Decorator for handling async cursor.copy() STDIN/STDOUT.
        Passes connection to function."""
        params = pg_credentials()

        async def async_wrapper(self, *args, **kwargs):
            res = None
            conn = await psycopg.AsyncConnection.connect(**params)
            await conn.set_autocommit(True)
            try:
                res = await func(self, conn, *args, **kwargs)
            except Exception as e:
                console.log(e)
                await conn.rollback()
                raise
            else:
                await conn.close()
            finally:
                await conn.close()
            return res

        return async_wrapper
