"""Wallet connect simulation. Spinner → return chosen wallet name."""
import time

from rich.console import Console

import ui


def connect_flow(console: Console) -> str | None:
    wallet = ui.render_wallet_picker(console)
    if wallet is None:
        return None

    with ui.render_connecting(console, wallet):
        time.sleep(1.2)

    console.print(f"[bright_green]✓ Connected via {wallet}[/]\n")
    time.sleep(0.4)
    return wallet
