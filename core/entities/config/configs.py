from typing import Optional
from dataclasses import dataclass

from omegaconf import MISSING


@ dataclass
class ClientSchema:
    session: str
    api_id: int
    api_hash: str
    phone: Optional[str] = MISSING
