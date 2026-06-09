"""Command-line interface for sending files through the genuine Blip app.

Subcommands:
  list     show the signed-in account and its paired devices (+ peer ids)
  send     send file(s) to a device by name (or by full user_id:device_id)
  doctor   print diagnostics (detected OS, state.dat path, Blip launcher)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import platforms
from .devices import Account, Device, load_account


def _load() -> Account:
    return load_account(platforms.find_state_dat())


def _resolve_device(account: Account, target: str) -> Device:
    # Allow passing a full peer id (user_id:device_id) straight through.
    if ":" in target and target.count(":") == 1:
        uid, did = target.split(":")
        return Device(id=did, name=target, user_id=uid)

    exact = [d for d in account.devices if d.name.lower() == target.lower()]
    matches = exact or [d for d in account.devices if target.lower() in d.name.lower()]
    if not matches:
        names = ", ".join(d.name for d in account.devices) or "(none)"
        raise SystemExit(f"No device matching '{target}'. Known devices: {names}")
    if len(matches) > 1:
        names = ", ".join(d.name for d in matches)
        raise SystemExit(f"'{target}' is ambiguous between: {names}")
    return matches[0]


def cmd_list(args: argparse.Namespace) -> int:
    account = _load()
    if args.json:
        print(json.dumps({
            "user_id": account.user_id,
            "devices": [{"id": d.id, "name": d.name, "peer": d.peer} for d in account.devices],
        }, indent=2))
    else:
        print(f"account user_id: {account.user_id}")
        for d in account.devices:
            print(f"  {d.name:<16} {d.peer}")
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    account = _load()
    device = _resolve_device(account, args.to)

    files = []
    for f in args.files:
        p = Path(f).expanduser()
        if not p.exists():
            raise SystemExit(f"File not found: {f}")
        files.append(str(p.resolve()))

    argv = platforms.build_send_argv(device.peer, files)

    if args.dry_run:
        print(" ".join(argv))
        return 0

    print(f"Sending to {device.name} ({device.peer}):")
    for f in files:
        print(f"  {f}")
    proc = subprocess.run(argv)
    if proc.returncode != 0:
        print(f"Blip launcher exited with code {proc.returncode}", file=sys.stderr)
        return proc.returncode
    print("Dispatched to Blip. Check the Blip window / recipient device.")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"platform: {sys.platform}")
    print("state.dat candidates:")
    for c in platforms.state_dat_candidates():
        print(f"  [{'x' if c.is_file() else ' '}] {c}")
    try:
        sp = platforms.find_state_dat()
        print(f"using state.dat: {sp}")
        account = load_account(sp)
        print(f"account user_id: {account.user_id}")
        print(f"devices: {', '.join(d.name for d in account.devices) or '(none)'}")
    except Exception as e:  # noqa: BLE001 - diagnostics
        print(f"state.dat: ERROR: {e}")
    print(f"launcher: {' '.join(platforms.launcher_prefix())}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="blip-send", description="Send files via the Blip app.")
    sub = p.add_subparsers(dest="command", required=True)

    pl = sub.add_parser("list", help="list account + paired devices")
    pl.add_argument("--json", action="store_true", help="output JSON")
    pl.set_defaults(func=cmd_list)

    ps = sub.add_parser("send", help="send file(s) to a device")
    ps.add_argument("--to", required=True, help="device name (e.g. 'MacBook Pro') or user_id:device_id")
    ps.add_argument("files", nargs="+", help="one or more file paths")
    ps.add_argument("--dry-run", action="store_true", help="print the Blip command instead of running it")
    ps.set_defaults(func=cmd_send)

    pd = sub.add_parser("doctor", help="print diagnostics")
    pd.set_defaults(func=cmd_doctor)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
