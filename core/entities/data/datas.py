from collections import namedtuple

FullChannelData = namedtuple(
    "FullChannelData", 
    ("channel_id", "title", "link", "about", "date", "participants_count")
)
MediaChannelData = namedtuple(
    "MediaChannelData", 
    ("photo", "video", "document", "music", "url", "voice", "gif")
)
UserData = namedtuple("UserData", ("user_id", "bot", "username"))
MessageData = namedtuple(
    "MessageData", (
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
