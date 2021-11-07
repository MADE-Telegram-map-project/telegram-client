from sqlalchemy import Column, BigInteger, ForeignKey, Text
from sqlalchemy.sql.sqltypes import DateTime

from .base import Base


class Replies(Base):
    __tablename__ = "Replies"
    id = Column("id", BigInteger, primary_key=True)
    message_id = Column("message_id", BigInteger, ForeignKey(
        "Messages.message_id"))
    channel_id = Column("channel_id", BigInteger, ForeignKey(
        "Messages.channel_id"))
    message = Column("message", Text, nullable=False)
    date = Column("date", DateTime(timezone=True), nullable=False)
    user_id = Column(BigInteger, nullable=False)
