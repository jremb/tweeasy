import sys
import time
from typing import List, Tuple, Set, Union
from pathlib import Path
import asyncio
import platform
import datetime
import logging

import tweepy
from tweepy.models import User
from rich import print
from rich.traceback import install
from rich.console import Console, Group
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn, TaskID
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live

from utils.api_config import with_api1_connection 
from utils.formatters import user_bytearray, format_time
from utils.logger import log, logger, log_setter
from db_handler.tweeasy_handler import UserFollowerDriver

# TODO: Implement API handler class in its own module

logger.info(f"\n\n\t\t\t[{datetime.datetime.now()}]")
# Reset logger for main.py:
log_setter(__name__, format="\t%(lineno)d - %(message)s")
logger = logging.getLogger(__name__)

MENU = """
# Options 
1. Get user data
2. Get user follower data
3. Get follower data by iterating over a list of users
4. Get follower ids by iterating over a list of users
5. Get row count for table(s)
6. Drop a table
7. Exit
"""

# Initialize rich traceback:
install()
# Create rich console instance for logging:
console = Console()
# Create db handler instance:
sf_db = UserFollowerDriver()
# Create progress bars:
id_progress = Progress(
    TextColumn("follower id query"),
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeElapsedColumn())
lookup_progress = Progress(
    TextColumn("lookup query"),
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TimeElapsedColumn())
sleep_progress = Progress(
    TextColumn(":sleeping: :zzz: [cyan]rate limit"),
    BarColumn(),
    TimeRemainingColumn())
progress_group = Group(
    Panel(
        Group(id_progress, lookup_progress)
    ),
    sleep_progress)
live = Live(progress_group)


@log
def get_username_list() -> List[str]:
    msg = "Enter the usernames directly in a comma-separated list [underline]or[/] provide a filename. If providing " \
          "a filename, the file must be a tsv file in the data directory and you must provide the file extension as " \
          "part of the filename:\n\te.g., 'username_list.tsv'\n "
    live.console.log(msg)
    user_input = input()
    if "." in user_input:
        filepath = f"./src/data/{user_input}"
        if not Path(filepath).exists():
            live.console.log("[bold red]File not found. Quitting...[/bold red]")
            sys.exit()
        else:
            with open(filepath, "r") as f:
                return [name for name in f.read().split("\t") if name]
    else:
        res: List[str] = [name.strip() for name in user_input.split(",")]
        return res


@log
def process_ids(user_id: int, ids: Set[int], just_ids: bool) -> None:
    # If lookup_users query isn't being run, then
    # it is safe to copy follower ids into followers table:
    if just_ids:
        sf_db.copy_in_ids("\n".join(str(_id) for _id in ids))
    join_data = f"\t{user_id}\n".join(str(_id) for _id in ids) + f"\t{user_id}"
    sf_db.copy_in_join(join_data)


@log
def process_lookup_users(users_list: List[User], ids_exist: bool = False) -> None:
    users_bytearr: bytearray = user_bytearray(users_list, ids_exist)
    sf_db.copy_in_lookup_users("followers", users_bytearr.decode())


@log
async def sleep_track(reset_time) -> None:
    """Sleeps for 1 second and then updates sleep progress bar
    until current time >= reset time. If no progress instance is passed,
    then one is instantiated will create one.

    Args:
        reset_time (int): time at which api rate limit will reset
    """
    logger.info(f"reset_time = {reset_time:,}")
    sleep_task: TaskID = sleep_progress.add_task(":sleeping: :zzz: [cyan]rate limit", total=reset_time)
    for i in range(reset_time):
        await asyncio.sleep(1)
        sleep_progress.update(sleep_task, advance=1)
    sleep_progress.update(sleep_task, visible=False)
    sleep_progress.stop_task(sleep_task)


