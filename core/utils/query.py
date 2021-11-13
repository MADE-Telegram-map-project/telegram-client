import re
from time import sleep
from typing import Union

from telethon.errors import (
    ChannelPrivateError,
    FloodWaitError,
    RpcCallFailError,
    RpcMcgetFailError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
    # MsgIdInvalidError,
)


def cool_exceptor(func):
    """ decorator for queries to except errors;
    works only with Crawler class
    """
    def wrapper(*args, **kwargs) -> Union[None, tuple]:
        """return None or normal result"""
        # func is custom_wrapper(get_*)  ~extractors
        self = args[0]
        result = None
        status = "wait"
        retries = 0
        while status == "wait":
            if retries == 5:
                self.logger.critical(
                    "After {} times of waiting there are no progress"
                    .format(retries))
                self.notify("After {} times of waiting there are no progress"
                    .format(retries))
                delay_time = self.get_request_delay() * 5  # a bit longer
                sleep(delay_time)
                return None

            retries += 1
            try:
                result = func(*args, **kwargs)
                status = "ok"
            # if we cann't get the channel, it means it doesn't really exist
            # anymore
            except (UsernameNotOccupiedError, UsernameInvalidError) as e:
                self.logger.warn("Channel DOES_NOT_EXIST")
                status = "error"
            except ValueError as e:
                error_message = str(e)
                if error_message.startswith("No user has"):
                    status = "error"
                    self.logger.warn(error_message)
                else:
                    status = "error"
                    self.logger.error(repr(e))
            # ok internal issues it seems:
            except (RpcCallFailError, RpcMcgetFailError) as e:
                self.logger.error(
                    "We got internal error it seems, going to sleep " +
                    "for a while and continue; {}".format(str(e)))
                delay_time = self.get_request_delay() * 5  # sleep a bit longer
                sleep(delay_time)
                status = "wait"
            except FloodWaitError as e:
                error_message = str(e)
                time_to_sleep_flood = extract_flood_waiting_time(
                    error_message) + self.get_request_delay() * 10
                self.logger.error(
                    "We got flood ban; {}; going to sleep for {} seconds"
                    .format(str(e), str(time_to_sleep_flood)))
                sleep(time_to_sleep_flood)
                status = "wait"
            except (TypeError, ChannelPrivateError) as e:
                # with open(self.invalid_id_path, "a") as invalid_ids_file:
                #     print(channel_record, file=invalid_ids_file)
                self.logger.warn(e)
                status = "error"
            except RuntimeError as e:
                if "retries" in str(e):
                    # ok that's easy, we just need to sleep and restart
                    self.logger.error(
                        "We got the number of retries error, going to sleep " +
                        "for a while now and then continue; {}".format(str(e)))
                    delay_time = self.get_request_delay() * 5  # a bit longer
                    sleep(delay_time)
                    status = "wait"
                else:
                    self.logger.critical("Weird runtime error \n" + str(e))
                    self.notify("Weird runtime error \n" + repr(e))
                    status = "error"
            except Exception as e:  # ok, it seems like
                self.logger.critical(
                    "it seems like it's over for now; {}".format(repr(e)))
                self.notify("it seems like it's over for now; {}".format(repr(e)))
                status = "error"
                # self.write_final_stats(successful, start_time)
        return result
    return wrapper


def extract_flood_waiting_time(error_message: str) -> int:
    ''' Extract time from the messages like
    "A wait of 30716 seconds is required" '''
    m = re.search("\\d+", error_message)
    return int(m.group(0))
