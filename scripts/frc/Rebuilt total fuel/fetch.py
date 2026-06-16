# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///

import os
import asyncio
import httpx
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

TBA_API_KEY = os.environ.get("TBA_API_KEY")
YEAR = 2026
BASE_URL = "https://www.thebluealliance.com/api/v3"
OUTPUT_FILE = Path("frc_2026_cache.json")
MAX_CONCURRENT_REQUESTS = 60  # Blazing fast, but watch out for TBA rate limits!

if not TBA_API_KEY:
    logging.error("TBA_API_KEY environment variable is not set.")
    raise ValueError("Please export TBA_API_KEY before running.")

HEADERS = {"X-TBA-Auth-Key": TBA_API_KEY, "accept": "application/json"}


async def get_events(client: httpx.AsyncClient):
    logging.info(f"Fetching official events for the {YEAR} season...")
    resp = await client.get(f"{BASE_URL}/events/{YEAR}")
    resp.raise_for_status()
    return resp.json()


async def get_matches(client: httpx.AsyncClient, event_key: str):
    resp = await client.get(f"{BASE_URL}/event/{event_key}/matches")
    resp.raise_for_status()
    return resp.json()


async def process_event(
    client: httpx.AsyncClient, event: dict, semaphore: asyncio.Semaphore
):
    """Worker function to fetch and process a single event asynchronously."""
    week = event.get("week")
    event_type = event.get("event_type")

    # Handle TBA null weeks for CMP
    if week is None:
        if event_type in [3, 4]:
            week_label = "Week 8 (CMP)"
        else:
            return None  # Skip off-season
    else:
        week_label = f"Week {week + 1}"

    event_key = event["key"]

    async with semaphore:
        try:
            logging.info(f"Fetching matches for {event_key}...")
            matches = await get_matches(client, event_key)
        except Exception as e:
            logging.error(f"Failed to fetch matches for {event_key}: {e}")
            return None

        event_matches = {}
        for match in matches:
            # We are now saving the ENTIRE match object exactly as TBA provides it
            event_matches[match["key"]] = match

        if event_matches:
            logging.info(f" -> Processed {len(event_matches)} matches for {event_key}")
            return (week_label, event_key, event_matches)

    return None


async def async_main():
    timeout = httpx.Timeout(45.0)  # Increased timeout slightly for the high concurrency

    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout) as client:
        events = await get_events(client)

        logging.info(
            f"Found {len(events)} total events. Starting concurrent processing..."
        )

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        tasks = [process_event(client, event, semaphore) for event in events]
        results = await asyncio.gather(*tasks)

    season_data = {}
    total_matches_saved = 0

    for result in results:
        if result:
            week_label, event_key, event_matches = result

            if week_label not in season_data:
                season_data[week_label] = {}

            season_data[week_label][event_key] = event_matches
            total_matches_saved += len(event_matches)

    logging.info(f"Writing full raw hierarchical data to {OUTPUT_FILE.resolve()}...")
    OUTPUT_FILE.write_text(json.dumps(season_data, indent=2), encoding="utf-8")

    logging.info(
        f"✅ Successfully saved {total_matches_saved} full matches to {OUTPUT_FILE.name}"
    )


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
