import argparse

from yaml import load
from sqlalchemy.orm import relation, sessionmaker, Session
from sqlalchemy import create_engine
from omegaconf import OmegaConf

from core.entities import DbConfigSchema
from core.utils import send_status_to_queue
from core.utils.web import extract_subscribers

DEFAULT_CONFIG_PATH = "configs/db_config.yml"


# def get_channel_from_db(session_cls: Session) -> Union[str, None]:
#     """ session_cls must do SERIALIZABLE connections """
#     with session_cls() as session:
#         record = session.query(ChannelQueue).filter(
#             ChannelQueue.status == "to_process").first()
#         if record is None:
#             return None
#         username = record.channel_link
#         session.query(ChannelQueue)\
#             .filter(ChannelQueue.channel_link == username)\
#             .update({"status": "processing"})

#         session.commit()
#     return username



def get_usernames(session_cls: Session):



def check_username(channel_username: str, session_cls: Session):



def main(config: DbConfigSchema):
    engine = create_engine(
                config.database.db_url,
                pool_recycle=60,
                pool_pre_ping=True,
                pool_size=3,
    )
    engine_ser = engine.execution_options(isolation_level='SERIALIZABLE')
    session_cls = sessionmaker(bind=engine_ser)




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
