import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding="utf-8")

console = Console()

FUND_NAMES = {
    "5103510": "IBI Shekel Money Market Fund",
    "5117700": "Ayalon Money Market Fund",
    "5135926": "Meitav Money Market Fund",
}


def load_transactions():
    data_dir = Path(__file__).parent / "investments_data"
    all_txs = []

    for yaml_path in sorted(data_dir.glob("*.yaml")):
        with open(yaml_path, encoding="utf-8") as f:
            txs = yaml.safe_load(f)
            if txs:
                all_txs.extend(txs)

    return all_txs


def main():
    txs = load_transactions()

    # Group transactions by fund
    funds = {}
    for tx in txs:
        fid = tx["fund_id"]
        if fid not in funds:
            funds[fid] = {
                "name": FUND_NAMES.get(fid, tx["fund_name"]),
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
            "[gray]Calculated using: Current Value + All Sales - All Buys - All Taxes[/gray]",
            border_style="cyan",
        )
    )

    for fid, data in funds.items():
        name = data["name"]

        # Aggregate buys, sells and taxes
        total_buys = sum(abs(tx["amount"]) for tx in data["buys"])
        total_sells = sum(tx["amount"] for tx in data["sells"])
        total_tax = sum(abs(tx["tax"]) for tx in data["sells"])

        # Calculate remaining units
        total_bought_qty = sum(tx["qty"] for tx in data["buys"])
        total_sold_qty = sum(abs(tx["qty"]) for tx in data["sells"])

        # Account for bank transfers (which move shares but are not sells)
        transferred_qty = sum(tx["qty"] for tx in data["transfers"])

        # Net units held
        net_qty = total_bought_qty - total_sold_qty + transferred_qty

        # Determine current value
        if fid == "5103510":  # IBI Fund
            # The user explicitly provided the current balance of 75,882 ILS
            current_value = 75882.00
        elif net_qty > 0:
            # For Meitav, calculate from remaining units and last known price from video (11.6615 ILS)
            last_price = 11.6615
            current_value = net_qty * last_price
        else:
            current_value = 0.00

        # Total earnings formula: Current Value + Sales - Buys - Tax
        net_earnings = current_value + total_sells - total_buys - total_tax

        console.print(f"\n[bold yellow]Security: {fid} - {name}[/bold yellow]")

        # Details Table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", justify="left")
        table.add_column("Value (ILS)", justify="right")
        table.add_column("Description", justify="left")

        table.add_row(
            "Total Buys (Cost)",
            f"{total_buys:,.2f}",
            f"Total capital invested ({total_bought_qty:,.0f} units)",
        )
        table.add_row(
            "Total Sells (Proceeds)",
            f"{total_sells:,.2f}",
            f"Capital realized from sales ({total_sold_qty:,.0f} units)",
        )
        table.add_row(
            "Total Tax Paid",
            f"{total_tax:,.2f}",
            "Actual withholding tax deducted by the bank (calculated after inflation)",
        )
        table.add_row(
            "Current Held Quantity",
            f"{net_qty:,.0f} units",
            "Active position currently held",
        )
        table.add_row(
            "Current Value",
            f"{current_value:,.2f}",
            "Current market value of held units",
        )

        pnl_style = "green" if net_earnings >= 0 else "red"
        table.add_row(
            "[bold]Total Net Earnings[/bold]",
            f"[{pnl_style}][bold]{net_earnings:+,.2f}[/bold][/{pnl_style}]",
            "[bold]Overall profit after all buys, sells, current balance, and taxes[/bold]",
        )

        console.print(table)

        # Note about inflation-adjusted tax
        console.print(
            "[gray]Note: The tax values shown here are the actual taxes withheld at source by the bank.\n"
            "By Israeli tax law, the bank automatically adjusts your purchase cost basis for inflation (CPI)\n"
            "before calculating and deducting the 25% capital gains tax. Hence, the tax is already net of inflation.[/gray]\n"
        )


if __name__ == "__main__":
    main()
