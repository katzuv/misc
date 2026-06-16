# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%H:%M:%S"
)

# --- Configuration ---
INPUT_FILE = Path("frc_2026_cache.json")
TARGET_RP = 6


def main():
    if not INPUT_FILE.exists():
        logging.error(f"Could not find {INPUT_FILE.name}.")
        raise FileNotFoundError(
            "Please run the fetch script first to generate the cache."
        )

    logging.info(f"Loading local cache from {INPUT_FILE.resolve()}...")
    file_content = INPUT_FILE.read_text(encoding="utf-8")
    season_data = json.loads(file_content)

    if not season_data:
        logging.warning("The cache file is empty. Exiting.")
        return

    found_matches = []
    total_scanned = 0

    logging.info(f"Scanning cache for matches with {TARGET_RP}+ RP...")

    # Traverse the hierarchy: Week -> Event -> Match
    for week_label, events in season_data.items():
        for event_key, matches in events.items():
            for match_key, match in matches.items():
                total_scanned += 1

                # Check if the match has a score breakdown
                if not match.get("score_breakdown"):
                    continue

                # Check both alliances
                for color in ["red", "blue"]:
                    breakdown = match["score_breakdown"].get(color, {})
                    rp = breakdown.get("rp", 0)

                    if rp >= TARGET_RP:
                        # Extract YouTube link if it exists
                        yt_link = "No video available"
                        if match.get("videos"):
                            for vid in match["videos"]:
                                if vid.get("type") == "youtube":
                                    yt_link = f"https://www.youtube.com/watch?v={vid.get('key')}"
                                    break

                        tba_link = (
                            f"https://www.thebluealliance.com/match/{match['key']}"
                        )

                        found_matches.append(
                            {
                                "event": event_key,
                                "match_key": match["key"],
                                "alliance": color.upper(),
                                "rp": rp,
                                "tba_link": tba_link,
                                "yt_link": yt_link,
                            }
                        )

    print("\n" + "=" * 60)
    print(f"Scanned {total_scanned:,} total matches from local cache.")

    if not found_matches:
        print(f"❌ No matches found with {TARGET_RP} or more RP.")
    else:
        print(f"🔥 FOUND {len(found_matches)} MATCH(ES) WITH {TARGET_RP}+ RP! 🔥")
        print("=" * 60)
        for match in found_matches:
            print(f"Match:    {match['match_key']}")
            print(f"Alliance: {match['alliance']} ({match['rp']} RP)")
            print(f"TBA:      {match['tba_link']}")
            print(f"YouTube:  {match['yt_link']}")
            print("-" * 60)


if __name__ == "__main__":
    main()
