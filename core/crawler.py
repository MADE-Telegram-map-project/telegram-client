from datetime import date
# import getpass  # so the password is hidden when typed
import json
import logging
import logging.config
import os
import re
from datetime import date, datetime
import random
from time import sleep, time
from typing import Tuple, List, Union

import numpy as np
import pandas as pd
from omegaconf import OmegaConf
# from statemachine import StateMachine, State
import telethon
from telethon.sync import TelegramClient
# from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.errors import (
    ChannelPrivateError,
    FloodWaitError,
    RpcCallFailError,
    RpcMcgetFailError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
    MsgIdInvalidError,
)
from telethon.tl.types import (
    MessageEntityMention,
    InputPeerChannel,
    PeerChannel,
    MessageService,
    TLObject
)
from telethon.tl.types.messages import ChannelMessages, ChatFull, SearchCounter
from telethon.helpers import TotalList
from telethon import functions, types
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import (
    GetSearchCountersRequest,
    GetRepliesRequest
)
import yaml

from core.entities import (
    FullChannelData, MediaChannelData,
    UserData, MessageData, ReplyData,
    ClientConfigSchema
)
from core.utils import (
    is_processed,
    load_channel,
    cool_exceptor,
    mark_as_processing,
    mark_as_error,
    mark_as_ok
)


