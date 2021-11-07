from sqlalchemy import Column, Integer, Text, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from .base import Base
from .channels import Channels
from .replies import Replies


class Messages(Base):
    __tablename__ = "Messages"

    message_id = Column("message_id", BigInteger, primary_key=True)
    channel_id = Column("channel_id", ForeignKey(
        f"{Channels.__tablename__}.channel_id"), primary_key=True)
    message = Column("message", Text, nullable=False)
    date = Column("date", DateTime(timezone=True), nullable=False)
    views = Column("views", Integer, nullable=False)
    forwards = Column("forwards", Integer, nullable=False)
    replies_cnt = Column("replies_cnt", Integer, nullable=False, default=0)
    fwd_from_channel_id = Column("fwd_from_channel_id", BigInteger, nullable=True)
    fwd_from_message_id = Column("fwd_from_message_id", BigInteger, nullable=True)
    replies = relationship(
        Replies, primaryjoin=f"and_({Replies.__tablename__}.channel_id == Messages.channel_id, {Replies.__tablename__}.message_id == Messages.message_id)")
