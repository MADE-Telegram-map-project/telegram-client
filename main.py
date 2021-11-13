import argparse
from logging import config
import queue
import threading

from omegaconf import OmegaConf
from yaml import load

from core.consumer import Consumer
from core.crawler import Crawler
from core.entities import AppConfig


def main(config: AppConfig):
    maxsize = 1
    input_queue = queue.Queue(maxsize=maxsize)
    output_queue = queue.Queue(maxsize=maxsize)

    crawler = Crawler(config, input_queue, output_queue)
    consumer = Consumer(config.message_broker, input_queue, output_queue)

    # # Other thread can receive message from output_queue and
    # # add processign result to input_queue
    t = threading.Thread(target=consumer.start_consuming)
    t.start()

    crawler.crawl()
    t.join()


def load_config() -> AppConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="A path to YAML configuration file")

    args, reminder = parser.parse_known_args()
    base_config = OmegaConf.load(args.config)
    cli_config = OmegaConf.from_cli(reminder)

    config = OmegaConf.merge(base_config, cli_config)
    schema = OmegaConf.structured(AppConfig)
    config = OmegaConf.merge(schema, config)
    config: AppConfig = OmegaConf.to_object(config)
    return config


if __name__ == "__main__":
    config = load_config()
    main(config)