class Crawler():
    '''
    this is the main class responsible for obtaining data from telegram

    each method get_* do "one" query to api

    '''
    # offset_date = date.fromisoformat("2020-01-01")
    messages_limit = 1000
    min_delay = 60
    max_delay = 180
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
            self, user_profile, log_filename,
            config_path="configs/client_config.yml",
            logging_config_path="configs/logger_config.yml",
            log_folder="logs/",
            dump_path="data/raw",
            already_parsed_path="already_parsed/",
            invalid_id_folder="invalid_ids/"):
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
        self.channel_id = None
        # self.invalid_id_path = invalid_id_folder + log_filename
        # self.new_ids_usernames = "tmp/new_ids_usernames_mapping_" + log_filename
        # self.already_parsed = self.get_already_parsed()
        # self.non_existing = self.get_non_existing()
        # self.invalid_ids = get_channel_records_from_folder(invalid_id_folder)

    def __load_config(self) -> ClientConfigSchema:
        base_config = OmegaConf.load(self.config_path)
        schema = OmegaConf.structured(ClientConfigSchema)
        config = OmegaConf.merge(schema, base_config)
        config: ClientConfigSchema = OmegaConf.to_object(config)
        return config

    def __authorize(self):
        client = TelegramClient(
            self.config.session,
            self.config.api_id,
            self.config.api_hash,
        )
        client.connect()
        if client.is_user_authorized():
            return client
        else:
            raise Exception("Not authorized")

    def __init_logging(self):
        with open(self.logging_config_path) as config_fin:
            config = yaml.safe_load(config_fin)
            logging.config.dictConfig(config)
        # let's go
        self.logger.debug("*** New run ***")

    def crawl(self):
        ''' that is the main method responsible for the parse of the messages
            TODO: complete the description
        '''
        self.__init_logging()
        successful = 0
        while True:
            username = load_channel()
            start_time = time()
            if username is None:
                stop_message = "Crawling done, successful calls: {}"\
                    .format(successful)
                self.logger.info(stop_message)
                self.notify(stop_message)
                break

            if is_processed(username):
                self.logger.info('Already parsed {}'.format(username))
                continue

            mark_as_processing(username)
            self.logger.info("Started iteration for {}".format(username))

            self.logger.info("Run channel full extraction")
            full_data = self.get_channel_full(username)
            if full_data is None:
                self.logger.error("Cannot get channel full")
                mark_as_error(username)
                self.wait()
                continue
            else:
                full_data, full_data_raw = full_data
                channel_id = full_data.channel_id
                self.channel_id = channel_id
                self.logger.info(
                    "Got channel full - username: {}, id: {}".format(
                        full_data.username, channel_id))
                self.save_to_json(full_data_raw, "full", channel_id)
                # TODO save full

            self.wait()
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
            chat_users = []
            if full_data.linked_chat_id is not None:
                self.logger.info("Extract linked chat (id={}) users")
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

            mark_as_ok(username)
            successful += 1
            spent_time = time() - start_time
            self.logger.info("Channel {} done in {} seconds".format(
                channel_id, spent_time))
            self.wait()

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
                if isinstance(msg.fwd_from.from_id, types.PeerChannel):
                    fwd_channel_id = msg.fwd_from.from_id.channel_id
                else:
                    fwd_channel_id = None

                fwd_message_id = msg.fwd_from.channel_post  # TODO check

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

    def save_messages_from_channel(self, channel):
        '''
        given a channgel(link|id) it asks for all messages and saves them as json
        '''
        self.logger.info("PROCESSING_CHANNEL:{}".format(channel.username))
        start_time = time()
        self.logger.info(
            "started retrieving messages from the channel: {}".format(
                channel.username))
        messages = self.client.get_message_history(channel, limit=10000)
        end_time = time()
        self.logger.info(
            "Overall number of messages: {}".format(
                channel.username))
        self.logger.info(
            "finished retrieving messages from the channel: {}".format(
                channel.username))
        timing = end_time - start_time
        self.logger.info(
            "Retrieved number of messages: {} Overall time: {} for channel: {}".format(
                len(messages), int(timing), channel.username))
        path = self.messages_folder + channel.username + ".json"
        open(path, 'w').close()  # just cleaning the file
        self.logger.info(
            "started saving messages from the channel: {}".format(
                channel.username))
        messages = [message.to_dict() for message in messages]
        with open(path, "a") as output, open(self.already_parsed_path + self.log_filename, "a") as already_parsed_file:
            json.dump(messages, output, default=self.json_serial)
            print(channel.username.lower(), file=already_parsed_file)
        self.logger.info(
            "finished saving messages from the channel: {}".format(
                channel.username))
        self.logger.info("FINISHED_CHANNEL:{}".format(channel.username))

    def read_messages_from_dist(self, username):
        ''' reads json messages saved to disk
            Input: channel name
            Output: json with its messages
        '''
        with open(self.messages_folder + username + ".json", "r") as inputfile:
            messages = json.load(inputfile)
        return messages

    def save_to_json(
            self, obj: [TLObject, TotalList], label: str, channel_id: int):
        """ dump TLObject inheritor to file

        params:
            - obj
            - label: {"full", "linked_chat", "media", "messages", "replies"}

        """
        assert isinstance(channel_id, int), "channel_id must be integer"
        assert "to_json" in dir(
            obj), "cannot dump object, it doesn't have .to_json"
        if not os.path.exist(self.dump_path):
            os.mkdir(self.dump_path)

        channel_path = os.path.join(self.dump_path, str(channel_id))
        if not os.path.exist(channel_path):
            os.mkdir(channel_path)

        filepath = os.path.join(channel_path, "{}.json".format(label))
        if label == "full":
            with open(filepath) as fp:
                obj.to_json(fp, ensure_ascii=False)

        elif label in {"messages", "linked_chat", "media"}:
            new_obj = [msg.to_dict() for msg in obj]
            with open(filepath) as fp:
                json.dump(new_obj, fp, ensure_ascii=False)
        
        elif label == "replies":
            new_obj = [msg.to_dict() for msg in obj]
            # with open(filepath) as fp:
            #     json.dump(new_obj, fp, ensure_ascii=False)
            # TODO dump replies, in "replies/meddage_id.json"
            # need to pass meddage_id into this function

        self.logger.info("{} dumped in {}".format(label, filepath))

    def is_channel(self, link: str) -> Tuple[bool, Union[None, int]]:
        """ check if link is channel link and return indicator and channel_id """
        entity = self.client.get_input_entity(link).to_dict()
        if entity["_"] == "InputPeerChannel":
            return True, entity["channel_id"]
        return False, None

    # @staticmethod
    # def json_serial(obj):
    #     """JSON serializer for objects not serializable by default json code"""

    #     if isinstance(obj, (datetime, date)):
    #         return obj.isoformat()
    #     if isinstance(obj, bytes):
    #         return "here we some bytes"
    #     raise TypeError("Type %s not serializable" % type(obj))

    def get_request_delay(self):
        ''' we need to set up a delay between requests, it must be a random number '''
        delay_time = np.random.randint(low=self.min_delay, high=self.max_delay)
        return delay_time

    def wait(self, delay: int = None, to_log=True):
        delay = delay or self.get_request_delay()
        if to_log:
            self.logger.info('going to sleep for {} seconds'
                             .format(str(delay_time)))
        sleep(delay)

    # def get_already_parsed(self):
    #     ''' reads the list of files in self.messages_folder, caches it and returns saved list '''
    #     if self.already_parsed_channels is None:
    #         self.already_parsed_channels = self.__find_already_parsed()
    #     return self.already_parsed_channels

    # def __find_already_parsed(self):
    #     ''' internal: finds json files already filled in self.messages_folder '''
    #     from_messages_folder = list(map(lambda filename: filename.replace(
    #         ".json", "").lower(), os.listdir(self.messages_folder)))
    #     from_config = get_channel_records_from_folder(self.already_parsed_path)
    #     all_parsed = from_messages_folder + from_config
    #     return all_parsed

    # def get_non_existing(self):
    #     ''' it loads usernames already determined to be non existant + reads the logs to find non-existant and updated the file '''
    #     # we read the accounts we already know to be non existing
    #     already_found = set(
    #         get_channel_records_from_folder(
    #             self.non_existing_accounts_folder))
    #     # we check if we found some new non existing accounts in the log
    #     log_data = []
    #     for log_file in os.listdir(self.log_folder):
    #         log_path = self.log_folder + "/" + log_file
    #         with open(log_path, "r") as log_file:
    #             log_data += log_file.read().splitlines()

    #     for line in log_data:
    #         m = re.search("DOES_NOT_EXIST:(?P<account>[A-Za-z0-9_-]+)", line)
    #         if m:
    #             new_account = m.group("account")

    #     return already_found

    # def write_final_stats(self, successful, start_time):
    #     self.logger.info("stats")
    #     self.logger.info("successful calls:{}".format(str(successful)))
    #     spent_time = time() - start_time
    #     self.logger.info("time spent in seconds:{}".format(str(spent_time)))
    #     self.logger.info("***END***")

    # def create_temporal_dataset(self, inputpath, outpath):
    #     ''' creates a temporal dataset of only records that are still not parsed '''
    #     df = pd.read_csv(inputpath, sep=";")
    #     urls = df['Короткий URL'].apply(
    #         lambda x: x.replace("@", "")).str.lower()
    #     out_df = df[~(urls.isin(self.already_parsed) | urls.isin(
    #         self.non_existing)) & (df['Тип (Группа/Канал)'] == "канал")]
    #     out_df.to_csv(outpath, sep=";")
