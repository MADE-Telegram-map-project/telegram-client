import json
import os
import random
from typing import Union, List, Set

import argparse
from urllib.parse import urlparse
from collections import namedtuple
import csv
import os
import logging

from psycopg2 import sql
from omegaconf import OmegaConf
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from core.entities import (
    FullChannelData, MediaChannelData, ChannelRelationData,
    UserData, MessageData, ReplyData, AppConfig
)
from core.db_seed.db import (
    ChannelQueue, Channels, Messages, UserChannel, ChannelRelation, Replies
)

STATUSES = {'ok', 'error', 'processing', 'to_process'}


def _load_channel(idx: int) -> Union[int, str]:
    """ load channel from queue """
    my_channels = [
        "gagaga_momomo121", "gagaga_momomo", "gudim_public", 1149710531, None]
    return my_channels[idx]


def save_header(
        full_data: FullChannelData, media: MediaChannelData, session_cls: Session):
    """ add channel header (full + media) to db """
    with session_cls() as session:
        record = session.query(Channels).filter(
            Channels.channel_id == full_data.channel_id).first()
        if record is None:
            session.add(Channels(
                channel_id=full_data.channel_id,
                title=full_data.title,
                link=full_data.username,
                about=full_data.about,
                date=full_data.date,
                participants_count=full_data.participants_count,
                total_photos=media.photo,
                total_video=media.video,
                total_document=media.document,
                total_music=media.music,
                total_url=media.url,
                total_gif=media.gif,
                total_voice=media.voice,
            ))
            session.commit()
    return


def save_users(users: List[UserData], session_cls: Session):
    """ add new user-channel links to db """
    with session_cls() as session:
        for user in users:
            record = session.query(UserChannel).filter(
                UserChannel.user_id == user.user_id,
                UserChannel.channel_id == user.channel_id,
            ).first()
            if record is None:
                session.add(UserChannel(
                    channel_id=user.channel_id,
                    user_id=user.user_id,
                    is_bot=user.bot,
                    username=user.username,
                ))
                session.commit()
    return


def save_messages(messages: List[MessageData], session_cls: Session):
    """ add channel messages to db """
    with session_cls() as session:
        for msg in messages:
            record = session.query(Messages).filter(
                Messages.message_id == msg.message_id,
                Messages.channel_id == msg.channel_id,
            ).first()
            if record is None:
                session.add(Messages(
                    message_id=msg.message_id,
                    channel_id=msg.channel_id,
                    message=msg.message,
                    date=msg.date,
                    views=msg.views,
                    forwards=msg.forwards,
                    replies_cnt=msg.replies_cnt,
                    fwd_from_channel_id=msg.fwd_channel_id,
                    fwd_from_message_id=msg.fwd_message_id,
                ))
                session.commit()
    return


def save_replies(replies: List[ReplyData], session_cls: Session):
    """ add message replies to db """
    with session_cls() as session:
        for rlp in replies:
            record = session.query(Replies).filter(
                    Replies.id == rlp.id,
                    Replies.message_id == rlp.message_id,
                    Replies.channel_id == rlp.channel_id,
                ).first()
            if record is None:
                session.add(Replies(
                    id=rlp.id,
                    message_id=rlp.message_id,
                    channel_id=rlp.channel_id,
                    message=rlp.message,
                    date=rlp.date,
                    user_id=rlp.user_id,
                ))
                session.commit()
    return


def save_relations(relations: List[ChannelRelationData], session_cls: Session):
    """ add channel usernames to queue & add pair of connected channels to db """
    with session_cls() as session:
        for rel in relations:
            record = session.query(ChannelRelation).filter(
                    ChannelRelation.from_channel_id == rel.from_channel_id,
                    ChannelRelation.to_channel_link == rel.to_channel_link,
                    ChannelRelation.to_channel_id == rel.to_channel_id,
                ).first()
            if record is None:
                session.add(ChannelRelation(
                    from_channel_id=rel.from_channel_id,
                    to_channel_link=rel.to_channel_link,
                    to_channel_id=rel.to_channel_id,
                    link_type=rel.type,
                ))
                session.commit()

            if rel.to_channel_link is None:
                # db queue only for links (usernames)
                continue

            record = session.query(ChannelQueue).filter(
                ChannelQueue.channel_link == rel.to_channel_link).first()
            if record is None:
                session.add(ChannelQueue(
                    channel_link=rel.to_channel_link, status="to_process"))
                session.commit()
    return


def send_status_to_queue(username: str, status: str, session_cls: Session):
    """ if username is in db, change status, else add new record """
    assert status in STATUSES, "such status {} is not allowable".format(status)
    with session_cls() as session:
        record = session.query(ChannelQueue).filter(
                ChannelQueue.channel_link == username).first()
        if record is not None:
            session.query(ChannelQueue)\
                    .filter(ChannelQueue.channel_link == username)\
                    .update({"status": status})
        else:
            session.add(ChannelQueue(channel_link=username, status=status))
        session.commit()
    

def is_done(username: str, session_cls: Session) -> bool:
    with session_cls() as session:
        record = session.query(ChannelQueue).filter(
                ChannelQueue.channel_link == username,
                ChannelQueue.status.in_(["ok", "error"])).first()
        if record is not None:
            return True
    return False


def is_ready_to_process(username: str, session_cls: Session) -> bool:
    return not is_done(username, session_cls)