@with_api1_connection
@log
def get_rate_limit(api, query: str = "ids") -> Tuple[int, int]:
    """Grabs the statuses for our Twitter API account, related to
    type of query. If relevant, formats remaining queries (rate_limit)
    according to Tweepy's pagination capability.

    Args:
        api (tweepy.api.API): supplied by decorator.
        query (str): query the rate limit pertains to. E.g., `ids` for 
        'get_follower_ids' query. `lookup` for 'lookup_users' query.
        Defaults to `ids`.
    Returns:
        Tuple:
            rate_limit (int): how many more queries we can make. `ids` assumes
            use of tweepy.Cursor with count parameter set to 5,000. We
            subtract one to make sure we don't trigger tweepy.api.API's own
            sleeper. `lookup` assumes grouping of 100 accounts.
            reset_time (int): interval between current time and time at
            which our rate limit will reset.
    """
    status = api.rate_limit_status()
    if query == "ids":
        id_rate_status = status["resources"]["followers"]["/followers/ids"]
        rate_limit = id_rate_status["remaining"] * 5_000 - 1 if id_rate_status["remaining"] else 0
        reset_time = id_rate_status["reset"] - int(time.time())
        return rate_limit, reset_time
    elif query == "lookup":
        lookup_rate_status = status["resources"]["users"]["/users/lookup"]
        logger.debug(f"lookup rate_status = {lookup_rate_status}")
        # rate_limit = lookup_rate_status["remaining"] * 20 - 100 if lookup_rate_status["remaining"] else 0
        rate_limit = lookup_rate_status["remaining"] * 100 - 1 if lookup_rate_status["remaining"] else 0
        reset_time = lookup_rate_status["reset"] - int(time.time())
        return rate_limit, reset_time


@with_api1_connection
@log
def api1_get_user(api, username: str) -> Tuple[Union[User, List[dict]], bool]:
    """Loads all pre-existing users from users table. If <username> not already
    in table, calls api for user data. If <username> already in table, just passes
    user data loaded from table back to caller.

    Args:
        api (tweepy.api.API): supplied by decorator.
        username (str): name following the @ symbol of a Twitter account.
    Returns:
        Tuple:
            [Union:
                tweepy.models.User,
                List[dict]]
                    Either the api return object or a List[dict] object from the
                    users table. Either one will be user data from Tweepy's
                    `get_user` method, List[dict] has been formatted from database.
            Bool: Whether the user data already existed in the database.
    """
    user_sns: set = sf_db.copy_out_user_sn()
    if username not in user_sns:
        live.console.print(f"Executing `[yellow]get_user[/]` query for [green]{username}[/]...")
        return api.get_user(screen_name=username), False
    else:
        live.console.print(f"[greeen]{username}[/] already in `users` table")
        return sf_db.get_users_row(username), True


