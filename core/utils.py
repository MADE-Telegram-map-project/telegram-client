"""
methods for
    - channels loading (DB)
    - channels dumping (DB)
    - base crawling functions without Exceptions handling ??
    - 

utils.data.load_from_queue/tree/dev
utils.data.dump_raw
utils.data.put_into_db

utils.parsing.get_header_media_counts
utils.parsing.get_commenters
utils.parsing.get_messages
utils.parsing.get_channel_full
utils.parsing.get_channel_id

"""
import os
from datetime import date
from collections import namedtuple

import telethon
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import (
    GetSearchCountersRequest, 
    GetRepliesRequest
)

# https://t.me/latinapopacanski

FullChannelData = namedtuple(
    "FullChannelData", 
    ("channel_id", "title", "link", "about", "date", "participants_count")
)
MediaChannelData = namedtuple(
    "MediaChannelData", 
    ("photo", "video", "document", "music", "url", "voice", "gif")
)
UserData = namedtuple("UserData", ("user_id", "bot", "username"))
Message_Data = namedtuple(
    "Message_Data", 
    (
        "message_id", 
        "id", 
        "text", 
        "date", 
        "views",
        "forwards",
        "replies_cnt", 
        "fwd_channel_id", 
        "fwd_message_id",
        "replies",
    )
)


MEDIA_FILTERS = [
    types.InputMessagesFilterPhotos(), 
    types.InputMessagesFilterVideo(),
    types.InputMessagesFilterDocument(),
    types.InputMessagesFilterMusic(),
    types.InputMessagesFilterUrl(),
    types.InputMessagesFilterVoice(),
    types.InputMessagesFilterGif(),
]
MEDIA_NAMES = [
    "Photos",
    "Video",
    "Document",
    "Music",
    "Url",
    "Voice",
    "Gif",
]


def get_header_media_counts(client, peer):
    """https://tl.telethon.dev/methods/messages/get_search_counters.html"""
    search_res = client(GetSearchCountersRequest(
            peer='latinapopacanski', filters=MEDIA_FILTERS,
    ))
    counts = [x.count for x in search_res]
    media = {m: cnt for m, cnt in zip(MEDIA_NAMES, counts)}
    return media


def get_commenters(client, channel_peer, message_id):
    comments = client(GetRepliesRequest(
        peer=channel_peer, 
        msg_id=message_id, 
        offset_id=0, 
        offset_date=None, 
        add_offset=0,
        limit=0,
        max_id=0,
        min_id=0,
        hash=0,
    ))
    commenters = [(x.id, x.bot, x.username) for x in comments.users]
    
    # TODO add comment text

    return commenters


def get_messages(client: TelegramClient, channel_name: str):
    client.get_messages(channel_name)


def get_channel_full(client, channel_name: str):
    full = client(GetFullChannelRequest(channel=channel_name))
    # print(full.stringify())
    data = {
        "id": full.full_chat.id,
        "name": full.chats[0].username,
        "about": full.full_chat.about,
        "date": full.chats[0].date,
        # TODO
    }
    return data


def notify(client, message: str, user: str):
    """ send `message` (notification) to @user """
    client.send_message(user, message)


def dump_to_json(obj):
    assert "to_json" in dir(obj)
    pass


def get_channel_id(client, channel_link: str) -> int:
    """ get id of @channel_link """
    if isinstance(channel_link, str):
        channel_link = channel_link.lstrip("@")
    
    full = client(GetFullChannelRequest(channel=channel_link))
    print(full.stringify())
    return full.full_chat.id


def is_channel(client, link: str) -> tuple:
    """ check if link is channel link and return indicator and channel_id """
    entity = client.get_input_entity(link).to_dict()
    if entity["_"] == "InputPeerChannel":
        return True, entity["channel_id"]
    return False, None


api_id: int = os.environ["API_ID"]
api_hash: str = os.environ["API_HASH"]

name = 'client1'
client: TelegramClient = None

# ch = 19534473280
# ch = "breakingmash"
ch = "latinapopacanski"  # 1149710531
message_id = 2563

with TelegramClient(name, api_id, api_hash) as client:
    # d = get_header_media_counts(client, ch)
    # print(d)
    # print(type(client))
    get_commenters(client, ch, message_id)


    # full = get_channel_full(client, ch)
    # print(full)

    # print(client.get_input_entity(ch))

    # client.get_entity(1117628569).to_json() # альтернатива получению всей инфы


    # print(get_channel_id(client, ch))
# 1232476793

