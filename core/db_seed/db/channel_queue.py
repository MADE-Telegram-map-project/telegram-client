from typing import Text
from sqlalchemy import Column, Enum, Text, Integer
from sqlalchemy.dialects import postgresql

from .base import Base


class ChannelQueue(Base):
    __tablename__ = "ChannelQueue"
    id_col = Column("queue_id", Integer, autoincrement=True, primary_key=True)
    channel_link = Column("link", Text, primary_key=True, unique=True, nullable=True)
    channel_id = Column("channel_id", Text, primary_key=True, unique=True, nullable=True)
    status = Column(Enum("ok", "error", "processing", "to_process"), default="to_process")
