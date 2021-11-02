"""
methods for
    - channels loading (DB)
    - channels dumping (DB & raw)
    - 

utils.data.load_from_queue/tree/dev
utils.data.dump_raw
utils.data.put_into_db


"""
import os
from datetime import date
from time import sleep
# from collections import namedtuple

import telethon
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.errors import (
    ChannelPrivateError,
    FloodWaitError,
    RpcCallFailError,
    RpcMcgetFailError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
    MsgIdInvalidError,
)


def notify(client, message: str, user: str):
    """ send `message` (notification) to @user """
    client.send_message(user, message)


def dump_to_json(obj):
    assert "to_json" in dir(obj)
    # TODO dump raw files


def is_channel(client, link: str) -> tuple:
    """ check if link is channel link and return indicator and channel_id """
    entity = client.get_input_entity(link).to_dict()
    if entity["_"] == "InputPeerChannel":
        return True, entity["channel_id"]
    return False, None


def load_channel() -> int:
    """ load channel from queue """
    return 0


def is_processed(channel) -> bool:
    """ check if channel marked completed or raised in BD """
    # TODO connection to DB
    return False


def mark_as_processing(channel: int):
    """ send mark 'processing' to DB """
    pass


def mark_as_error(channel):
    """ send mark 'error' to DB """
    pass


def mark_as_ok(channel):
    """ send mark 'ok' to DB """
    pass 


def cool_exceptor(func):
    """ decorator for queries to except errors; 
    works only with Crawler class
    """
    def wrapper(*args, **kwargs):
        """return None or normal result"""
        # func is custom_wrapper(get_*)  ~extractors
        self = args[0]
        result = None
        status = "wait"
        retries = 0
        while status == "wait":
            if retries == 5:
                self.logger.critical(
                    "after {} times of waiting there are no progress"\
                        .format(retries))
                return None

            retries += 1
            try:
                result = func(*args, **kwargs)
                status = "ok"
            # if we cann't get the channel, it means it doesn't really exist
            # anymore
            except (UsernameNotOccupiedError, UsernameInvalidError) as e:
                self.logger.info("DOES_NOT_EXIST")
                status = "error"
            except ValueError as e:
                error_message = str(e)
                if error_message.startswith("No user has"):
                    status = "error"
                    self.logger.info(error_message)
                else:
                    status = "error"
                    self.logger.error(repr(e))
            # ok internal issues it seems:
            except (RpcCallFailError, RpcMcgetFailError) as e:
                self.logger.error(
                    "We got this internal error it seems, going to sleep for a while now and continue\n" +
                    str(e))
                delay_time = self.get_request_delay() * 5  # just sleep a bit longer
                sleep(delay_time)
                status = "wait"
            except FloodWaitError as e:
                error_message = str(e)
                time_to_sleep_flood = extract_flood_waiting_time(
                    error_message) + self.get_request_delay() * 10
                self.logger.error(
                    "Got flood ban \n" +
                    str(e) +
                    "\n" +
                    "going to sleep for {} seconds".format(
                        str(time_to_sleep_flood)))
                sleep(time_to_sleep_flood)
                status = "wait"
            except (TypeError, ChannelPrivateError) as e:
                # with open(self.invalid_id_path, "a") as invalid_ids_file:
                #     print(channel_record, file=invalid_ids_file)
                self.logger.info(e)
                status = "error"
            except RuntimeError as e:
                if "retries" in str(e):
                    # ok that's easy, we just need to sleep and restart
                    self.logger.error(
                        "We got the number of retries error, I am going to sleep for a while now and then continue\n" +
                        str(e))
                    delay_time = self.get_request_delay() * 5  # just sleep a bit longer
                    sleep(delay_time)
                    status = "wait"
                else:
                    self.logger.critical("Weird runtime error \n" + str(e))
                    status = "error"
                    # self.write_final_stats(successful, start_time)
            except Exception as e:  # ok, it seems like
                self.logger.critical(
                    "it seems like it's over for now; {}".format(repr(e)))
                status = "error"
                # self.write_final_stats(successful, start_time)
        return result
    return wrapper


def extract_flood_waiting_time(error_message: str) -> int:
    ''' Extract time from the messages like "A wait of 30716 seconds is required" '''
    m = re.search("\\d+", error_message)
    return int(m.group(0))
