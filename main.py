import queue
import threading

from omegaconf import OmegaConf

from core.consumer import Consumer
from core.crawler import Crawler
from core.entities import AppConfig


def main(config: AppConfig):
    maxsize = 1
    input_queue = queue.Queue(maxsize=maxsize)
    output_queue = queue.Queue(maxsize=maxsize)

    crawler = Crawler(config, input_queue, output_queue)
    consumer = Consumer(config.message_broker, input_queue, output_queue, crawler)

    # # Other thread can receive message from output_queue and
    # # add processign result to input_queue
    t = threading.Thread(target=consumer.start_consuming)
    t.start()

    crawler.crawl()
    t.join()


if __name__ == "__main__":
    config_path = "configs/client_config.yml"
    base_config = OmegaConf.load(config_path)
    schema = OmegaConf.structured(AppConfig)
    config = OmegaConf.merge(schema, base_config)
    config: AppConfig = OmegaConf.to_object(config)
    main(config)
