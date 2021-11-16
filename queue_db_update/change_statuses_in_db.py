import argparse
from collections import defaultdict
from os import stat
from typing import Union, List

from yaml import load
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from omegaconf import OmegaConf
import tqdm

from core.entities import DbConfigSchema
from core.utils.web import extract_subscribers
from core.db_seed.db import ChannelQueue

DEFAULT_CONFIG_PATH = "configs/db_config.yml"
BATCH_SIZE = 500
EPOCHS = 10
min_participants_count = 5000


def get_channels(session_cls: Session, batch_size=BATCH_SIZE) -> List[str]:
    """ get channel usernames from db queue and update their status to 'to_process'"""
    with session_cls() as session:
        records = session.query(ChannelQueue)\
            .filter(ChannelQueue.status == "to_process")\
            .limit(batch_size)
        if records is None:
            return None

        usernames = [r.channel_link for r in records]
        session.query(ChannelQueue)\
            .filter(ChannelQueue.channel_link.in_(usernames))\
            .update({"status": "processing"})

        session.commit()
    return usernames


def check_usernames(usernames: List[str]) -> dict:
    """ return statuses to update in db queue"""
    statuses = defaultdict(list)
    nerror = nsmall = nproc = 0
    uname = 'start'
    for uname in tqdm.tqdm(usernames, "parsing"):
        partisiants = extract_subscribers(uname)
        if partisiants == -1:
            statuses["error"].append(uname)
            nerror += 1
        elif partisiants < min_participants_count:
            statuses["error"].append(uname)
            nsmall += 1
        else:
            statuses["to_process"].append(uname)
            nproc += 1
    print(f"Error: {nerror}, small: {nsmall}, to_process: {nproc}")
    return statuses


def update_db_queue(new_statuses: dict, session_cls: Session):
    with session_cls() as session:
        for status, usernames in new_statuses.items():
            session.query(ChannelQueue)\
                .filter(ChannelQueue.channel_link.in_(usernames))\
                .update({"status": status})
            session.commit()

def cancel_processing(session_cls: Session):
    with session_cls() as session:
        session.query(ChannelQueue)\
            .filter(ChannelQueue.status == "processing")\
            .update({"status": "to_process"})
        session.commit()


def main(config: DbConfigSchema):
    engine = create_engine(
        config.db_url,
        pool_recycle=60,
        pool_pre_ping=True,
        pool_size=3,
    )
    engine_ser = engine.execution_options(isolation_level='SERIALIZABLE')
    session_cls = sessionmaker(bind=engine)
    session_cls_ser = sessionmaker(bind=engine_ser)

    for _ in range(EPOCHS):
        usernames = get_channels(session_cls_ser)
        new_statuses = check_usernames(usernames)
        update_db_queue(new_statuses, session_cls)


def load_config() -> DbConfigSchema:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=False,
                        help="A path to YAML configuration file",
                        default=DEFAULT_CONFIG_PATH,
                        )

    args, reminder = parser.parse_known_args()
    base_config = OmegaConf.load(args.config)
    cli_config = OmegaConf.from_cli(reminder)

    config = OmegaConf.merge(base_config, cli_config)
    schema = OmegaConf.structured(DbConfigSchema)
    config = OmegaConf.merge(schema, config)
    config: DbConfigSchema = OmegaConf.to_object(config)
    return config


if __name__ == "__main__":
    config: DbConfigSchema = load_config()
    main(config)
