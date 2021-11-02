


def load_channel() -> int:
    """ load channel from queue """
    return 0


def is_processed(channel) -> bool:
    """ check if channel marked completed or raised in BD """
    # TODO connection to DB
    return False


def mark_as_processing(channel: int):
    """ send mark 'processing' to DB """
    pass


def mark_as_error(channel):
    """ send mark 'error' to DB """
    pass


def mark_as_ok(channel):
    """ send mark 'ok' to DB """
    pass 


def save_to_json(obj):
    assert "to_json" in dir(obj)
    # TODO dump raw files


def save_to_db(obj):
    pass
