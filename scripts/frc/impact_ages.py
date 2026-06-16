# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "requests",
#     "matplotlib",
#     "numpy",
# ]
# ///

import requests
import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path

# --- CONFIGURATION ---
# Insert your Read API Key from thebluealliance.com/account
TBA_AUTH_KEY = "YOUR_API_KEY_HERE"
HEADERS = {"X-TBA-Auth-Key": TBA_AUTH_KEY}
BASE_URL = "https://www.thebluealliance.com/api/v3"
CACHE_FILE = Path("tba_cache.json")


def load_cache():
    """Load the API cache from disk if it exists using pathlib."""
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    """Save the API cache to disk using pathlib."""
    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


# Initialize global cache
api_cache = load_cache()


def fetch_tba(url):
    """Fetch from TBA, using the local cache if available."""
    if url in api_cache:
        return api_cache[url]

    response = requests.get(url, headers=HEADERS)

    if response.ok:
        data = response.json()
        api_cache[url] = data
        return data

    # Catch authentication errors so we don't fail silently
    if response.status_code == 401:
        print(
            "❌ API Auth Error (401). Did you replace 'YOUR_API_KEY_HERE' with a real TBA Read API Key?"
        )
    else:
        print(f"⚠️ Warning: Got status {response.status_code} for {url}")

    return None


def get_team_rookie_year(team_key):
    """Fetch the rookie year for a given team."""
    url = f"{BASE_URL}/team/{team_key}"
    data = fetch_tba(url)
    if data:
        return data.get("rookie_year")
    return None


def main():
    current_year = 2026
    years = range(1992, current_year + 1)

    # Store aggregated age data per year
    data = {}

    for year in years:
        if year == 2020:
            continue

        print(f"Polling data for {year}...")

        events_url = f"{BASE_URL}/events/{year}/simple"
        events = fetch_tba(events_url)
        if not events:
            continue

        # event_type == 4 refers to Championship Finals (Einstein).
        # For 2017-2019, this cleanly catches BOTH Championships.
        cmp_events = [e for e in events if e.get("event_type") == 4]

        data[year] = {"winners": [], "finalists": []}

        for cmp_event in cmp_events:
            awards_url = f"{BASE_URL}/event/{cmp_event['key']}/awards"
            awards = fetch_tba(awards_url) or []

            for award in awards:
                award_type = award.get("award_type")

                # 0: Winner, 69: Finalist
                if award_type in (0, 69):
                    for recipient in award.get("recipient_list", []):
                        team_key = recipient.get("team_key")
                        if team_key:
                            rookie_year = get_team_rookie_year(team_key)

                            if rookie_year:
                                age = year - rookie_year
                                if award_type == 0:
                                    data[year]["winners"].append(age)
                                else:
                                    data[year]["finalists"].append(age)

    # Save all new API calls to disk
    save_cache(api_cache)
    print("Data collection complete. Cache saved.")

    # --- Plotting the Data ---
    years_plotted = []

    winners_x, winners_y, winners_labels = [], [], []
    finalists_x, finalists_y, finalists_labels = [], [], []
    averages_x, averages_y = [], []
    average_text_labels = []  # To store the overall average text to place below stars

    for year in sorted(data.keys()):
        w_data = data[year]["winners"]
        f_data = data[year]["finalists"]

        if not w_data and not f_data:
            continue

        years_plotted.append(year)

        for age in w_data:
            winners_x.append(year)
            winners_y.append(age)
            winners_labels.append(str(age))

        for age in f_data:
            finalists_x.append(year)
            finalists_y.append(age)
            finalists_labels.append(str(age))

        # Calculate the average age for the year (ALL finalists + ALL winners across ALL CMPs)
        all_ages = w_data + f_data
        if all_ages:
            overall_avg = np.mean(all_ages)
            averages_x.append(year)
            averages_y.append(overall_avg)

            # Record the overall average to be printed below the lowest winner's star
            if w_data:
                bottom_winner_age = min(w_data)
                average_text_labels.append(
                    {
                        "year": year,
                        "y": bottom_winner_age,
                        "text": f"Avg: {overall_avg:.1f}",
                    }
                )

    # Safety guard against an empty dataset
    if not years_plotted:
        print(
            "\n❌ Error: No data points were collected. The graph cannot be generated."
        )
        print("Please verify your API key and network connection, then try again.")
        return

    plt.figure(figsize=(15, 8))

    # Plot Finalists
    if finalists_x:
        plt.scatter(
            finalists_x,
            finalists_y,
            color="gray",
            alpha=0.6,
            s=50,
            label="Finalists' Ages",
        )
        # Add age annotations for finalists
        for i, txt in enumerate(finalists_labels):
            plt.annotate(
                txt,
                (finalists_x[i], finalists_y[i]),
                xytext=(6, 0),
                textcoords="offset points",
                fontsize=8,
                color="dimgray",
                va="center",
            )

    # Highlight Winners
    if winners_x:
        plt.scatter(
            winners_x,
            winners_y,
            color="gold",
            edgecolor="black",
            s=250,
            zorder=5,
            marker="*",
            label="Winner's Age",
        )
        # Add age annotations for winners
        for i, txt in enumerate(winners_labels):
            plt.annotate(
                txt,
                (winners_x[i], winners_y[i]),
                xytext=(12, 0),
                textcoords="offset points",
                fontsize=11,
                fontweight="bold",
                color="black",
                va="center",
                zorder=6,
            )

    # Trend Line for Average Age
    if averages_x:
        plt.plot(
            averages_x,
            averages_y,
            color="#0066cc",
            linestyle="--",
            alpha=0.8,
            linewidth=2,
            label="Average Age (All Candidates)",
        )

    # Overall Average Label below Winners
    for label in average_text_labels:
        plt.annotate(
            label["text"],
            (label["year"], label["y"]),
            xytext=(0, -18),
            textcoords="offset points",
            fontsize=9,
            fontstyle="italic",
            color="#8B6508",
            ha="center",
            va="top",
            zorder=6,
        )

    # Formatting
    plt.title(
        "FIRST Impact Award Winner & Finalist Ages Over Time", fontsize=16, pad=15
    )
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Team Age (Years Since Rookie Year)", fontsize=12)
    plt.xticks(np.arange(min(years_plotted), max(years_plotted) + 1, 2), rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # 2015 marker
    plt.axvline(
        x=2015,
        color="red",
        linestyle=":",
        alpha=0.5,
        label="Finalist Model Introduced (2015)",
    )

    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
