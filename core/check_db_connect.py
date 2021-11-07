from urllib.parse import urlparse
from collections import namedtuple

from psycopg2 import sql
from omegaconf import OmegaConf
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from core.db_seed.db import ChannelQueue
from core.entities import AppConfig


DbCredentials = namedtuple("TemplateInfo", ["username", "password", "database", "hostname", "port"])


def main(config: AppConfig):
    engine = create_engine(config.database.db_url)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        query = session.query(ChannelQueue)\
            .filter(ChannelQueue.status == "to_process")\
            .limit(10)

        if query is not None:
            links = [i.channel_link for i in query]

        session.commit()


if __name__ == "__main__":
    config_path = "configs/client_config.yml"
    base_config = OmegaConf.load(config_path)
    schema = OmegaConf.structured(AppConfig)
    config = OmegaConf.merge(schema, base_config)
    config: AppConfig = OmegaConf.to_object(config)

    main(config)
