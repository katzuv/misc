import dataclasses


@dataclasses.dataclass
class Team:
    number: str
    name: str
    location: str
    year_spans: list[tuple[int, int]]
