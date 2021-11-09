import datetime
from dataclasses import dataclass
from typing import Union

from telethon.tl.types import MessageReplies


@dataclass
class FullChannelData:
    channel_id: int
    title: str
    username: str
    about: str
    date: datetime.datetime
    participants_count: int
    linked_chat_id: Union[int, None]


@dataclass
class MediaChannelData:
    photo: int = 0
    video: int = 0
    document: int = 0
    music: int = 0
    url: int = 0
    voice: int = 0
    gif: int = 0


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
    fwd_channel_id: Union[int, None]
    fwd_message_id: Union[int, None]
    replies: Union[MessageReplies, None] = None


@dataclass
class ReplyData:
    id: int
    message_id: int
    channel_id: int
    message: str
    date: datetime.datetime
    user_id: int


@dataclass
class ChannelRelationData:
    from_channel_id: int
    to_channel_link: Union[str, None] = None
    to_channel_id: Union[int, None] = None
