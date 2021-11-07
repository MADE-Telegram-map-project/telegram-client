import json
import logging
import logging.config
import os
import random
from datetime import date, datetime
from time import sleep, time
from typing import List, Tuple, Union

import yaml
from omegaconf import OmegaConf
from telethon import types
from telethon.errors import MsgIdInvalidError
from telethon.helpers import TotalList
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import (GetRepliesRequest,
                                            GetSearchCountersRequest)
from telethon.tl.types import InputPeerChannel, PeerChannel, TLObject
from telethon.tl.types.messages import ChannelMessages, ChatFull, SearchCounter

from core.entities import (AppConfig, FullChannelData,
                           MediaChannelData, MessageData, ReplyData, UserData)
from core.utils import (cool_exceptor, extract_usernames, is_processed,
                        load_channel, mark_as_error, mark_as_ok,
                        mark_as_processing)


class Crawler():
    '''
    this is the main class responsible for obtaining data from telegram

    each method get_* do "one" query to api

    '''
    min_participants_count = 5000
    messages_limit = 3000
    min_delay = 60
    max_delay = 120  # 180
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
            config_path="configs/client_config.yml",
            logging_config_path="configs/logger_config.yml",
            dump_path="data/raw",
            activate_logging=True,
    ):
        '''
        reads config values, creates logger and
        authorizes the client if necessary
        '''

        self.config_path = config_path
        self.config = self.__load_config()
        self.logging_config_path = logging_config_path
        self.client = self.__authorize()
        self.logger = logging.getLogger("client")
        self.dump_path = dump_path
        self.successful = 0
        self.chat_member = False
        self.activate_logging = activate_logging
        if activate_logging:
            self.__init_logging()

    def __load_config(self) -> AppConfig:
        base_config = OmegaConf.load(self.config_path)
        schema = OmegaConf.structured(AppConfig)
        config = OmegaConf.merge(schema, base_config)
        config: AppConfig = OmegaConf.to_object(config)
        return config

    def __authorize(self):
        client = TelegramClient(
            self.config.client_config.session,
            self.config.client_config.api_id,
            self.config.client_config.api_hash,
        )
        client.connect()
        if client.is_user_authorized():
            return client
        else:
            self.logger.critical("Not authorized")
            raise Exception("Not authorized")

    def __init_logging(self):
        with open(self.logging_config_path) as config_fin:
            config = yaml.safe_load(config_fin)
            logging.config.dictConfig(config)
        # let's go
        self.logger.debug("*** New run ***")

    def end_parsing(self):
        stop_message = "Crawling done, successful calls: {}".format(self.successful)
        self.logger.info(stop_message)
        self.notify(stop_message, "kpotoh")

    def crawl_channel(self, username: Union[int, str]):
        ''' that is the main method responsible for the parse of the messages
            TODO: complete the description
        '''
        start_time = time()
        if not self.activate_logging:
            self.__init_logging()

        try:
            if username is None:
                return "end"

            # if is_processed(username):
            #     self.logger.info('Already parsed {}'.format(username))
            #     return "error"

            self.logger.info("Started iteration for {}".format(username))

            ########## FULL ##########
            self.logger.info("Run channel full extraction")
            full_data = self.get_channel_full(username)
            if full_data is None:
                self.logger.info("Cannot get channel full; go to next chanel")
                mark_as_error(username)
                self.wait()
                return "error"
            else:
                full_data, full_data_raw = full_data
                channel_id = full_data.channel_id
                # self.channel_id = channel_id
                self.logger.info(
                    "Got channel full - username: {}, id: {}".format(
                        full_data.username, channel_id))
                self.save_to_json(full_data_raw, "full", channel_id)
                # TODO save full

            self.wait()
            _pc = full_data.participants_count
            if _pc < self.min_participants_count:
                self.logger.info(
                    'Small channel, {} participants, pass it'.format(_pc))
                return "small"

            ########## MEDIA ##########
            self.logger.info('Run channel media counts extraction')
            media_data = self.get_header_media_counts(channel_id)
            if media_data is None:
                self.logger.error("Cannot get channel media counts")
                self.logger.info("Continue crawling")
                media_data = (MediaChannelData(), None)  # default zeros
            else:
                self.logger.info("Media counts extracted")
                media_data, media_data_raw = media_data
                self.save_to_json(media_data_raw, "media", channel_id)
                # TODO save media counts

            self.wait()

            ########## CHAT ##########
            chat_users = []
            if full_data.linked_chat_id is not None:
                self.logger.info("Extract linked chat (id={}) users"
                    .format(full_data.linked_chat_id))
                chat_users = self.get_linked_chat_members(
                    channel_id, full_data.linked_chat_id)
                if chat_users is None:
                    self.logger.error("Cannot get linked chat users")
                else:
                    self.logger.info("{} users extracted from linked chat"
                                     .format(len(chat_users[0])))
                    chat_users, chat_users_raw = chat_users
                    self.save_to_json(
                        chat_users_raw, "linked_chat", channel_id)
                    # TODO save chat users
            else:
                self.logger.info("There are no linked chat")

            self.wait()

            ########## MESSAGES ##########
            self.logger.info("Start retrieving of messages from channel")
            messages = self.get_messages(channel_id)
            if messages is None:
                self.logger.error("Cannot retrieve channel messages")
            else:
                self.logger.info("Retrieved {} messages".format(
                    len(messages[0])))
                messages, messages_raw = messages
                self.save_to_json(messages_raw, "messages", channel_id)
                # TODO save messages

            ########## NEW CHANNELS ##########
            self.logger.info(
                "Start extraction of new usernames from messages and about")
            new_channels = extract_usernames(full_data.about, messages_raw)
            self.logger.info("Extracted {} new potential channels"
                             .format(len(new_channels)))

            mark_as_ok(username)
            self.successful += 1
            spent_time = time() - start_time
            self.logger.info("Channel {} done in {:.2f} seconds".format(
                channel_id, spent_time))
            self.wait()
            return 'ok'

        except Exception as e:
            self.logger.critical(repr(e))
            return 'error'

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
            about=full.full_chat.about,
            date=header.date,
            participants_count=full.full_chat.participants_count,
            linked_chat_id=linked_chat_id,
        )
        return data, full

    @cool_exceptor
    def get_linked_chat_members(
            self, channel_id: int,
            chat_id: int) -> Tuple[List[UserData], TotalList]:
        chat_members = self.client.get_participants(chat_id)
        data = [UserData(channel_id, x.id, x.bot, x.username)
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
                message=msg.raw_text,  # text maybe?
                date=msg.date,
                views=msg.views,
                forwards=msg.forwards,
                replies_cnt=replies_cnt,
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
                message=msg.message,
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
        self.logger.info(
            "{} dumped in {}".format(label.capitalize(), filepath))

    def is_channel(self, link: str) -> Tuple[bool, Union[None, int]]:
        """ check if link is channel link; return indicator and channel_id """
        try:
            entity = self.client.get_input_entity(link)
            if isinstance(entity, InputPeerChannel):
                return True, entity.channel_id
        except ValueError as e:
            self.logger.info(repr(e))
        except Exception as e:
            self.logger.error(repr(e))
        return False, None

    def notify(self, message: str, chat=1777596799):
        """ send `message` (notification) to chat """
        if not self.chat_member:
            self.chat_member = True
            self.client(JoinChannelRequest(chat))
            self.logger.info("Joined to chat")

        self.client.send_message(chat, message)
        self.logger.info("Sended message '{}' to chat".format(message))

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
            self.logger.info('Going to sleep for {} sec'.format(str(delay)))
        sleep(delay)
