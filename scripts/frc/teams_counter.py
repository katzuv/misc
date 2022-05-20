import itertools
import string
import urllib.parse

import requests


AUTH_KEY_HEADER = "X-TBA-Auth-Key"
API_BASE_URL = "https://www.thebluealliance.com/api/v3/"
TEAMS_SIMPLE_ENDPOINT = string.Template("teams/$page_number/simple")
YEARS_PARTICIPATED_ENDPOINT = string.Template("team/$team_key/years_participated")
TEAM_KEY_TEMPLATE = string.Template("frc$team_number")

COUNTRY = "country"
ISRAEL = "Israel"
TEAM_NUMBER = "team_number"


def get_all_teams(api_key: str) -> list[dict]:
    """
    :param api_key: TBA API auth key
    :return: list of all teams
    """
    teams = []
    for page_number in itertools.count():
        url = urllib.parse.urljoin(
            API_BASE_URL, TEAMS_SIMPLE_ENDPOINT.substitute(page_number=page_number)
        )
        response = requests.get(url, headers={AUTH_KEY_HEADER: api_key})
        paged_teams = response.json()
        if not paged_teams:
            break
        teams.extend(paged_teams)

    return teams


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
    url = urllib.parse.urljoin(
        API_BASE_URL, YEARS_PARTICIPATED_ENDPOINT.substitute(team_key=team_key)
    )
    response = requests.get(url, headers={AUTH_KEY_HEADER: api_key})
    years_participated = response.json()

    grouped_years = more_itertools.consecutive_groups(years_participated)
    # `itertools.consecutive_groups()` returns a generator, so we convert it to a tuple.
    grouped_years = tuple(map(tuple, grouped_years))
    return grouped_years
