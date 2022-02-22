import json
import datetime
import logging
from typing import Tuple

import tweepy

from utils.logger import log, log_setter

log_setter(__name__, format="\t%(lineno)d - %(message)s")
logger = logging.getLogger(__name__)

# Initialize translation table:
nul_table = str.maketrans(u"\x00", " ")
trans_table = str.maketrans("""\r\n\t\\""", """    """)
trans_table.update(nul_table)


@log
def format_time(t: float) -> Tuple[float, str]:
    if t > 60:
        # Convert to minutes:
        t = round(t / 60, 2)
        # If hours, convert to hours frmat:
        if t > 60:
            t = t / 60
            return t, "hrs"
        return t, "min"
    return round(t, 2), "sec"


def format_attributes(user: tweepy.models.User) -> list:
    # Format text fields:
    name = user.name.translate(trans_table)
    screen_name = user.screen_name.translate(trans_table)
    location = user.location.translate(trans_table) if user.location else r"\N"
    description = user.description.translate(
        trans_table) if user.description else r"\N"
    url = user.url.translate(trans_table) if user.url else r"\N"

    # Format json fields:
    entities = str(user.entities).replace('"', "'")
    entities = entities.replace("'{", "E'{")
    entities = entities.translate(trans_table)
    # Can't access status on protected accounts
    try:
        status = str(user.status._json).replace('"', "'")
        status = status.replace("'{", "E'{")
        status = status.translate(trans_table)
        if "\\" in status:
            status = status.replace("\\", " ")
    except Exception as e:
        status = {}

    withheld_in_countries = user.withheld_in_countries if user.withheld_in_countries else r"\N"

    # Return list of attributes:
    return [
        user.id,
        name,
        screen_name,
        location,
        description,
        url,
        json.dumps(entities),
        user.protected,
        user.followers_count,
        user.friends_count,
        user.listed_count,
        user.created_at,
        user.favourites_count,
        user.verified,
        user.statuses_count,
        json.dumps(status),
        withheld_in_countries,
        datetime.datetime.now()
    ]


@log
def user_bytearray(users_set: set, ids_exist: bool = False) -> bytearray:
    users_bytearr = bytearray("", "utf-8")
    skipped = 0
    for user in users_set:
        attr_list = format_attributes(user)

        if ids_exist:
            attr_list.pop(0)
        
        # We set up a variable for the specific user
        # so that we can check for any problems that
        # might arise from fromatting errors related
        # to unicode or escape characters:
        user_bytearr = bytearray("", "utf-8")

        for idx, attr in enumerate(attr_list):
            # Each attribute represents a column, marked by tab. if last 
            # attribute of User, we want it marked with new-line char:
            if idx != len(attr_list) - 1:  # If not on last attribute:
                user_bytearr += bytearray(str(attr) + "\t", "utf-8")
            else:  # On last attribute:
                user_bytearr += bytearray(str(attr) + "\n", "utf-8")

        # Once we've created a bytearray for a specific user, we
        # double check the number of attributes before adding user 
        # to users_bytearr:
        if len(user_bytearr.decode().split("\t")) != 18:
            skipped += 1
            log_file = "./src/data/formatters_warning.log"
            log_setter(__name__, file_name=log_file)
            formatters_log = logging.getLogger(__name__)
            formatters_log.warning(f"Problem formatting user with twitter id \
                {user.id}. Skipped copying this user into database.")
        else:
            users_bytearr += user_bytearr            

    if skipped:
        print(f"Skipped {skipped} users. See formatters_log.log in the \
            data directory for details.")

    return users_bytearr
