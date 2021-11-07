from time import sleep
import queue
from omegaconf import OmegaConf

from core.crawler import Crawler
from core.entities import AppConfig
from core.utils.link_extractor import extract_usernames
from core.consumer import Consumer


def run_crawler():
    profiles = ["megafon", "base", "interactive"]
    # configuring logging
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        raise Exception("wrong number of arguments")

    profile = sys.argv[1]
    if profile not in profiles:
        raise Exception("unsupported profile")

    if len(sys.argv) == 2:
        min_value = 0
        max_value = 0
    elif len(sys.argv) == 3:
        min_value = int(sys.argv[2])
        max_value = 10**5
    elif len(sys.argv) == 4:
        min_value = int(sys.argv[2])
        max_value = int(sys.argv[3])

    if profile != "interactive":
        log_name = profile + "_" + str(datetime.now().month) + "_" + str(
            datetime.now().day) + "_" + str(datetime.now().hour)
        crawler = RutanCrawler(profile, log_name)
        data = Preprocessor().get_new_ids()
    #   data = Preprocessor().get_clean_downloaded_dataset_with_7k_records("data/tmp_dataset.csv")
    #   urls = data['Короткий URL'].iloc[min_value:max_value]
        urls = data.iloc[min_value:max_value]
        crawler.crawl(urls, id_mode=True)
    else:
        crawler = RutanCrawler(profile, profile)
#       crawler.create_temporal_dataset(inputpath="data/groups_channels_Oct_2017.csv", outpath="data/tmp_dataset.csv")
#       data    = Preprocessor().get_clean_downloaded_dataset_with_7k_records("data/tmp_dataset.csv")
    return locals()


def main(config: AppConfig):
    # ch = 1149710531  # latina
    # mid = 2581
    ch = "gagaga_momomo"

    # maxsize = 1
    # input_queue = queue.Queue(maxsize=maxsize)
    # output_queue = queue.Queue(maxsize=maxsize)

    # # Other thread can receive message from output_queue and add processign result to input_queue
    # consumer = Consumer(config.message_broker, input_queue, output_queue)
    # consumer.start_consuming()

    crawler = Crawler()
    crawler.notify("test")
    # crawler.crawl()

    # crawler.is_channel(ch)

    # full, full_raw = crawler.get_channel_full(ch)
    # crawler.save_to_json(full_raw, "full", ch)
    # sleep(2)
    # media, media_raw = crawler.get_header_media_counts(ch)
    # crawler.save_to_json(media_raw, "media", ch)
    # sleep(2)
    # lch_members, lch_members_raw = crawler.get_linked_chat_members(
    #     ch, full.linked_chat_id)
    # crawler.save_to_json(lch_members_raw, "linked_chat", ch)
    # sleep(2)

    # n_messages = 10
    # messages, messages_raw = crawler.get_messages(ch, n_messages)

    # nei_usernames = extract_usernames(full.about, messages_raw)

    # crawler.save_to_json(messages_raw, "messages", ch)

    # print(messages)
    # sleep(2)

    # for msg in messages:
    #     if msg.replies_cnt > 0:
    #         replies, commenters = crawler.get_replies(ch, msg.message_id)
    #         sleep(1)


if __name__ == "__main__":
    config_path = "configs/client_config.yml"
    base_config = OmegaConf.load(config_path)
    schema = OmegaConf.structured(AppConfig)
    config = OmegaConf.merge(schema, base_config)
    config: AppConfig = OmegaConf.to_object(config)
    main(config)


# if __name__ =="__main__":
#     api_id: int = os.environ["API_ID"]
#     api_hash: str = os.environ["API_HASH"]

#     name = 'client1'
#     client: TelegramClient = None

#     # https://t.me/latinapopacanski
#     # ch = 19534473280
#     # ch = "breakingmash"
#     ch = "latinapopacanski"  # 1149710531
#     message_id = 2563

#     with TelegramClient(name, api_id, api_hash) as client:
#         # d = get_header_media_counts(client, ch)
#         # print(d)
#         # print(type(client))
#         get_commenters(client, ch, message_id)


#         # full = get_channel_full(client, ch)
#         # print(full)

#         # print(client.get_input_entity(ch))

#         # client.get_entity(1117628569).to_json() # альтернатива получению всей инфы


#         # print(get_channel_id(client, ch))
#     # 1232476793