@with_api1_connection
@log
async def api1_get_follower_ids(
        api,
        user_data: Union[User, List[dict]],
        just_ids: bool = True
) -> None:
    """Collects follower ids from user specified in <user_data> param. Collected
    ids are filtered down into two groups: those ids which don't already exist
    in the `followers` table and those ids which don't already exist joined to
    specific user in `users_followers` table.

    Unique ids will then either be passed to the `process_ids` function (if
    `just_ids` == True) or the `lookup_users` function (if `just_ids == False).

    We track the rate limit specific to this query throughout the process. If we
    are about to hit the rate limit the collection process will pause and all
    collected ids will be filtered and either processed or passed to `lookup_users`
    at this time. If the rate limit has not yet reset before these tasks are
    finished then we sleep.

    Args:
        api (tweepy.api.API): supplied by decorator

        user_data (Union): user_data object will either be List[dict], if user
        already exists in users table, or tweepy.models.User, if user does not
        already exist in users table.

        just_ids (bool): indicates whether we just want to perform this query,
        or if we also want to perform the `lookup_users` query on the follower ids
        we collect. If just_ids == False, then we will hand off the follower ids
        to the `lookup_users` query either once we have collected all the ids or
        once we have reached the query rate limit and are waiting for it to reset.
    """

    # If `username` passed at earlier stage already exists in the database, then
    # we will be passed user_data as a list from the database. Otherwise, it will
    # be a tweepy.models.User object directly from `get_user` query:
    if isinstance(user_data, list):
        username = user_data[0]["screen_name"]
        user_id = user_data[0]["user_id"]
        followers_count = user_data[0]["followers_count"]
    else:
        username = user_data.screen_name
        user_id = user_data.id
        followers_count = user_data.followers_count
    # Set of pre-existing id data in `users_followers` table for this user.
    # We initialize coroutine task since this table can be significantly larger
    # than `followers` table:
    load_join_task = asyncio.create_task(sf_db.get_all_users_followers(user_id))
    join_table_data: set = await load_join_task
    # Set of pre-existing follower_id data in `followers` table:
    follower_table_data: set = sf_db.copy_out_ids(table_name="followers")

    # Set up rich progress bar task for query:
    id_task: TaskID = id_progress.add_task("follower ids", total=followers_count)
    with live:
        # Initialize set for holding total unique ids found during session:
        total_unique_ids = set()
        # Initialize set to hold ids until rate limit or total
        # for this user (if total < rate limit):
        temp_collection = set()

        # Check rate limit:
        rate_limit, reset_time = get_rate_limit(query="ids")
        if not rate_limit:
            await sleep_track(reset_time)
            # Get new status:
            rate_limit, reset_time = get_rate_limit(query="ids")

        live.console.print(f"[green]{username}[/]: {followers_count:,} followers")
        live.console.print("Executing `[yellow]get_follower_ids[/]` query...")
        # Iterate through follower ids:
        for follower in tweepy.Cursor(
                api.get_follower_ids, screen_name=username, count=5_000
        ).items():
            # Add follower's id to unfiltered set:
            temp_collection.add(follower)
            # Track with rate limit:
            rate_limit -= 1
            if not rate_limit:
                # Filter out duplicate ids:
                unique_ids = temp_collection.difference(follower_table_data)
                unique_joins = temp_collection.difference(join_table_data)
                # Add new unique follower ids to total_unique_ids
                total_unique_ids = total_unique_ids.union(unique_ids)
                # Handle unique ids:
                if not just_ids and unique_ids:
                    live.console.print(
                        f"Found {len(unique_ids):,} unique follower ids and {len(unique_joins):,} unique "
                        f"joins\nExecuting `[yellow]lookup_users[/]` query on follower ids while waiting for rate "
                        f"limit to reset.")
                    # Pass unique ids to `lookup_users` process:
                    await api1_lookup_users(user_id, unique_ids, unique_joins)
                elif unique_ids:
                    live.console.print(
                        f"Found {len(unique_ids):,} unique follower ids\nWhile waiting for rate limit to reset, "
                        "entering follower ids into database...")
                    # Pass unique ids to process for database entry:
                    process_ids(user_id, unique_ids, True)

                # Get new rate limit status:
                rate_limit, reset_time = get_rate_limit(query="ids")
                if not rate_limit:
                    # Create task for sleep_progress bar:
                    await sleep_track(reset_time)
                    # Get new rate limit status:
                    rate_limit, reset_time = get_rate_limit(query="ids")

                # Empty set:
                temp_collection = set()

            # Update progress bar:
            id_progress.update(id_task, advance=1)

        # Handle any remaining ids:
        if temp_collection:
            # Filter out duplicate ids:
            unique_ids = temp_collection.difference(follower_table_data)
            unique_joins = temp_collection.difference(join_table_data)
            # Add new unique follower ids to total_unique_ids
            total_unique_ids = total_unique_ids.union(unique_ids)
            # Handle unique ids:
            if not just_ids and (unique_ids or unique_joins):
                if not unique_ids:
                    process_ids(user_id, unique_ids, False)
                else:
                    live.console.print(
                        f"Found {len(unique_ids):,} unique follower ids and {len(unique_joins):,} unique "
                        f"joins\nExecuting `[yellow]lookup_users[/]` query on follower ids...")
                    await api1_lookup_users(user_id, unique_ids, unique_joins)
            elif unique_ids:
                live.console.print(f"Found {len(unique_ids):,} unique follower ids\nEntering ids into database...")
                process_ids(user_id, unique_ids, True)

        # Stop id_progress task:
        id_progress.update(id_task, visible=False)
        id_progress.stop_task(id_task)

        # Output how many new follower ids we've found:
        live.console.print(f"Total new ids found for {username}: {len(total_unique_ids):,}\n")


