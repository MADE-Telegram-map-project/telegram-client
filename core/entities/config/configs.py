from typing import Optional
from dataclasses import dataclass, field

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
class MessageBrokerConfigSchema:
    input_queue: str = MISSING
    input_durable: bool = field(default=True)
    user: str = MISSING
    passwd: str = MISSING
    host: str = MISSING
    port: int = MISSING
    auto_ack: bool = False
    heartbeat: Optional[int] = 0
    sleep_timeout_in_sec: int = 3


@dataclass
class AppConfig:
    client_config: ClientConfigSchema = MISSING
    message_broker: MessageBrokerConfigSchema = MISSING
    database: DbConfigSchema = MISSING
