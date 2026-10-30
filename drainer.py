"""Drain sequence with live row-by-row animation."""
import time

from rich.box import SIMPLE
from rich.console import Console, Group
from rich.live import Live
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

import config
import ui


DRAIN_STEPS = [
    "Initializing secure channel…",
    "Reading wallet state…",
    "Verifying asset ownership…",
    "Building transfer batch…",
    "Broadcasting transaction…",
    "Awaiting confirmation…",
]


def _drain_header(state: dict, status: str) -> Text:
    t = Text()
    t.append("  ⚡ Draining assets\n", style="bold bright_red")
    t.append(f"  {state['short_addr']}  ", style="dim")
    t.append(f"→  {config.short_addr(config.DEMO_RECIPIENT)}", style="dim")
    t.append(f"\n\n  {status}", style="bright_yellow")
    return t


def _build_status_table(assets, drained, running_total) -> Table:
    t = Table(
        box=SIMPLE, show_header=True,
        header_style="bold bright_black", pad_edge=False, expand=True,
    )
    t.add_column("", width=2)
    t.add_column("Asset", style="bright_white")
    t.add_column("Amount", justify="right")
    t.add_column("Value", justify="right")
    t.add_column("Status", width=12)

    drained_syms = {a["symbol"] for a in drained}
    for a in assets:
        done = a["symbol"] in drained_syms
        if done:
            t.add_row(
                f"[dim]{a['letter']}[/]",
                f"[dim]{a['name']}[/]",
                f"[dim]{a['fmt_balance']}[/]",
                f"[dim]{a['fmt_usd']}[/]",
                "[bright_red]drained ✓[/]",
            )
        else:
            t.add_row(
                f"[{a['color']}]{a['letter']}[/]",
                a["name"],
                a["fmt_balance"],
                a["fmt_usd"],
                "[bright_yellow]pending[/]",
            )
    return t


def _status_footer(running_total: float) -> Text:
    t = Text()
    t.append("  Total drained:  ", style="dim")
    t.append(config.fmt_usd(running_total), style="bold bright_red")
    return t


def run_drain(console: Console, state: dict) -> dict | None:
    ui.render_dashboard(console, state)

    if not ui.render_claim_prompt(console):
        return None

    if not ui.render_approval_dialog(console):
        console.print("\n[dim]approval rejected.[/]\n")
        return None

    console.print()
    console.print(Rule("[bold bright_red]draining[/]", style="bright_red"))
    console.print()

    assets = sorted(state["assets"], key=lambda a: a["usd"], reverse=True)
    drained: list[dict] = []
    running_total = 0.0

    with Live(console=console, refresh_per_second=20, transient=False) as live:
        for step in DRAIN_STEPS:
            live.update(Group(
                _drain_header(state, step),
                Text(),
                _build_status_table(assets, drained, running_total),
                Text(),
                _status_footer(running_total),
            ))
            time.sleep(0.32)

        for i, asset in enumerate(assets):
            drained.append(asset)
            running_total += asset["usd"]
            live.update(Group(
                _drain_header(state, f"Drained {i+1}/{len(assets)}…"),
                Text(),
                _build_status_table(assets, drained, running_total),
                Text(),
                _status_footer(running_total),
            ))
            time.sleep(0.22)

        live.update(Group(
            _drain_header(state, "Finalizing…"),
            Text(),
            _build_status_table(assets, drained, running_total),
            Text(),
            _status_footer(running_total),
        ))
        time.sleep(0.9)

    return {
        "state": state,
        "drained": drained,
        "total_usd": running_total,
        "fmt_total": config.fmt_usd(running_total),
        "tx_hash": config.fake_tx_hash(),
        "block": config.fake_block(),
        "recipient": config.DEMO_RECIPIENT,
    }
