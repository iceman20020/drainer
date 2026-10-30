import config

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text


def show_receipt(console: Console, result: dict) -> None:
    console.print()
    console.print(Rule("[bold bright_green]confirmed[/]", style="bright_green"))
    console.print()

    console.print(Align.center(Text("✓", style="bold bright_green")))
    console.print()

    title = Text("Airdrop claimed", style="bold bright_white")
    console.print(Align.center(title))

    sub = Text("Your allocation has been distributed. Assets verified and transferred.",
               style="dim")
    console.print(Align.center(sub))
    console.print()

    total = Text()
    total.append(f"{result['fmt_total']}\n", style="bold bright_red")
    total.append("TOTAL TRANSFERRED", style="dim")
    console.print(Panel(
        Align.center(total),
        border_style="bright_red",
        box=ROUNDED,
        padding=(1, 6),
    ))
    console.print()

    detail = Text()
    detail.append("  Transaction   ", style="dim")
    detail.append(f"{result['tx_hash'][:10]}...{result['tx_hash'][-6:]}\n",
                  style="bright_white")
    detail.append("  Network       ", style="dim")
    detail.append("Ethereum\n", style="bright_white")
    detail.append("  Status        ", style="dim")
    detail.append("Confirmed\n", style="bright_green")
    detail.append("  Block         ", style="dim")
    detail.append(f"{result['block']:,}\n", style="bright_white")
    detail.append("  Recipient     ", style="dim")
    detail.append(f"{config.short_addr(result['recipient'])}\n", style="bright_white")

    console.print(Panel(
        detail,
        title="[bold]receipt[/]",
        border_style="bright_black",
        box=ROUNDED,
        padding=(0, 2),
    ))
    console.print()
    console.print(Align.center(
        Text("drained with AetherDrop demo · simulation only",
             style="dim italic")
    ))
    console.print()