@with_api1_connection
@log
async def api1_lookup_users(
        api,
        user_id: int,
        follower_ids: Set[int],
        unique_joins: Set[int]
) -> None:
    """Runs `lookup_users` query for 100 follower ids at a time. These
    are immediately processed and entered into `followers` table and
    `users_follower` table.

    Rationale: Processing the results of the query 100 at a time is slightly
    slower than adding them to a set and then processing only after we have
    queried all ids, but there are two advantages to the former method:

    (1) it allows us to narrow down accounts causing 404 errors and
    (2) it allows us to not requery account sets if we can't avoid other
    errors like HTTP 500 or 503. (Making the former method faster than the
    latter, were we to encounter those errors on larger sets.)

    Additionally, in my own testing, the former method is still able to
    completely query and process the maximum number of ids that it can be
    passed from the `get_follower_ids` query before the api rate limit on
    that query resets. Thus, even though slower, no time is lost in the
    overall run-time when querying large sets of ids. For smaller sets,
    the time difference becomes negligible (e.g., a difference of 30 seconds).

    Args:
        api (tweepy.api.API): supplied by decorator.

        user_id (int): Twitter id for <user_id> from prior api call
        follower_ids (List[int]): Twitter ids of those following <user_id> that
        have not yet been entered into the `followers` table.

        unique_joins (Set[int]): Twitter ids of those following <user_id> that
        have not yet been entered into the `users_followers` table.
    """
    # TODO: Ensure rate limit calculation is accurate
    # Get number of follower ids to be processed:
    follower_count = len(follower_ids)
    # Convert follower_ids (set) to list:
    follower_ids = [_id for _id in follower_ids]

    # Set up rich progress task for query:
    lookup_task: TaskID = lookup_progress.add_task("lookup query", total=follower_count)
    # Get rate limit status:
    rate_limit, reset_time = get_rate_limit(query="lookup")
    logger.debug(f"`lookup_users` query rate_limit = {rate_limit}, reset_time: {reset_time}")
    if not rate_limit:
        await sleep_track(reset_time)
        # Get new status:
        rate_limit, reset_time = get_rate_limit(query="lookup")
        logger.debug(f"`lookup_users` query rate_limit = {rate_limit}, reset_time: {reset_time}")

    range_param = int(follower_count / 100)
    for i in range(range_param + 1):
        end_loc = min((i + 1) * 100, follower_count)
        # A small percentage of ids returned by `get_follower_ids` query
        # will 404 when running `lookup_users` query. If such an error
        # occurs in the set of hundred, we write the set to the log so that
        # the problem can be filtered out later if desired:
        try:
            hundred_followers: List[User] = api.lookup_users(
                user_id=follower_ids[i * 100: end_loc])
            # Add hundred followers to followers table:
            process_lookup_users(hundred_followers)
            set_of_hundred = set(user.id for user in hundred_followers)
            # Grab intersection of unique join ids and hundred followers:
            joins_to_process: set = unique_joins.intersection(set_of_hundred)
            # Process joins:
            process_ids(user_id, joins_to_process, False)
            # Filter out processed joins:
            unique_joins = unique_joins.difference(joins_to_process)
        except tweepy.errors.NotFound:
            not_found_ids = follower_ids[i * 100: end_loc]
            logger.error(
                f"[404 ERROR] At least one of the following ids could not be found in `lookup_users` "
                f"query:\n{not_found_ids}")
            live.console.print("[bold red][404 ERROR][/] NotFound error encountered for some user ids. See call log "
                               "for details.")
        finally:
            rate_limit -= 1

            # if not rate_limit:
            if not rate_limit:
                # Sleep:
                await sleep_track(reset_time)
                # Check rate limit again:
                rate_limit, reset_time = get_rate_limit(query="lookup")
                logger.info(f"`lookup` query rate_limit = {rate_limit}, reset_time: {reset_time}")
                if not rate_limit:
                    live.console.print("[orange]lookup_users[/] query rate limit not yet reset. Sleeping...")
                    await sleep_track(reset_time)
                    # Get new status:
                    rate_limit, reset_time = get_rate_limit(query="lookup")
                    logger.info(
                        f"`lookup` query rate_limit = {rate_limit}, reset_time: {reset_time}")

            # Update lookup_task:
            lookup_progress.update(lookup_task, advance=100)
    # If we didn't add unique_joins to join table earlier, do so
    # now:
    if unique_joins:
        process_ids(user_id, unique_joins, False)
    # Hide & stop lookup_progress bar:
    lookup_progress.update(lookup_task, visible=False)
    lookup_progress.stop_task(lookup_task)


