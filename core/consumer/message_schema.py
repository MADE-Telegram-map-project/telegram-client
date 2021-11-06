import enum
from dataclasses import dataclass
from typing import Optional


class ProcessingStatus(enum.IntEnum):
    SUCCESS = enum.auto()
    FAIL = enum.auto()
    FAIL_NEED_REQUEUE = enum.auto()


@dataclass
class ProcessingResult:
    data: Optional[dict]
    status: ProcessingStatus
