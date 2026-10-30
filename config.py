"""Shared config: tokens, wallet state, demo addresses."""
import secrets
import time


DEMO_RECIPIENT = "0x4f2a8c1e9b7d3a5c6e8f0b2d4a6c8e0f2b4d6a8c"
CLAIM_TOKEN    = "AETH"
CLAIM_AMOUNT   = 1840

# (name, symbol, balance, usd_price, rich_color, letter)
TOKENS = [
    ("Ethereum",    "ETH",   1.8472,      3280.55,  "bright_blue",    "E"),
    ("USD Coin",    "USDC",  4210.88,     1.00,     "blue",           "$"),
    ("Tether",      "USDT",  3150.20,     1.00,     "green",          "T"),
    ("Wrapped BTC", "WBTC",  0.0412,      61240.00, "yellow",         "B"),
    ("Chainlink",   "LINK",  240.50,      18.42,    "bright_cyan",    "L"),
    ("Uniswap",     "UNI",   512.10,      11.87,    "magenta",        "U"),
    ("Aave",        "AAVE",  14.20,       142.30,   "purple",         "A"),
    ("Shiba Inu",   "SHIB",  84_200_000,  0.000032, "red",            "S"),
    ("Pepe",        "PEPE",  125_000_000, 0.000011, "bright_green",   "P"),
    ("Polygon",     "MATIC", 1840.00,     0.92,     "bright_magenta", "M"),
]


def fmt_balance(v: float) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.4f}".rstrip("0").rstrip(".")
    return f"{v:.8f}".rstrip("0").rstrip(".")


def fmt_usd(v: float) -> str:
    return f"${v:,.2f}" if v >= 1000 else f"${v:.2f}"


def short_addr(addr: str) -> str:
    return addr[:6] + "..." + addr[-4:]


def build_wallet_state(wallet_name: str) -> dict:
    addr = "0x" + secrets.token_hex(20)
    total = 0.0
    assets = []
    for name, sym, bal, price, color, letter in TOKENS:
        usd = bal * price
        total += usd
        assets.append({
            "name": name, "symbol": sym,
            "balance": bal, "price": price, "usd": usd,
            "color": color, "letter": letter,
            "fmt_balance": fmt_balance(bal),
            "fmt_usd": fmt_usd(usd),
        })
    return {
        "wallet_name": wallet_name,
        "addr": addr,
        "short_addr": short_addr(addr),
        "assets": assets,
        "total_usd": total,
        "fmt_total": fmt_usd(total),
        "claim_token": CLAIM_TOKEN,
        "claim_amount": CLAIM_AMOUNT,
        "recipient": DEMO_RECIPIENT,
        "connected_at": int(time.time()),
    }


def fake_tx_hash() -> str:
    return "0x" + secrets.token_hex(32)


def fake_block() -> int:
    return 21_000_000 + int(time.time()) % 100_000
