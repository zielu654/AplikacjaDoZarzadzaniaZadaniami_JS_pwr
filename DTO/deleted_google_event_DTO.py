from dataclasses import dataclass
from datetime import datetime

@dataclass
class DeletedGoogleEventDTO:
    google_event_id: str
    updated_at: datetime