@log
async def follower_data_pipe(username: str, just_ids: bool = True) -> None:
    """Handles the various data gathering steps.

    Args:
        username (str): name following the @ symbol of a Twitter account.
        just_ids (bool, optional): If True, will only grab follower ids.
        If false will grab all follower data. Defaults to True.
    """
    # with Live(progress_group) as live:
    live.console.print(f"\nProcessing [green]{username}[/]")
    start = time.perf_counter()
    user_data, in_db = api1_get_user(username)
    if not in_db:
        user_bytearr: bytearray = user_bytearray({user_data})
        sf_db.copy_in_lookup_users("users", user_bytearr.decode())

    followers_count = user_data.followers_count if not isinstance(user_data, list) else user_data[0]["followers_count"]

    # Get just follower ids
    if just_ids:
        # Check if ids file already exist and prompt user if they want to update ids:
        # TODO: Reimplement check for pre-existing ids this so that we check database.
        
        # Grab the ids:
        await api1_get_follower_ids(user_data, just_ids=True)
        duration, units = format_time(time.perf_counter() - start)
        live.console.print(f"Duration: {duration} {units}")

    # Get full follower data:
    else:
        await api1_get_follower_ids(user_data, just_ids=False)
        duration, units = format_time(time.perf_counter() - start)
        live.console.print(f"Duration: {duration} {units}")


@log
async def selection_one():
    """For getting user data."""
    username = input("Enter the username: ")
    # First check whether data for user already exists:
    res = sf_db.check_user_exists(username, "users")
    if res:
        proceed = input(
            "User already exists.\nProceed or cancel? (y/n)\n").lower()
        if proceed[0] == "n":
            return
    user_data = api1_get_user(username)
    await sf_db.insert_user_data("users", user_data[0])
    console.log(f"[green]{username} added to users table[/green]")


@log
async def selection_two():
    """For getting a user's follower data."""
    username = input("Enter the username: ")
    await follower_data_pipe(username)


@log
async def selection_three():
    """For getting full follower data by iterating over a list of users."""
    username_list = get_username_list()
    for user in username_list:
        await follower_data_pipe(user, just_ids=False)


@log
async def selection_four():
    """For getting follower IDs by iterating over a list of users."""
    users_list = get_username_list()
    for user in users_list:
        await follower_data_pipe(user)


@log
async def selection_five():
    """For getting the row count(s) of a table or tables."""
    table = input(
        "Enter the table name(s) you would like a row count of (can be a comma-separated list):\n"
    )
    if "," in table:
        table = [t.strip() for t in table.split(",")]
    res = await sf_db.get_table_row_count(table)
    console.log(res)


@log
async def selection_six():
    """For dropping a table."""
    table = input("Note: enter 'all' to drop and reset all tables.\nEnter table to drop: ")
    if table.lower() != "all":
        await sf_db.drop_table(table)
    else:
        await sf_db.reset_all_tables()


@log
async def main():
    while True:
        print(Markdown(MENU))
        try:
            selection = int(input("Option number: "))
            print()
            if selection == 1:
                await selection_one()
            if selection == 2:
                await selection_two()
            if selection == 3:
                await selection_three()
            if selection == 4:
                await selection_four()
            if selection == 5:
                await selection_five()
            if selection == 6:
                await selection_six()
            # Seven gives user a chance to change their mind after continue or before
            # selecting an option. The prompt gives the user an option after viewing
            # results, without having msg obscure those results.
            if selection == 7:
                sys.exit()
        except TypeError:
            print("Please enter a number")
        prompt = input("\nContinue? (y/n)\n").lower()
        # We'll use indexing in case user enters 'yes'/'no'
        if prompt[0] == "n":
            sys.exit()


if __name__ == "__main__":
    # Will get psycopg.InterfaceError if we don't set this on Windows.
    # As a Docker container this line isn't needed, but it's being left
    # in for those who may wish to run this apart from the container:
    system = platform.system()
    if system == "Windows":
        from asyncio import WindowsSelectorEventLoopPolicy

        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
