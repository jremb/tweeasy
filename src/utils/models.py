import datetime
from typing import Optional, TypedDict, Any

from pydantic import BaseModel


class EntitiesModel(TypedDict):
    url: dict
    description: dict


class StatusModel(TypedDict):
    created_at: datetime.datetime
    id: int
    id_str: str
    text: str
    truncated: bool
    entities: dict
    source: str
    in_reply_to_status_id: int
    in_reply_to_status_id_str: str
    in_reply_to_user_id: int
    in_reply_to_user_id_str: str
    in_reply_to_screen_name: str
    geo: Optional[str]
    coordinates: Optional[str]
    place: Optional[str]
    contributors: Optional[str]
    is_quote_status: bool
    quoted_status_id: Optional[int]
    quoted_status_id_str: Optional[str]
    retweet_count: int
    favorite_count: int
    favorited: bool
    retweeted: bool
    possibly_sensitive: bool
    lang: str


class UserModel(BaseModel):
    id: int
    id_str: str
    name: str
    screen_name: str
    location: Optional[str]
    profile_location: Optional[dict]
    description: Optional[str]
    url: Optional[str]
    entities: EntitiesModel
    protected: bool
    followers_count: int
    friends_count: int
    listed_count: int
    created_at: datetime.datetime
    favourites_count: int
    utc_offset: Optional[str]
    time_zone: Optional[str]
    geo_enabled: Optional[str]
    verified: bool
    statuses_count: int
    lang: Optional[str]
    status: Optional[StatusModel]
    contributors_enabled: bool
    is_translator: bool
    is_translation_enabled: bool
    profile_background_color: Optional[str]
    profile_background_image_url: Optional[str]
    profile_background_image_url_https: Optional[str]
    profile_background_tile: Optional[bool]
    profile_image_url: Optional[str]
    profile_image_url_https: Optional[str]
    profile_banner_url: Optional[str]
    profile_link_color: Optional[str]
    profile_sidebar_border_color: Optional[str]
    profile_sidebar_fill_color: Optional[str]
    profile_text_color: Optional[str]
    profile_use_background_image: bool
    has_extended_profile: bool
    default_profile: bool
    default_profile_image: bool
    following: bool
    follow_request_sent: bool
    notifications: bool
    translator_type: Optional[str]
    withheld_in_countries: Optional[list]
