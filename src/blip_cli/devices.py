"""Parse Blip's local ``state.dat`` to recover the signed-in account and its
paired devices.

``state.dat`` is a Square Wire protobuf written by the Blip desktop app. We do
not have the ``.proto`` schema, but the layout is stable enough to extract what
we need with a couple of targeted byte patterns:

* the account ``user_id`` is the first length-36 string field in the account
  block (``0a 24 <uuid>``);
* each paired device is a field-7 sub-message shaped like
  ``0a 24 <device_id> 12 <len> 0a 24 <uuid> 10 <type> 1a <len> <name>``.

A Blip "peer id" (what ``Blip --peer`` expects) is ``<user_id>:<device_id>``.
All of a single account's own devices share that account's ``user_id``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_UUID = rb"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

_USER_ID_RE = re.compile(rb"\x0a\x24(" + _UUID + rb")")
_DEVICE_RE = re.compile(
    rb"\x0a\x24(" + _UUID + rb")"   # device_id
    rb"\x12.\x0a\x24" + _UUID +     # nested repeated id
    rb"\x10.\x1a(.)",               # type byte, then a name-length byte
    re.S,
)


@dataclass(frozen=True)
class Device:
    id: str
    name: str
    user_id: str

    @property
    def peer(self) -> str:
        return f"{self.user_id}:{self.id}"


@dataclass(frozen=True)
class Account:
    user_id: str
    devices: list[Device]


def parse_state(data: bytes) -> Account:
    """Parse raw ``state.dat`` bytes into an :class:`Account`."""
    m = _USER_ID_RE.search(data)
    if not m:
        raise ValueError("could not locate account user_id in state.dat")
    user_id = m.group(1).decode()

    devices: list[Device] = []
    seen: set[str] = set()
    for mm in _DEVICE_RE.finditer(data):
        dev_id = mm.group(1).decode()
        if dev_id in seen:
            continue
        name_len = mm.group(2)[0]
        name_start = mm.end()
        name = data[name_start : name_start + name_len].decode("utf-8", "replace")
        seen.add(dev_id)
        devices.append(Device(id=dev_id, name=name, user_id=user_id))

    return Account(user_id=user_id, devices=devices)


def load_account(state_path) -> Account:
    with open(state_path, "rb") as fh:
        return parse_state(fh.read())
