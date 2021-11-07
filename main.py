import queue
from time import sleep

from omegaconf import OmegaConf

from core.consumer import Consumer
from core.crawler import Crawler
from core.entities import AppConfig
from core.utils.link_extractor import extract_usernames


def main(config: AppConfig):
    maxsize = 1
    input_queue = queue.Queue(maxsize=maxsize)
    output_queue = queue.Queue(maxsize=maxsize)

    # # Other thread can receive message from output_queue and 
    # # add processign result to input_queue
    consumer = Consumer(config.message_broker, input_queue, output_queue)
    consumer.start_consuming()
    print(consumer)
    
    crawler = Crawler()
    crawler.crawl()



if __name__ == "__main__":
    config_path = "configs/client_config.yml"
    base_config = OmegaConf.load(config_path)
    schema = OmegaConf.structured(AppConfig)
    config = OmegaConf.merge(schema, base_config)
    config: AppConfig = OmegaConf.to_object(config)
    print(config)
    main(config)
