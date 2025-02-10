from dataclasses import dataclass
from typing import List

@dataclass
class Artist:
    id: str
    name: str
    genres: List[str]

@dataclass
class Track:
    id: str
    name: str
    artists: List[Artist]
    popularity: int
    duration_ms: int