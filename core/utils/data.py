import json
import os
import random
from typing import Union


def load_channel() -> Union[int, str]:
    """ load channel from queue """
    my_channels = [1149710531, "gagaga_momomo"]
    return random.sample(my_channels, 1)[0]


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
