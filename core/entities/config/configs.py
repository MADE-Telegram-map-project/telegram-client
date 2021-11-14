from typing import Optional
from dataclasses import dataclass

from omegaconf import MISSING


@ dataclass
class ClientConfigSchema:
    session: str
    api_id: int
    api_hash: str
    phone: Optional[str] = MISSING


@dataclass
class DbConfigSchema:
    user: str = MISSING
    passw: str = MISSING
    host: str = MISSING
    port: int = MISSING
    db_url: str = MISSING


@dataclass
class AppConfig:
    client_config: ClientConfigSchema = MISSING
    database: DbConfigSchema = MISSING
