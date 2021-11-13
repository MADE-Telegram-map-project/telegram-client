import argparse
from logging import config

from omegaconf import OmegaConf
from yaml import load

from core.crawler import Crawler
from core.entities import AppConfig


def main(config: AppConfig):
    crawler = Crawler(config)
    crawler.crawl()


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
