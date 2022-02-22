############################################################
# Contains our credential getter functions and the
# decorator functions for the Twitter api.
#
# It is assumed that credentials are set via environment
# variables.
############################################################
import os
import tweepy
from rich.console import Console

# Create rich console instance:
console = Console()


def twitter_credentials() -> dict:
    """Dictionary of the parameters required to
    connect to the Twitter API. You'll need to have
    set the credentials as environment variables.
    :return: dictionary of credentials."""
    return {
        "bearer": os.environ["TWITTER_API_BEARER"],
        "cons_key": os.environ["CONSUMER_KEY"],
        "cons_sec": os.environ["CONSUMER_SECRET"],
        "acc_token": os.environ["ACCESS_TOKEN"],
        "acc_sec": os.environ["ACCESS_SECRET"],
    }


def with_api1_connection(func):
    """Decorator for handling Twitter API v1 connection"""
    params = twitter_credentials()

    def wrapper(*args, **kwargs):
        auth = tweepy.OAuthHandler(params["cons_key"], params["cons_sec"])
        auth.set_access_token(params["acc_token"], params["acc_sec"])
        api = tweepy.API(
            auth,
            retry_count=5,
            retry_delay=60,
            retry_errors=[500, 503],
            wait_on_rate_limit=True)
        try:
            res = func(api, *args, **kwargs)
            return res
        except Exception as e:
            console.log(e)

    return wrapper


def with_api2_connection(func):
    """Decorator for handling Twitter API v2 connection"""
    params = twitter_credentials()

    def wrapper(self, *args, **kwargs):
        client = tweepy.Client(params["bearer"], wait_on_rate_limit=True)
        try:
            res = func(client, *args, **kwargs)
        except Exception as e:
            console.log(e)
        return res

    return wrapper
