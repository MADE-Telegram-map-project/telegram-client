import json
import os
import random
from typing import Union

from core.entities import (
    FullChannelData, MediaChannelData,
    UserData, MessageData, ReplyData,
)


def load_channel(idx: int) -> Union[int, str]:
    """ load channel from queue """
    my_channels = [
        "gagaga_momomo121", "gagaga_momomo", "gudim_public", 1149710531, None]
    return my_channels[idx]


def is_processed(channel) -> bool:
    """ check if channel marked as ok, processing or error in BD """
    # TODO connection to DB
    return False


def mark_as_processing(channel: int):
    """ send mark 'processing' for channel to DB """
    pass


def mark_as_error(channel):
    """ send mark 'error' for channel to DB """
    pass


def mark_as_ok(channel):
    """ send mark 'ok' for channel to DB """
    pass 


def save_to_db(obj):
    pass
