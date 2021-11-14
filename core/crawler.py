import getpass
import json
import logging
import logging.config
import os
import random
from queue import Queue
from datetime import date, datetime
from time import sleep, time
from typing import List, Tuple, Union, Set
from sqlalchemy.sql.functions import user

import yaml
from sqlalchemy.orm import relation, sessionmaker, Session
from sqlalchemy import create_engine
from telethon import types
from telethon.errors import MsgIdInvalidError, SessionPasswordNeededError
from telethon.helpers import TotalList
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import (GetRepliesRequest,
                                            GetSearchCountersRequest)
from telethon.tl.types import InputPeerChannel, PeerChannel, TLObject
from telethon.tl.types.messages import ChannelMessages, ChatFull, SearchCounter

from core.entities import (AppConfig, FullChannelData, MediaChannelData,
                           MessageData, ReplyData, UserData, ProcessingStatus)
from core.utils import (
    cool_exceptor,
    extract_usernames,
    save_header,
    save_users,
    save_messages,
    save_relations,
    send_status_to_queue,
    is_done,
    get_channel_from_db
)


class Crawler():
    '''
    this is the main class responsible for obtaining data from telegram

    each method get_* do "one" query to api

    '''
    min_participants_count = 5000
    messages_limit = 500
    min_delay = 20
    max_delay = 60
    qcutoff = 0.5  # frequency of using of local queue
    max_passes_num = 50
    media_filters = [
        types.InputMessagesFilterPhotos(),
        types.InputMessagesFilterVideo(),
        types.InputMessagesFilterDocument(),
        types.InputMessagesFilterMusic(),
        types.InputMessagesFilterUrl(),
        types.InputMessagesFilterVoice(),
        types.InputMessagesFilterGif(),
    ]

    def __init__(
            self,
            config: AppConfig,
            activate_logging=True,
            logging_config_path="configs/logger_config.yml",
            dump_path="data/raw",
    ):
        '''
        read config values, create logger and
        authorize the client if necessary
        '''
        self.logging_config_path = logging_config_path
        self.logger = logging.getLogger("client")
        if activate_logging:
            self.__init_logging()
        self.logger.debug("*** New run *** {}".format(config.client_config.session))

        self.config = config
        self.client = self.__authorize()
        self.dump_path = dump_path
        self.successful = 0
        self.chat_member = False
        engine = create_engine(self.config.database.db_url)
        engine_ser = engine.execution_options(isolation_level='SERIALIZABLE')
        self.db_session_cls = sessionmaker(bind=engine)
        self.db_session_cls_ser = sessionmaker(bind=engine_ser)
        self.local_queue = Queue()
        # self.local_queue.put(1149710531)

    def __authorize(self):
        client = TelegramClient(
            self.config.client_config.session,
            self.config.client_config.api_id,
            self.config.client_config.api_hash,
        )
        client.connect()

        if client.is_user_authorized():
            return client

        client.sign_in(self.config.client_config.phone)
        try:
            client.sign_in(code=input('Enter code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=getpass.getpass())
        self.logger.debug("Authorized")
        return client

    def __init_logging(self):
        with open(self.logging_config_path) as config_fin:
            config = yaml.safe_load(config_fin)
            logging.config.dictConfig(config)

    def end_parsing(self):
        stop_message = "Crawling done, successful calls: {}".format(self.successful)
        self.logger.critical(stop_message)
        self.notify(stop_message)

    def crawl(self):
        self.wait(random.randint(0, 15))  # random initiation for clients
        n_passes = 0
        while n_passes < self.max_passes_num:
            try:
                if not self.local_queue.empty() and random.random() > self.qcutoff:
                    username = self.local_queue.get()
                    self.logger.info("Got channel id {} from local queue".format(username))
                else:
                    username = get_channel_from_db(self.db_session_cls_ser)
                    if username is None:
                        n_passes += 1
                        self.logger.warn("There are no usernames to process in db")
                        continue

                    self.logger.info("Got username {} from db".format(username))

                channel_username, status = self.parse_channel(username)
                if status == ProcessingStatus.SUCCESS:
                    n_passes = 0
                    send_status_to_queue(
                        channel_username, "ok", self.db_session_cls)
                    self.logger.debug("Sent 'ok' to db-queue")
                elif status == ProcessingStatus.FAIL:
                    n_passes = 0
                    send_status_to_queue(
                        channel_username, "error", self.db_session_cls)
                    self.logger.debug("Sent 'error' to db-queue")

                self.logger.debug("Channel {} processed with {}"
                                .format(channel_username, str(status)))
            
            except Exception as e:
                self.logger.critical("Global error: {}".format(repr(e)))
                self.notify(repr(e))
        self.end_parsing()

    def parse_channel(
            self, channel: Union[int, str]) -> Tuple[str, ProcessingStatus]:
        ''' that is the main method responsible for the parse of the messages
            TODO: complete the description
            TODO add notify to critical errors
        '''
        is_inner_processing = isinstance(channel, int)
        try:
            start_time = time()
            self.logger.debug("Started iteration for {}".format(channel))

            ########## FULL ##########
            self.logger.debug("Run channel full extraction")
            full_data = self.get_channel_full(channel)
            if full_data is None:
                self.logger.warn("Cannot get channel full; go to next chanel")
                delay = self.get_request_delay() * 2
                self.wait(delay)
                if is_inner_processing:
                    return channel, ProcessingStatus.PASS
                return channel, ProcessingStatus.FAIL
            else:
                full_data, full_data_raw = full_data
                channel_id = full_data.channel_id
                username = full_data.username
                self.logger.info("Got channel full - username: {}, id: {}"
                                 .format(username, channel_id))

                if is_inner_processing:
                    if is_done(username, self.db_session_cls):
                        self.logger.info("Channel from inner queue is already done")
                        delay = self.get_request_delay() * 2
                        self.wait(delay)
                        return username, ProcessingStatus.PASS
                    else:
                        send_status_to_queue(username, "processing", self.db_session_cls)
                        self.logger.debug("Set status 'processing' to channel from inner queue")

                self.save_to_json(full_data_raw, "full", channel_id)

            self.wait()
            _pc = full_data.participants_count
            if _pc < self.min_participants_count:
                self.logger.info(
                    'Small channel, {} participants, pass it'.format(_pc))
                delay = self.get_request_delay() * 2
                self.wait(delay)
                return username, ProcessingStatus.FAIL

            ########## MEDIA ##########
            self.logger.debug('Run channel media counts extraction')
            media_data = self.get_header_media_counts(channel_id)
            if media_data is None:
                self.logger.error("Cannot get channel media counts, continue crawling")
                media_data = (MediaChannelData(), None)  # default zeros
            else:
                self.logger.debug("Media counts extracted")
                media_data, media_data_raw = media_data
                self.save_to_json(media_data_raw, "media", channel_id)

            save_header(full_data, media_data, self.db_session_cls)
            self.logger.debug("Header saved to db")
            self.wait()

            ########## CHAT ##########
            chat_users = []
            if full_data.linked_chat_id is not None:
                self.logger.debug("Extract linked chat (id={}) users"
                                  .format(full_data.linked_chat_id))
                chat_users = self.get_linked_chat_members(
                    channel_id, full_data.linked_chat_id)
                if chat_users is None:
                    self.logger.error("Cannot get linked chat users, continue crawling")
                else:
                    self.logger.debug("{} users extracted from linked chat"
                                      .format(len(chat_users[0])))
                    chat_users, chat_users_raw = chat_users
                    self.save_to_json(
                        chat_users_raw, "linked_chat", channel_id)
                    save_users(chat_users, self.db_session_cls)
                    self.logger.debug("Linked chat users saved to db")
                self.wait()
            else:
                self.logger.debug("There are no linked chat")

            ########## MESSAGES ##########
            self.logger.debug("Start retrieving of messages from channel")
            messages = self.get_messages(channel_id)
            if messages is None:
                self.logger.error("Cannot retrieve channel messages, continue crawling")
            else:
                self.logger.debug("Retrieved {} messages".format(
                    len(messages[0])))
                messages, messages_raw = messages
                self.save_to_json(messages_raw, "messages", channel_id)
                save_messages(messages, self.db_session_cls)
                self.logger.debug("Messages saved to db and drive")

            ########## NEW CHANNELS ##########
            self.logger.debug(
                "Start extraction of new usernames from messages and about")
            relations, nhead, ndirect, nfwd = extract_usernames(
                channel_id, full_data.about, messages_raw)
            self.logger.debug("Extracted {} new head usernames".format(nhead))
            self.logger.debug("Extracted {} new direct usernames".format(ndirect))
            self.logger.debug("Extracted {} new fwd channel ids".format(nfwd))
            for rel in relations:
                if rel.type == "forward":
                    self.local_queue.put(rel.to_channel_id)
            self.logger.debug("Fwd channel ids put to local queue")

            save_relations(relations, self.db_session_cls)
            self.logger.debug("Relations saved to db and usernames added to queue")

            self.successful += 1
            spent_time = time() - start_time
            self.logger.info("Channel {} done in {:.2f} seconds".format(
                username, spent_time))
            self.wait()
            return username, ProcessingStatus.SUCCESS

        except Exception as e:
            error_msg = repr(e)
            self.logger.critical(error_msg)
            self.notify(error_msg)
            return username, ProcessingStatus.FAIL

    @cool_exceptor
    def get_channel_full(
            self,
            channel: Union[str, int]) -> Tuple[FullChannelData, ChatFull]:
        """ channel is link or id"""
        full = self.client(GetFullChannelRequest(channel=channel))
        header = full.chats[0]
        linked_chat_id = full.full_chat.linked_chat_id

        data = FullChannelData(
            channel_id=header.id,
            title=header.title,
            username=header.username,
            about=full.full_chat.about or "",
            date=header.date,
            participants_count=full.full_chat.participants_count or 0,
            linked_chat_id=linked_chat_id,
        )
        return data, full

    @cool_exceptor
    def get_linked_chat_members(
            self, channel_id: int,
            chat_id: int) -> Tuple[List[UserData], TotalList]:
        chat_members = self.client.get_participants(chat_id)
        data = [UserData(channel_id, x.id, x.bot or False, x.username)
                for x in chat_members]
        return data, chat_members

    @cool_exceptor
    def get_header_media_counts(
            self,
            channel_id: int) -> Tuple[MediaChannelData, List[SearchCounter]]:
        """https://tl.telethon.dev/methods/messages/get_search_counters.html"""
        search_res = self.client(GetSearchCountersRequest(
            peer=channel_id, filters=self.media_filters,
        ))
        counts = [x.count for x in search_res]
        data = MediaChannelData(*counts)
        return data, search_res

    @cool_exceptor
    def get_messages(
            self,
            channel_id: int,
            limit: int = None) -> Tuple[List[MessageData], TotalList]:
        """ return collected messages from oldest to newest

        we can collect MessageReplies and release from them short info
        about commenters : List[PeerUser(user_id: int)]
        """
        limit = limit or self.messages_limit
        limit = max(limit, 55) + random.randint(-50, 50)  # some stochastics
        messages = self.client.get_messages(entity=channel_id, limit=limit)
        data = []
        for msg in messages:
            replies = msg.replies
            replies_cnt = 0
            if replies is not None:
                # old messages has no replies object (only None)
                replies_cnt = replies.replies
            if msg.fwd_from is None:
                fwd_channel_id = None
                fwd_message_id = None
            else:
                if isinstance(msg.fwd_from.from_id, PeerChannel):
                    fwd_channel_id = msg.fwd_from.from_id.channel_id
                else:
                    fwd_channel_id = None
                fwd_message_id = msg.fwd_from.channel_post

            cur_message_data = MessageData(
                message_id=msg.id,
                channel_id=msg.peer_id.channel_id,
                message=msg.raw_text or "",  # text maybe?
                date=msg.date,
                views=msg.views or 0,
                forwards=msg.forwards or 0,
                replies_cnt=replies_cnt or 0,
                fwd_channel_id=fwd_channel_id,
                fwd_message_id=fwd_message_id,
                replies=replies,
            )
            data.append(cur_message_data)
        return data, messages

    @cool_exceptor
    def get_replies(
        self,
        channel_id: int,
        message_id: int,
    ) -> Tuple[List[ReplyData], List[UserData], ChannelMessages]:
        """ run only if message has replies obj OR if replies_cnt > 0 """
        try:
            comments = self.client(GetRepliesRequest(
                peer=channel_id,
                msg_id=message_id,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=0,
                max_id=0,
                min_id=0,
                hash=0,
            ))
        except MsgIdInvalidError as e:
            self.logger.error("Cannot get replies: {}".format(repr(e)))
            return [], []
        except Exception as e:
            raise e

        commenters = [UserData(channel_id, x.id, x.bot, x.username)
                      for x in comments.users]
        replies = [
            ReplyData(
                message_id=message_id,  # id of the message, not the reply
                channel_id=channel_id,
                message=msg.message or "",
                date=msg.date,
                user_id=msg.from_id.user_id)
            for msg in comments.messages]

        return replies, commenters, comments

    def save_to_json(
            self, obj: Union[TLObject, TotalList],
            label: str, channel_id: int):
        """ dump TLObject inheritor to file

        params:
            - label: {"full", "linked_chat", "media", "messages", "replies"}
        """
        assert isinstance(channel_id, int), "channel_id must be integer"
        if not os.path.exists(self.dump_path):
            os.mkdir(self.dump_path)

        channel_path = os.path.join(self.dump_path, str(channel_id))
        if not os.path.exists(channel_path):
            os.mkdir(channel_path)

        filepath = os.path.join(channel_path, "{}.json".format(label))
        with open(filepath, "w") as fp:
            if label == "full":
                obj.to_json(fp, ensure_ascii=False)

            elif label in {"messages", "linked_chat", "media"}:
                new_obj = [msg.to_dict() for msg in obj]
                json.dump(
                    new_obj, fp, default=self.json_serial, ensure_ascii=False)

            elif label == "replies":
                new_obj = [msg.to_dict() for msg in obj]
                # with open(filepath) as fp:
                #     json.dump(new_obj, fp, ensure_ascii=False)
                # TODO dump replies, in "replies/meddage_id.json"
                # need to pass meddage_id into this function
            else:
                raise ValueError("label '{}' unsupported")
        self.logger.debug(
            "{} dumped in {}".format(label.capitalize(), filepath))

    def is_channel(self, link: str) -> Tuple[bool, Union[None, int]]:
        """ check if link is channel link; return indicator and channel_id """
        try:
            entity = self.client.get_input_entity(link)
            if isinstance(entity, InputPeerChannel):
                return True, entity.channel_id
        except ValueError as e:
            self.logger.debug(repr(e))
        except Exception as e:
            self.logger.error(repr(e))
        return False, None

    def notify(self, message: str, chat="telemap_ctitical"):
        """ send `message` (notification) to chat """
        try:
            if not self.chat_member:
                self.chat_member = True
                self.client(JoinChannelRequest(chat))
                self.logger.debug("Joined to chat")

            self.client.send_message(chat, message)
            self.logger.debug("Sent message '{}' to chat".format(message))
        except:
            self.logger.debug("Cannot send notification to chat")

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return "here we some bytes"
        raise TypeError("Type %s not serializable" % type(obj))

    def get_request_delay(self):
        ''' we need to set up a delay between requests,
        it must be a random number '''
        delay_time = random.randint(self.min_delay, self.max_delay)
        return delay_time

    def wait(self, delay: int = None, to_log=True):
        delay = delay or self.get_request_delay()
        if to_log:
            self.logger.debug('Going to sleep for {} sec'.format(str(delay)))
        sleep(delay)
