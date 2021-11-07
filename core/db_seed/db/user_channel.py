from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy import Column, BigInteger, ForeignKey, Text

from .base import Base


class UserChannel(Base):
    __tablename__ = "UserChannel"
    channel_id = Column("channel_id", ForeignKey(
        "Channels.channel_id"), primary_key=True)
    user_id = Column("user_id", BigInteger, primary_key=True)
    is_bot = Column("is_bot", Boolean, default=False)
    username = Column("username", Text, nullable=True)
