"""Platform-specific knowledge: where Blip stores ``state.dat`` and how to launch
the Blip binary so it creates a transfer.

The send mechanism is identical across desktop platforms because Blip uses the
same Compose/Conveyor launcher everywhere: invoking the binary with
``--peer <user_id>:<device_id> --file <path>`` forwards the request to the
already-running single instance, which creates the transfer.

Only two things differ per OS and are isolated here:

* :func:`state_dat_candidates` -- candidate paths to ``state.dat``;
* :func:`launcher_prefix` -- the argv prefix used to invoke Blip.

Windows is verified. macOS and Linux ship best-effort candidates; if Blip lives
somewhere else on your machine, add the path here (PRs welcome) or override with
the ``BLIP_STATE`` / ``BLIP_BIN`` environment variables.
"""

from __future__ import annotations

import glob
import os
import shutil
import sys
from pathlib import Path

# MSIX package family name for the Microsoft Store build of Blip.
_WIN_PKG = "BlipStudioInc.BlipApp_eydxbjyejh39j"
_APP_DIR = "net.blip.desktop"  # Blip's data-dir name on all platforms


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


def state_dat_candidates() -> list[Path]:
    """Return candidate ``state.dat`` locations for the current OS, most likely
    first. Callers should use the first one that exists."""
    env = os.environ.get("BLIP_STATE")
    if env:
        return [_expand(env)]

    if sys.platform.startswith("win"):
        local = os.environ.get("LOCALAPPDATA", "")
        return [
            Path(local) / "Packages" / _WIN_PKG / "LocalCache" / "Local" / _APP_DIR / "state.dat",
            Path(local) / _APP_DIR / "state.dat",  # non-packaged fallback
        ]

    if sys.platform == "darwin":
        home = Path.home()
        cands = [
            home / "Library" / "Application Support" / _APP_DIR / "state.dat",
        ]
        # Sandboxed (Mac App Store) builds live under a container.
        cands += [
            Path(p)
            for p in glob.glob(
                str(home / "Library" / "Containers" / "*" / "Data" / "Library"
                    / "Application Support" / _APP_DIR / "state.dat")
            )
        ]
        return cands

    # Linux / other unix
    xdg = os.environ.get("XDG_DATA_HOME")
    home = Path.home()
    cands = []
    if xdg:
        cands.append(Path(xdg) / _APP_DIR / "state.dat")
    cands += [
        home / ".local" / "share" / _APP_DIR / "state.dat",
        home / ".config" / _APP_DIR / "state.dat",
    ]
    return cands


def find_state_dat() -> Path:
    for c in state_dat_candidates():
        if c.is_file():
            return c
    searched = "\n  ".join(str(c) for c in state_dat_candidates())
    raise FileNotFoundError(
        "Could not find Blip's state.dat. Searched:\n  " + searched +
        "\nIs Blip installed and signed in? You can also set BLIP_STATE=<path>."
    )


def launcher_prefix() -> list[str]:
    """Return the argv prefix that launches Blip (without --peer/--file)."""
    env = os.environ.get("BLIP_BIN")
    if env:
        return [env]

    if sys.platform.startswith("win"):
        # App execution alias, resolved via PATH (WindowsApps), with a fallback.
        alias = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "blip.exe"
        if shutil.which("blip.exe"):
            return ["blip.exe"]
        if alias.is_file():
            return [str(alias)]
        return ["blip.exe"]  # let it fail loudly if truly missing

    if sys.platform == "darwin":
        for app in ("/Applications/Blip.app", str(Path.home() / "Applications" / "Blip.app")):
            binary = Path(app) / "Contents" / "MacOS" / "Blip"
            if binary.is_file():
                return [str(binary)]
        # Fallback: hand args to the registered app via `open`.
        return ["open", "-a", "Blip", "--args"]

    # Linux / other unix
    for name in ("blip", "Blip"):
        found = shutil.which(name)
        if found:
            return [found]
    for cand in ("/opt/Blip/bin/Blip", "/opt/blip/bin/blip", "/usr/lib/blip/bin/Blip"):
        if Path(cand).is_file():
            return [cand]
    return ["blip"]  # let it fail loudly if truly missing


def build_send_argv(peer: str, files: list[str]) -> list[str]:
    argv = launcher_prefix() + ["--peer", peer]
    for f in files:
        argv += ["--file", f]
    return argv
