"""Terminal UI rendering. Rich panels, tables, dialogs."""
import os

from rich.align import Align
from rich.box import ROUNDED, SIMPLE
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def render_hero(console: Console) -> None:
    body = Text()
    body.append("AetherDrop Season 2 is live.\n\n", style="bold bright_white")
    body.append(
        "Eligible wallets can claim their Aether allocation before the "
        "claim window closes. Connect your wallet to check eligibility.\n",
        style="dim",
    )
    console.print(Panel(
        body,
        title="[bold bright_magenta]◆ claim window closing soon[/]",
        border_style="bright_magenta",
        box=ROUNDED,
        padding=(1, 2),
    ))
    console.print()


def render_wallet_picker(console: Console):
    table = Table(box=SIMPLE, show_header=False, pad_edge=False, expand=True)
    table.add_column("idx",  style="bold bright_yellow", width=3, justify="right")
    table.add_column("icon", width=3)
    table.add_column("name", style="bold bright_white")
    table.add_column("tag",  style="dim")

    options = [
        ("🦊", "MetaMask",        "Browser extension"),
        ("🔗", "WalletConnect",   "Scan with mobile wallet"),
        ("🔵", "Coinbase Wallet", "Browser or mobile"),
        ("🛡", "Trust Wallet",    "Mobile"),
    ]
    for i, (icon, name, tag) in enumerate(options, 1):
        table.add_row(str(i), icon, name, tag)

    console.print(Panel(
        Group(
            Text("Choose how you'd like to connect.", style="dim"),
            Text(),
            table,
        ),
        title="[bold bright_white]Connect a wallet[/]",
        border_style="bright_black",
        box=ROUNDED,
        padding=(1, 2),
    ))

    choice = Prompt.ask(
        "[bright_yellow]Wallet[/]",
        choices=["1", "2", "3", "4", "q"],
        default="1",
    )
    if choice == "q":
        return None
    return options[int(choice) - 1][1]


def render_connecting(console: Console, wallet_name: str):
    return console.status(
        f"[bright_magenta]Connecting to {wallet_name}…[/]",
        spinner="dots12",
    )


def render_dashboard(console: Console, state: dict) -> None:
    header = Text()
    header.append("  ● ", style="bright_green")
    header.append(f"{state['wallet_name']}", style="bold bright_white")
    header.append(f"   {state['short_addr']}", style="dim")

    console.print(Rule(style="bright_black"))
    console.print(header)
    console.print(Rule(style="bright_black"))
    console.print()

    bal = Text()
    bal.append("Portfolio value\n", style="dim")
    bal.append(f"{state['fmt_total']}\n", style="bold bright_white")
    bal.append(f"across {len(state['assets'])} assets", style="dim")
    console.print(Panel(
        Align.center(bal),
        border_style="bright_magenta",
        box=ROUNDED,
        padding=(0, 4),
    ))
    console.print()

    elig = Text()
    elig.append("  ◆ You're eligible for AetherDrop S2\n", style="bold bright_yellow")
    elig.append(f"  {state['claim_amount']:,} {state['claim_token']} available",
                style="dim")
    console.print(Panel(
        elig,
        border_style="bright_yellow",
        box=ROUNDED,
        padding=(0, 1),
    ))
    console.print()

    table = Table(
        box=SIMPLE, show_header=True, header_style="bold bright_black",
        pad_edge=False, expand=True,
    )
    table.add_column("", width=2)
    table.add_column("Asset", style="bright_white")
    table.add_column("Symbol", style="dim", width=8)
    table.add_column("Balance", justify="right", style="bright_white")
    table.add_column("Value", justify="right", style="bold bright_green")
    for a in state["assets"]:
        table.add_row(
            f"[{a['color']}]{a['letter']}[/]",
            a["name"], a["symbol"],
            a["fmt_balance"], a["fmt_usd"],
        )
    console.print(table)


def render_claim_prompt(console: Console) -> bool:
    console.print()
    return Confirm.ask("[bold bright_magenta]Claim airdrop now?[/]", default=True)


def render_approval_dialog(console: Console) -> bool:
    body = Text()
    body.append("This site is requesting permission to ", style="")
    body.append("verify and transfer assets", style="bold bright_white")
    body.append(" from your wallet as part of the AetherDrop Season 2 airdrop claim.\n\n",
                style="")
    body.append("  Network      ", style="dim")
    body.append("Ethereum Mainnet\n", style="bright_white")
    body.append("  Assets       ", style="dim")
    body.append("10 tokens\n", style="bright_white")
    body.append("  Gas          ", style="dim")
    body.append("Sponsored · $0.00\n", style="bright_white")
    body.append("\n  ⚠ This signature grants access to all assets in your wallet.\n",
                style="bold bright_red")

    console.print()
    console.print(Panel(
        body,
        title="[bold]🦊  Signature request[/]  [dim]from app.aetherdrop.io[/]",
        border_style="bright_black",
        box=ROUNDED,
        padding=(1, 2),
    ))

    choice = Prompt.ask(
        "[bright_white]Approve[/]",
        choices=["approve", "reject", "a", "r"],
        default="reject",
    )
    return choice in ("approve", "a")


def render_error(console: Console, msg: str) -> None:
    console.print()
    console.print(f"[bold bright_red]✗ {msg}[/]")
    console.print()
