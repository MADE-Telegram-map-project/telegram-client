from typing import Text
from sqlalchemy import Column, Text, Integer, Enum

from .base import Base


class ChannelRelation(Base):
    __tablename__ = "ChannelRelation"
    id_col = Column("rel_id", Integer, autoincrement=True, primary_key=True)
    from_channel_id = Column("from_channel_id", Integer, nullable=False)
    to_channel_link = Column("to_channel_link", Text, nullable=True)
    to_channel_id = Column("to_channel_id", Integer, nullable=True)
    link_type = Column(Enum("direct", "forward", "header"))
