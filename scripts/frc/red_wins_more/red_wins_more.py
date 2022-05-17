import collections
import pathlib
import string
import urllib.parse

import click
import requests


AUTH_KEY_HEADER = "X-TBA-Auth-Key"
API_BASE_URL = "https://www.thebluealliance.com/api/v3/"
MATCHES_SIMPLE_ENDPOINT = string.Template("event/$event_key/matches/simple")
ANALYSIS_RESULT_TEMPLATE = string.Template(
    pathlib.Path("analysis_result.txt").read_text()
)

CONTEXT = {"help_option_names": ["-h", "--help"]}

COMP_LEVEL = "comp_level"
QUALIFICATION_MATCH = "qm"
WINNING_ALLIANCE = "winning_alliance"
RED = "red"
BLUE = "blue"


def _calculate_percent(dividend, divisor, ndigits=None):
    """
    :param dividend:
    :param divisor:
    :param ndigits: number of digits to round to; if None, round to the nearest integer
    :return: quotient in percents
    """
    return round((dividend / divisor) * 100, ndigits)


def red_wins_more(event_key: str, matches: list[dict]) -> str:
    """
    :param event_key: TBA event key
    :param matches: simple list of matches in played in the event
    :return:
    """
    wins = collections.defaultdict(int)
    for match in matches:
        if match[COMP_LEVEL] != QUALIFICATION_MATCH:
            continue
        winning_alliance = match[WINNING_ALLIANCE]
        wins[winning_alliance] += 1

    red_wins = wins[RED]
    blue_wins = wins[BLUE]
    total_matches_amount = red_wins + blue_wins
    difference = red_wins - blue_wins

    red_wins_percent = _calculate_percent(red_wins, total_matches_amount)
    blue_wins_percent = _calculate_percent(blue_wins, total_matches_amount)

    return ANALYSIS_RESULT_TEMPLATE.substitute(
        total=total_matches_amount,
        event_key=event_key,
        red_wins=red_wins,
        red_wins_percent=red_wins_percent,
        blue_wins=blue_wins,
        blue_wins_percent=blue_wins_percent,
        difference=difference,
    )


@click.command(context_settings=CONTEXT)
@click.option("-e", "--event", "event_key", required=True, help="TBA event key")
@click.option(
    "-k",
    "--key",
    "api_key",
    required=True,
    prompt=True,
    hide_input=True,
    envvar="TBA_AUTH_KEY",
    show_envvar=True,
    help="TBA API authorization key",
)
def cli(event_key, api_key):
    """
    :param event_key: TBA event key
    :param api_key: auth key to access the TBA's API
    :return: simple matches list from the event
    """
    url = urllib.parse.urljoin(
        API_BASE_URL, MATCHES_SIMPLE_ENDPOINT.substitute(event_key=event_key)
    )
    response = requests.get(url, headers={AUTH_KEY_HEADER: api_key})
    response.raise_for_status()

    matches = response.json()
    click.echo(red_wins_more(event_key, matches))


if __name__ == "__main__":
    cli()
