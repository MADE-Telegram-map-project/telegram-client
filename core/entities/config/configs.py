from dataclasses import dataclass


@ dataclass
class ClientSchema:
    session: str
    api_id: int
    api_hash: str
    phone: str = None
