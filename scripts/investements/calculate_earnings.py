import csv
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding="utf-8")

console = Console()


def load_standings():
    standings_path = Path(__file__).parent / "data" / "standings.csv"
    standings = {}
    if standings_path.exists():
        with open(standings_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                standings[row["security_id"]] = {
                    "current_value": float(row["current_value"]),
                    "description": row["description"],
                }
    return standings


def load_transactions_from_csv():
    csv_path = Path(__file__).parent / "data" / "transactions.csv"
    txs = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            txs.append(
                {
                    "date": row["date"],
                    "type": row["type"],
                    "amount": float(row["amount"]),
                    "tax": float(row["tax"]),
                    "security_id": row["security_id"],
                    "security_name": row["security_name"],
                }
            )

    return txs


def main():
    txs = load_transactions_from_csv()
    standings = load_standings()

    # Group transactions by fund ID
    funds = {}
    for tx in txs:
        fid = tx["security_id"]
        if fid not in funds:
            funds[fid] = {
                "name": tx["security_name"],
                "buys": [],
                "sells": [],
                "transfers": [],
            }

        if tx["type"] == "Buy":
            funds[fid]["buys"].append(tx)
        elif tx["type"] == "Sell":
            funds[fid]["sells"].append(tx)
        elif tx["type"] == "Bank Transfer":
            funds[fid]["transfers"].append(tx)

    console.print(
        Panel.fit(
            "[bold cyan]Money Market Funds - Overall Earnings & Tax Report[/bold cyan]\n"
            "[gray]Parsed from transactions.csv & standings.csv (Current Value + All Sales - All Buys - All Taxes)[/gray]",
            border_style="cyan",
        )
    )

    # Sort funds by ID for consistent output ordering
    for fid in sorted(funds.keys()):
        data = funds[fid]
        name = data["name"]

        # Aggregate buys, sells, and taxes
        total_buys = sum(abs(tx["amount"]) for tx in data["buys"])
        total_sells = sum(tx["amount"] for tx in data["sells"])
        total_tax = sum(abs(tx["tax"]) for tx in data["sells"])

        # Determine current value from standings.csv
        held_info = standings.get(
            fid, {"current_value": 0.00, "description": "No standing details found"}
        )
        current_value = held_info["current_value"]
        value_desc = held_info["description"]

        # Total earnings formula: Current Value + Sales - Buys - Tax
        net_earnings = current_value + total_sells - total_buys - total_tax

        console.print(f"\n[bold yellow]Security: {fid} - {name}[/bold yellow]")

        # Details Table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", justify="left")
        table.add_column("Value (ILS)", justify="right")
        table.add_column("Description", justify="left")

        table.add_row(
            "Total Buys (Cost)", f"{total_buys:,.2f}", "Total capital invested"
        )
        table.add_row(
            "Total Sells (Proceeds)",
            f"{total_sells:,.2f}",
            "Capital realized from sales",
        )
        table.add_row(
            "Total Tax Paid",
            f"{total_tax:,.2f}",
            "Actual withholding tax deducted by bank (already net of inflation)",
        )
        table.add_row("Current Value", f"{current_value:,.2f}", value_desc)

        pnl_style = "green" if net_earnings >= 0 else "red"
        table.add_row(
            "[bold]Total Net Earnings[/bold]",
            f"[{pnl_style}][bold]{net_earnings:+,.2f}[/bold][/{pnl_style}]",
            "[bold]Overall profit after all buys, sells, current balance, and taxes[/bold]",
        )

        console.print(table)

    # Note about inflation-adjusted tax
    console.print(
        "[i][gray]Note: The tax values shown here are the actual taxes withheld at source by the bank.\n"
        "By Israeli tax law, the bank automatically adjusts your purchase cost basis for inflation (CPI)\n"
        "before calculating and deducting the 25% capital gains tax. Hence, the tax is already net of inflation.[/gray][/i]\n"
    )


if __name__ == "__main__":
    main()
