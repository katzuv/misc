# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "plotly",
# ]
# ///

import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

    event_rows = []
    total_matches = 0

    logging.info("Traversing hierarchical raw cache data...")

    # Traverse: Week -> Event -> Match
    for week_label, events in season_data.items():
        for event_key, matches in events.items():
            event_total = 0
            for match_key, match_data in matches.items():
                # Check if the match actually has a score breakdown yet (was played)
                bd = match_data.get("score_breakdown")
                if bd and bd.get("blue") and "hubScore" in bd["blue"]:
                    # Dig into the raw TBA schema
                    event_total += bd["blue"]["hubScore"].get("totalCount", 0)
                    event_total += bd["red"]["hubScore"].get("totalCount", 0)
                    total_matches += 1

            if event_total > 0:
                event_rows.append(
                    {"Week": week_label, "Event": event_key, "Count": event_total}
                )

    if not event_rows:
        logging.warning("No valid match data found to graph.")
        return

    logging.info(
        f"Processed {total_matches} played matches across {len(season_data)} distinct weeks."
    )

    # Create DataFrames
    df_events = pd.DataFrame(event_rows)
    df_events["Week_Num"] = df_events["Week"].str.extract(r"(\d+)").astype(int)

    # Sort so the largest events are at the bottom of the stack
    df_events = df_events.sort_values(["Week_Num", "Count"], ascending=[True, False])

    # Secondary DataFrame for Cumulative
    df_weekly = df_events.groupby(["Week", "Week_Num"])["Count"].sum().reset_index()
    df_weekly = df_weekly.sort_values("Week_Num")
    df_weekly["Cumulative_Count"] = df_weekly["Count"].cumsum()

    # --- Plotting with Plotly ---
    logging.info("Generating interactive HTML plots...")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            "<b>FRC Hub Pieces Scored PER WEEK (Hover for Event Data)</b>",
            "<b>CUMULATIVE FRC Hub Pieces by Week</b>",
        ),
    )

    color_scale = [
        "#E3F2FD",
        "#BBDEFB",
        "#90CAF9",
        "#64B5F6",
        "#42A5F5",
        "#2196F3",
        "#1E88E5",
        "#1976D2",
        "#1565C0",
        "#0D47A1",
    ]

    for week_num in df_weekly["Week_Num"]:
        week_data = df_events[df_events["Week_Num"] == week_num]
        week_label = week_data["Week"].iloc[0]

        for i, (index, row) in enumerate(week_data.iterrows()):
            color = color_scale[i % len(color_scale)]

            hover_text = f"<b>Event:</b> {row['Event']}<br><b>Amount:</b> {row['Count']:,} pieces<extra></extra>"

            fig.add_trace(
                go.Bar(
                    x=[week_label],
                    y=[row["Count"]],
                    name=row["Event"],
                    marker_color=color,
                    marker_line_color="black",
                    marker_line_width=0.5,
                    hovertemplate=hover_text,
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

    fig.add_trace(
        go.Bar(
            x=df_weekly["Week"],
            y=df_weekly["Cumulative_Count"],
            marker_color="#ff6600",
            marker_line_color="black",
            marker_line_width=1,
            hovertemplate="<b>%{x}</b><br><b>Total Cumulative:</b> %{y:,} pieces<extra></extra>",
            showlegend=False,
            text=df_weekly["Cumulative_Count"].apply(lambda x: f"{x:,}"),
            textposition="outside",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        barmode="stack",
        height=900,
        plot_bgcolor="white",
        hovermode="closest",
        font=dict(family="Arial, sans-serif"),
    )

    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray", row=1, col=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray", row=2, col=1)

    max_weekly = df_weekly["Count"].max()
    max_cumulative = df_weekly["Cumulative_Count"].max()
    fig.update_yaxes(range=[0, max_weekly * 1.15], row=1, col=1)
    fig.update_yaxes(range=[0, max_cumulative * 1.15], row=2, col=1)

    logging.info("Opening dashboard in your web browser...")
    fig.show()


if __name__ == "__main__":
    main()
