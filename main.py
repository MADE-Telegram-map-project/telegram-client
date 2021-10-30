from time import sleep

from core.crawler import Crawler



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
        log_name = profile + "_" + str(datetime.now().month) + "_" + str(datetime.now().day) + "_" + str(datetime.now().hour)
        crawler  = RutanCrawler(profile,log_name)
        data     = Preprocessor().get_new_ids()
    #   data = Preprocessor().get_clean_downloaded_dataset_with_7k_records("data/tmp_dataset.csv")
    #   urls = data['Короткий URL'].iloc[min_value:max_value]
        urls = data.iloc[min_value:max_value]
        crawler.crawl(urls, id_mode=True)
    else:
        crawler = RutanCrawler(profile, profile)
#       crawler.create_temporal_dataset(inputpath="data/groups_channels_Oct_2017.csv", outpath="data/tmp_dataset.csv")
#       data    = Preprocessor().get_clean_downloaded_dataset_with_7k_records("data/tmp_dataset.csv")
    return locals()


def main():
    ch = 1149710531
    mid = 2581

    crawler = Crawler("user_profile", "log_filename")
    # crawler.get_commenters(ch, mid)
    n_messages = 5
    messages = crawler.get_messages(ch, n_messages)
    sleep(2)

    for msg in messages:
        replies, commenters = crawler.get_replies(ch, msg.message_id)
        sleep(1)



if __name__ == "__main__":
    main()
