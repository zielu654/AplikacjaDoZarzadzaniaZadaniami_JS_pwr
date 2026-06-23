from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserCredentialsDTO:
    user_id: int
    token_data: str
    last_synced: datetime | None = None
