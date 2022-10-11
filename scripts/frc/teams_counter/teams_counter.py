import os
import string

import more_itertools

from scripts.frc.tba_api_utils import send_api_request, get_all_teams
from scripts.frc.teams_counter.team import Team


TBA_AUTH_KEY_ENVVAR = "TBA_AUTH_KEY"

YEARS_PARTICIPATED_ENDPOINT = string.Template("team/$team_key/years_participated")
TEAM_KEY_TEMPLATE = string.Template("frc$team_number")

COUNTRY = "country"
ISRAEL = "Israel"
TEAM_NUMBER = "team_number"
TEAM_NAME = "nickname"
CITY = "city"


def get_israeli_teams(teams: list[dict]) -> list[dict]:
    """
    :param teams: list of teams
    :return: only teams which are based in Israel
    """
    return [team for team in teams if team[COUNTRY] == ISRAEL]


def get_team_to_years(team_number: int, api_key: str) -> tuple[tuple[int, int], ...]:
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


def get_teams_objects(teams: list[dict], tba_api_key: str) -> list[Team]:
    """
    :param teams: teams in dictionary form
    :param tba_api_key: API key to access the API with
    :return: list of teams as `Team` objects
    """
    teams_objects = []
    for team in teams:
        number = team[TEAM_NUMBER]
        name = team[TEAM_NAME]
        city = team[CITY]
        country = team[COUNTRY]
        year_spans = get_team_to_years(number, tba_api_key)

        team_object = Team(number, name, city, country, year_spans)
        teams_objects.append(team_object)
    return teams_objects


def main():
    """Run the program: get teams, calculate year spans, and print a list."""
    tba_api_key = os.environ[TBA_AUTH_KEY_ENVVAR]
    all_teams = get_all_teams(tba_api_key)
    israeli_teams_dict = get_israeli_teams(all_teams)

    israeli_teams = get_teams_objects(israeli_teams_dict, tba_api_key)

    for index, team in enumerate(israeli_teams, start=1):
        print(f"{index})\t{team}")


if __name__ == "__main__":
    main()
