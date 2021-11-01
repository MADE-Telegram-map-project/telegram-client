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
# from collections import namedtuple

import telethon
from telethon.sync import TelegramClient
from telethon import functions, types


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
    """ send mark to DB """
    pass


def cool_exceptor(func):
    def wrapper(*args, **kwargs):
        # func is custom_wrapper(get_*)  ~extractors
        try:
            func(*args, **kwargs)
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
