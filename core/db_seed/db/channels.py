from sqlalchemy import Column, Integer, Text, DateTime, BigInteger
from sqlalchemy.orm import relationship

from .base import Base
from .user_channel import UserChannel


class Channels(Base):
    __tablename__ = "Channels"

    channel_id = Column("channel_id", BigInteger, primary_key=True)
    title = Column("text", Text, nullable=False)
    link = Column("link", Text, nullable=False)
    about = Column("about", Text, nullable=False)
    date = Column("date", DateTime(timezone=True), nullable=False)
    participants_count = Column("participants_count", Integer, nullable=False, default=0)
    total_photos = Column("total_photos", Integer, nullable=False, default=0)
    total_video = Column("total_video", Integer, nullable=False, default=0)
    total_document = Column("total_document", Integer, nullable=False, default=0)
    total_music = Column("total_music", Integer, nullable=False, default=0)
    total_url = Column("total_url", Integer, nullable=False, default=0)
    total_gif = Column("total_gif", Integer, nullable=False, default=0)
    total_voice = Column("total_voice", Integer, nullable=False, default=0)

    usesr = relationship(UserChannel)
    messsages = relationship("Messages")
