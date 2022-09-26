import itertools
import string
import urllib.parse

import requests


AUTH_KEY_HEADER = "X-TBA-Auth-Key"
API_BASE_URL = "https://www.thebluealliance.com/api/v3/"
TEAMS_SIMPLE_ENDPOINT = string.Template("teams/$page_number/simple")


def send_api_request(endpoint: str, api_key: str) -> dict:
    """
    Send a GET request to The Blue Alliance API and return its response.

    :param endpoint: endpoint to send request to
    :param api_key: API key to access the API with
    :return: response body
    :raises: requests.HTTPError if an error occurred
    """
    url = urllib.parse.urljoin(API_BASE_URL, endpoint)
    response = requests.get(url, headers={AUTH_KEY_HEADER: api_key})
    response.raise_for_status()
    return response.json()


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
