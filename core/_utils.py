"""
methods for
    - channels loading (DB)
    - channels dumping (DB & raw)
    - 

utils.data.load_from_queue/tree/dev
utils.data.dump_raw
utils.data.put_into_db


"""
# import os
from datetime import date
from time import sleep
# from collections import namedtuple

# import telethon
# from telethon.sync import TelegramClient
# from telethon import functions, types
# from telethon.errors import (
#     ChannelPrivateError,
#     FloodWaitError,
#     RpcCallFailError,
#     RpcMcgetFailError,
#     UsernameInvalidError,
#     UsernameNotOccupiedError,
#     MsgIdInvalidError,
# )


def notify(client, message: str, user: str):
    """ send `message` (notification) to @user """
    client.send_message(user, message)



def is_channel(client, link: str) -> tuple:
    """ check if link is channel link and return indicator and channel_id """
    entity = client.get_input_entity(link).to_dict()
    if entity["_"] == "InputPeerChannel":
        return True, entity["channel_id"]
    return False, None

