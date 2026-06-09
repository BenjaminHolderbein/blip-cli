"""Parser tests using a synthetic state.dat blob.

The fixture is built from the documented byte patterns with fake UUIDs and
names, so no real account data is committed.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from blip_cli.devices import parse_state  # noqa: E402

USER_ID = "11111111-1111-4111-8111-111111111111"
DEV_A = "22222222-2222-4222-8222-222222222222"
DEV_B = "33333333-3333-4333-8333-333333333333"


def _field1_uuid(uuid: str) -> bytes:
    b = uuid.encode()
    assert len(b) == 36
    return b"\x0a\x24" + b


def _account_block(user_id: str) -> bytes:
    # user_id, then a non-device-shaped continuation (email-like, 0a 15 ...)
    email = b"a@example.com"
    inner = b"\x0a" + bytes([len(email)]) + email
    return _field1_uuid(user_id) + b"\x12" + bytes([len(inner)]) + inner


def _device_block(dev_id: str, name: str) -> bytes:
    name_b = name.encode()
    nested = (
        _field1_uuid(dev_id)
        + b"\x10\x04"                       # type byte
        + b"\x1a" + bytes([len(name_b)]) + name_b
    )
    return (
        _field1_uuid(dev_id)
        + b"\x12" + bytes([len(nested)]) + nested
    )


def build_fixture() -> bytes:
    return b"".join([
        b"\x08\x02\x18\x01",  # arbitrary leading fields
        _account_block(USER_ID),
        _device_block(DEV_A, "MacBook Pro"),
        _device_block(DEV_B, "iPhone"),
    ])


def test_parse_account_and_devices():
    acct = parse_state(build_fixture())
    assert acct.user_id == USER_ID
    names = {d.name: d for d in acct.devices}
    assert set(names) == {"MacBook Pro", "iPhone"}
    assert names["MacBook Pro"].id == DEV_A
    assert names["MacBook Pro"].peer == f"{USER_ID}:{DEV_A}"
    assert names["iPhone"].peer == f"{USER_ID}:{DEV_B}"


def test_account_block_not_parsed_as_device():
    acct = parse_state(build_fixture())
    assert all(d.id != USER_ID for d in acct.devices)


if __name__ == "__main__":
    test_parse_account_and_devices()
    test_account_block_not_parsed_as_device()
    print("ok")
