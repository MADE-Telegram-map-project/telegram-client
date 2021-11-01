import datetime
# from collections import namedtuple
from dataclasses import dataclass
from typing import Union

from telethon.tl.types import MessageReplies


@dataclass
class FullChannelData:
    channel_id: int
    title: str
    link: str
    about: str
    date: datetime.datetime
    participants_count: int
    linked_chat_id: Union[int, None]


@dataclass
class MediaChannelData:
    photo: int
    video: int
    document: int
    music: int
    url: int
    voice: int
    gif: int


@dataclass
class UserData:
    channel_id: int
    user_id: int
    bot: bool
    username: str


@dataclass
class MessageData:
    message_id: int
    channel_id: int
    message: str
    date: datetime.datetime
    views: int
    forwards: int
    replies_cnt: int
    fwd_channel_id: int
    fwd_message_id: int
    replies: MessageReplies = None


@dataclass
class ReplyData:
    message_id: int
    channel_id: int
    message: str
    date: datetime.datetime
    user_id: int


# FullChannelData = namedtuple(
#     "FullChannelData",
#     ("channel_id", "title", "link", "about", "date", "participants_count")
# )

# MediaChannelData = namedtuple(
#     "MediaChannelData",
#     ("photo", "video", "document", "music", "url", "voice", "gif")
# )
# UserData = namedtuple("UserData", ("user_id", "bot", "username"))
# MessageData = namedtuple(
#     "MessageData", (
#         "message_id",
#         "text",
#         "date",
#         "views",
#         "forwards",
#         "replies_cnt",
#         "fwd_channel_id",
#         "fwd_message_id",
#         "replies",
#     )
# )
