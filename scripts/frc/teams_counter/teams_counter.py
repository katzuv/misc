import string

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
