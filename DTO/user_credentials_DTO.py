from dataclasses import dataclass

@dataclass
class UserCredentialsDTO:
    user_id: int
    token_data: str