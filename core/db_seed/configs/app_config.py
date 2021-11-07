from dataclasses import dataclass
from typing import Optional
from omegaconf import MISSING


@dataclass
class DbConfigSchema:
    user: Optional[str] = MISSING
    database: Optional[str] = MISSING
    passw: Optional[str] = MISSING
    host: Optional[str] = MISSING
    port: Optional[int] = MISSING
    db_url: str = MISSING
    drop_tables: bool = False


@ dataclass
class AppConfigSchema:
    database: DbConfigSchema = MISSING
    sql_ddl_path: str = MISSING
    path_to_init_csv: str = MISSING
    channel_id_key: str = "link"
