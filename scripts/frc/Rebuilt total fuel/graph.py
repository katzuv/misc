# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "matplotlib",
# ]
# ///

import json
import pandas as pd
import matplotlib.pyplot as plt
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

INPUT_FILE = Path("frc_2026_cache.json")


def main():
    if not INPUT_FILE.exists():
        logging.error(f"Could not find {INPUT_FILE.name}.")
        raise FileNotFoundError(
            "Please run the fetch script first to generate the cache."
        )

    logging.info(f"Loading data from {INPUT_FILE.resolve()}...")

    file_content = INPUT_FILE.read_text(encoding="utf-8")
    season_data = json.loads(file_content)

    if not season_data:
        logging.warning("The cache file is empty. Exiting.")
        return

    weekly_totals = {}
    total_matches = 0

    logging.info("Traversing hierarchical cache data...")

    # Traverse the hierarchy: Week -> Event -> Match
    for week_label, events in season_data.items():
        for event_key, matches in events.items():
            for match_key, match_data in matches.items():
                blue_total = match_data["blue_alliance"]["total_count"]
                red_total = match_data["red_alliance"]["total_count"]

                match_total = blue_total + red_total
                weekly_totals[week_label] = (
                    weekly_totals.get(week_label, 0) + match_total
                )
                total_matches += 1

    logging.info(
        f"Processed {total_matches} matches across {len(weekly_totals)} distinct weeks."
    )

    # Convert to DataFrame
    df = pd.DataFrame(list(weekly_totals.items()), columns=["Week", "Weekly_Count"])

    if df.empty:
        logging.warning("No valid match data found to graph.")
        return

    df["Week_Num"] = df["Week"].str.extract(r"(\d+)").astype(int)
    df = df.sort_values("Week_Num").drop("Week_Num", axis=1)

    # Cumulative Sum
    df["Cumulative_Count"] = df["Weekly_Count"].cumsum()

    logging.info("\n--- Final Aggregated Match Data ---")
    print(df.to_string(index=False))

    # --- Plotting ---
    logging.info("Generating plots...")

    # Create a figure with 2 subplots (stacked vertically)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # --- Top Subplot: Non-Cumulative (Weekly Total) ---
    bars1 = ax1.bar(df["Week"], df["Weekly_Count"], color="#0073e6", edgecolor="black")

    for bar in bars1:
        yval = bar.get_height()
        if yval > 0:
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                yval + (yval * 0.015),
                f"{int(yval):,}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    ax1.set_title(
        "FRC Hub Pieces Scored PER WEEK (2026)", fontsize=14, fontweight="bold"
    )
    ax1.set_ylabel("Pieces Scored", fontsize=12)
    ax1.set_ylim(0, df["Weekly_Count"].max() * 1.15)  # Buffer for text
    ax1.grid(axis="y", linestyle="--", alpha=0.7)

    # --- Bottom Subplot: Cumulative ---
    bars2 = ax2.bar(
        df["Week"], df["Cumulative_Count"], color="#ff6600", edgecolor="black"
    )

    for bar in bars2:
        yval = bar.get_height()
        if yval > 0:
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                yval + (yval * 0.015),
                f"{int(yval):,}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    ax2.set_title(
        "CUMULATIVE FRC Hub Pieces by Week (2026)", fontsize=14, fontweight="bold"
    )
    ax2.set_xlabel("Competition Week", fontsize=12)
    ax2.set_ylabel("Cumulative Pieces Scored", fontsize=12)
    ax2.set_ylim(0, df["Cumulative_Count"].max() * 1.15)
    ax2.grid(axis="y", linestyle="--", alpha=0.7)

    # Adjust spacing so they don't overlap
    plt.tight_layout()

    logging.info("Displaying plot window.")
    plt.show()


if __name__ == "__main__":
    main()
