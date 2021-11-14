import enum


class ProcessingStatus(enum.IntEnum):
    SUCCESS = enum.auto()
    FAIL = enum.auto()
    PASS = enum.auto()
