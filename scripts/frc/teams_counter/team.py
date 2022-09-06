import dataclasses


@dataclasses.dataclass
class Team:
    number: str
    location: str
    year_spans: list[tuple[int, int]]
