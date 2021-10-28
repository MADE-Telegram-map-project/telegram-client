from datetime import date
import getpass  # so the password is hidden when typed
import json
import logging
import os
import re
from collections import namedtuple
from datetime import date, datetime
from time import sleep, time
from typing import Tuple, List, Union

import numpy as np
import pandas as pd
from pyhocon import ConfigFactory
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.errors.rpc_error_list import (ChannelPrivateError,
                                            FloodWaitError, RpcCallFailError,
                                            RpcMcgetFailError,
                                            UsernameInvalidError,
                                            UsernameNotOccupiedError)
from telethon.tl.types import PeerChannel
from tqdm import tqdm

from rutan_core.utils import get_channel_records_from_folder
from core.utils import (
    FullChannelData, MediaChannelData, UserData, MessageData
)

import telethon
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import (
    GetSearchCountersRequest, 
    GetRepliesRequest
)


# Debugging
# from pdb import set_trace as bp


class Crawler():
    ''' this is the main class responsible for obtaining data from telegram 
    
    each method get_* do "one" query to api
    
    '''
    offset_date = date.fromisoformat('2020-01-01')
    messages_limit = 1000

    messages_folder = "data/messages/"
    already_parsed = "already_parsed/"
    non_existing_accounts_folder = "non_existing/"
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
    # media_names = [
    #     "Photos",
    #     "Video",
    #     "Document",
    #     "Music",
    #     "Url",
    #     "Voice",
    #     "Gif",
    # ]

    def __init__(self, user_profile, log_filename, config_path="application.conf",
                 log_folder="logs/", already_parsed_path="already_parsed/", invalid_id_folder="invalid_ids/"):
        ''' reads config values, creates logger and authorizes the client if necessary '''
        self.already_parsed_path = already_parsed_path
        self.already_parsed_channels = None
        self.non_existing_accounts_path = self.non_existing_accounts_folder + "/" + log_filename
        self.config = ConfigFactory.parse_file(config_path)
        self.invalid_id_path = invalid_id_folder + log_filename
        self.logger = logging.getLogger("rutan")
        self.log_filename = log_filename
        self.new_ids_usernames = "tmp/new_ids_usernames_mapping_" + log_filename
        if user_profile == "interactive":
            self.user_profile = "base"
        else:
            self.user_profile = user_profile
        self.client = self.__authorize()
        self.log_folder = log_folder
        self.already_parsed = self.get_already_parsed()
        self.non_existing = self.get_non_existing()
        self.invalid_ids = get_channel_records_from_folder(invalid_id_folder)

    def crawl(self, records, id_mode=False):
        ''' that is the main method responsible for the parse of the messages
            id_mode = True (default False) -- crawl method receives only ids and not full dataset to work on
            TODO: complete the description
        '''
        self.__init_logging()
        start_time = time()
        successful = 0
        for channel_record in tqdm(records):
            if id_mode:
                username = channel_record  # it's in fact id and not url or name, in this case
            else:
                username = channel_record.replace("@", "").lower()

            if username in self.already_parsed or username in self.non_existing or username in self.invalid_ids:
                continue
            self.logger.info('started iteration for {}'.format(username))
            try:
                if id_mode:
                    channel = self.client.get_entity(PeerChannel(username))
                    with open(self.new_ids_usernames, "a") as new_id_usename_file:
                        print(
                            "{channel_id},{channel_username}".format(
                                channel_id=username,
                                channel_username=channel.username),
                            file=new_id_usename_file)
                else:
                    channel = self.client.get_entity(username)
                delay_time = self.get_request_delay()
                sleep(delay_time)
                self.save_messages_from_channel(channel)
                successful += 1
                delay_time = self.get_request_delay()
                self.logger.info(
                    'Going to sleep for {} seconds'.format(
                        str(delay_time)))
                sleep(delay_time)
            # if we cann't get the channel, it means it doesn't really exist
            # anymore
            except (UsernameNotOccupiedError, UsernameInvalidError) as e:
                self.logger.info("DOES_NOT_EXIST:{}".format(username))
                # save non existing immediately
                with open(self.non_existing_accounts_path, "a") as non_existing_file:
                    print(username, file=non_existing_file)
                delay_time = self.get_request_delay()
                self.logger.info(
                    'Taking an upset nap for {} seconds after stumbling on a non-existing channel'.format(str(delay_time)))
            # ok internal issues it seems:
            except (RpcCallFailError, RpcMcgetFailError) as e:
                self.logger.error(
                    "We got this internal error it seems, going to sleep for a while now and continue\n" +
                    str(e))
                delay_time = self.get_request_delay() * 5  # just sleep a bit longer
                sleep(delay_time)
            except FloodWaitError as e:
                error_message = str(e)
                time_to_sleep_flood = self.extract_flood_waiting_time(
                    error_message) + self.get_request_delay() * 10
                self.logger.error(
                    "Got flood ban \n" +
                    str(e) +
                    "\n" +
                    "going to sleep for {} seconds".format(
                        str(time_to_sleep_flood)))
                sleep(time_to_sleep_flood)
            except (TypeError, ChannelPrivateError) as e:
                with open(self.invalid_id_path, "a") as invalid_ids_file:
                    print(channel_record, file=invalid_ids_file)
                self.logger.info(e)
            except RuntimeError as e:
                if "retries" in str(
                        e):  # ok that's easy, we just need to sleep and restart
                    self.logger.error(
                        "We got the number of retries error, I am going to sleep for a while now and then continue\n" +
                        str(e))
                    delay_time = self.get_request_delay() * 5  # just sleep a bit longer
                    sleep(delay_time)
                else:
                    self.logger.critical("Weird runtime error \n" + str(e))
                    self.write_final_stats(successful, start_time)
                    bp()
                    print('starting debuggin')
            except Exception as e:  # ok, it seems like
                self.logger.critical(
                    "it seems like it's over for now \n" + str(e))
                self.write_final_stats(successful, start_time)
                bp()
                print('starting debuggin')

    def __authorize(self):
        ''' if not authorized, needs to go through 2 factor authorization, otherwise connects '''
        client = TelegramClient(
            self.config.get(
                self.find_config_name("app_name")), self.config.get(
                self.find_config_name("api_id")), self.config.get(
                self.find_config_name("api_hash")))
        connect = client.connect()
        authorized = client.is_user_authorized()
        if authorized:
            return client
        client.sign_in(self.config.get(self.find_config_name('phone_number')))
        try:
            client.sign_in(code=input('Enter code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=getpass.getpass())
        return client

    def find_config_name(self, config_param):
        return self.user_profile + "." + config_param

################
# my functions #
################

    def get_channel_full(self, channel: Union[str, int]) -> Tuple[FullChannelData, int]:
        """ channel is link or id"""
        full = self.client(GetFullChannelRequest(channel=channel))
        header = full.chats[0]
        linked_chat_id = full.full_chat.linked_chat_id

        data = FullChannelData(
            header.id,
            header.title,
            header.username,
            full.full_chat.about,
            header.date,
            full.full_chat.participants_count,
        )
        return data, linked_chat_id

    def get_linked_chat_members(self, chat_id: int) -> List[UserData]:
        chat_members = self.client.get_participants(chat_id)
        data = [UserData(x.id, x.bot, x.username) for x in chat_members]
        return data

    def get_header_media_counts(self, channel: Union[str, int]) -> MediaChannelData:
        """https://tl.telethon.dev/methods/messages/get_search_counters.html"""
        search_res = self.client(GetSearchCountersRequest(
                peer=channel, filters=self.media_filters,
        ))
        counts = [x.count for x in search_res]
        data = MediaChannelData(*counts)
        return data

    def get_messages(self, channel: Union[str, int]) -> List[MessageData]:
        """ return collected messages from oldest to newest"""
        messages = self.client.get_messages(
            channel, 
            limit=self.messages_limit,
            offset_date=self.offset_date, 
            reverse=True
        )
        data = []
        for m in messages:
            replies_cnt = m.replies.replies
            if m.fwd_from is None:
                fwd_channel_id = None
                fwd_message_id = None
            else:
                fwd_channel_id = m.fwd_from.from_id.channel_id
                fwd_message_id = m.fwd_from.channel_post  # TODO check

            cur_mes_data = MessageData(
                m.id, 
                m.text, 
                m.date, 
                m.views, 
                m.forwards,
                replies_cnt,
                fwd_channel_id,
                fwd_message_id,
                m.replies,
            )
            data.append(cur_mes_data)
        return data


    def get_commenters(self, channel: Union[str, int], message_id: int):
        comments = self.client(GetRepliesRequest(
            peer=channel, 
            msg_id=message_id, 
            offset_id=0, 
            offset_date=None, 
            add_offset=0,
            limit=0,
            max_id=0,
            min_id=0,
            hash=0,
        ))
        commenters = [UserData(x.id, x.bot, x.username) for x in comments.users]
        
        # TODO add comment text

        return commenters

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

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return "here we some bytes"
        raise TypeError("Type %s not serializable" % type(obj))

    def get_request_delay(self):
        ''' we need to set up a delay between requests, it must be a random number '''
        delay_time = np.random.randint(low=self.min_delay, high=self.max_delay)
        return delay_time

    def get_already_parsed(self):
        ''' reads the list of files in self.messages_folder, caches it and returns saved list '''
        if self.already_parsed_channels is None:
            self.already_parsed_channels = self.__find_already_parsed()
        return self.already_parsed_channels

    def __find_already_parsed(self):
        ''' internal: finds json files already filled in self.messages_folder '''
        from_messages_folder = list(map(lambda filename: filename.replace(
            ".json", "").lower(), os.listdir(self.messages_folder)))
        from_config = get_channel_records_from_folder(self.already_parsed_path)
        all_parsed = from_messages_folder + from_config
        return all_parsed

    def get_non_existing(self):
        ''' it loads usernames already determined to be non existant + reads the logs to find non-existant and updated the file '''
        # we read the accounts we already know to be non existing
        already_found = set(
            get_channel_records_from_folder(
                self.non_existing_accounts_folder))
        # we check if we found some new non existing accounts in the log
        log_data = []
        for log_file in os.listdir(self.log_folder):
            log_path = self.log_folder + "/" + log_file
            with open(log_path, "r") as log_file:
                log_data += log_file.read().splitlines()

        for line in log_data:
            m = re.search("DOES_NOT_EXIST:(?P<account>[A-Za-z0-9_-]+)", line)
            if m:
                new_account = m.group("account")

        return already_found

    def write_final_stats(self, successful, start_time):
        self.logger.info("stats")
        self.logger.info("successful calls:{}".format(str(successful)))
        spent_time = time() - start_time
        self.logger.info("time spent in seconds:{}".format(str(spent_time)))
        self.logger.info("***END***")

    def __init_logging(self):
        log_file = self.log_folder + self.log_filename
        logger = logging.getLogger('rutan')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        # let's go
        logger.debug("*** New run ***")

    def create_temporal_dataset(self, inputpath, outpath):
        ''' creates a temporal dataset of only records that are still not parsed '''
        df = pd.read_csv(inputpath, sep=";")
        urls = df['Короткий URL'].apply(
            lambda x: x.replace("@", "")).str.lower()
        out_df = df[~(urls.isin(self.already_parsed) | urls.isin(
            self.non_existing)) & (df['Тип (Группа/Канал)'] == "канал")]
        out_df.to_csv(outpath, sep=";")

    @staticmethod
    def extract_flood_waiting_time(error_message):
        ''' Extract time from the messages like "A wait of 30716 seconds is required" '''
        m = re.search("\\d+", error_message)
        return int(m.group(0))
