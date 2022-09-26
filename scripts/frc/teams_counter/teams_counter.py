import string
from collections.abc import Sequence

import more_itertools

from scripts.frc.tba_api_utils import send_api_request


YEARS_PARTICIPATED_ENDPOINT = string.Template("team/$team_key/years_participated")
TEAM_KEY_TEMPLATE = string.Template("frc$team_number")

COUNTRY = "country"
ISRAEL = "Israel"
TEAM_NUMBER = "team_number"


def get_israeli_teams(teams: list[dict]) -> list[dict]:
    """
    :param teams: list of teams
    :return: only teams which are based in Israel
    """
    return [team for team in teams if team[COUNTRY] == ISRAEL]


def get_team_to_years(team_number: int, api_key: str) -> tuple[tuple, ...]:
    """
    :param team_number: team number
    :param api_key: TBA API auth key
    :return: years the given team participated in, grouped by consecutive years
    """
    team_key = TEAM_KEY_TEMPLATE.substitute(team_number=team_number)
    endpoint = YEARS_PARTICIPATED_ENDPOINT.substitute(team_key=team_key)
    years_participated = send_api_request(endpoint, api_key)

    grouped_years = more_itertools.consecutive_groups(years_participated)
    # `itertools.consecutive_groups()` returns a generator, so we convert it to a tuple.
    grouped_years = tuple(map(tuple, grouped_years))
    return grouped_years


def get_formatted_year_spans(grouped_years: Sequence[Sequence[int]]) -> str:
    """
    Return a formatted string of grouped years.

    For example, the following groups: `((2001, 2002, 2003), (2005, 2006, 2007, 2008), (2010,))` will be formatted to
    `"2001-2003, 2005-2008, 2010"`.

    :param grouped_years: years grouped by consecutive years
    :return: a formatted version of the grouped years
    """
    year_spans = []
    for group in grouped_years:
        first_year = group[0]
        if len(group) == 1:
            # If a group has one year, i.e. has only "2010", write the year alone instead of "2010-2010".
            year_spans.append(str(first_year))
            continue
        last_year = group[-1]
        year_span = f"{first_year}-{last_year}"
        year_spans.append(year_span)
    return ", ".join(year_spans)
