from dataclasses import dataclass

@dataclass
class CategoryDTO:
    id: int
    name: str
    color_hex: str
    color_name: str
    sync_enabled: bool