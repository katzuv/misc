# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

import os
import requests
import json

TBA_API_KEY = os.environ.get("TBA_API_KEY")
YEAR = 2026
BASE_URL = "https://www.thebluealliance.com/api/v3"

if not TBA_API_KEY:
    raise ValueError(
        "TBA_API_KEY environment variable is not set. Please set it before running."
    )

HEADERS = {"X-TBA-Auth-Key": TBA_API_KEY, "accept": "application/json"}


def main():
    print(f"Fetching official events for {YEAR}...")
    events_resp = requests.get(f"{BASE_URL}/events/{YEAR}", headers=HEADERS)
    events_resp.raise_for_status()
    events = events_resp.json()

    # Look for the first official event (has a 'week' assigned) that has match data
    for event in events:
        if event.get("week") is not None:
            event_key = event["key"]

            matches_resp = requests.get(
                f"{BASE_URL}/event/{event_key}/matches", headers=HEADERS
            )
            if matches_resp.status_code == 200:
                matches = matches_resp.json()

                # Find the first match that actually has a score breakdown populated
                for match in matches:
                    if match.get("score_breakdown"):
                        print(
                            f"\nFound match data in event: {event_key} (Match: {match['key']})"
                        )
                        print("\n--- 2026 Score Breakdown Schema ---")
                        # We only need one alliance's breakdown to see the schema
                        blue_schema = match["score_breakdown"].get("blue", {})
                        print(json.dumps(blue_schema, indent=2))
                        return

    print(
        f"Could not find any {YEAR} matches that have a populated score breakdown yet."
    )


if __name__ == "__main__":
    main()
