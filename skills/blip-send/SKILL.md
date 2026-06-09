---
name: blip-send
description: >-
  Send files to one of the user's own devices through the Blip file-transfer app.
  Use this whenever the user asks to "blip" a file or send/share a file via Blip,
  e.g. "blip this to my mac", "send report.pdf to my iphone with blip",
  "share this file to my ipad via blip". Resolves a friendly device name to a
  Blip peer id and dispatches the transfer through the genuine Blip app (no UI
  driving). v1 supports the user's OWN paired devices only, not other people.
---

# Blip a file to one of my devices

This skill sends file(s) to one of the user's own Blip-paired devices (Mac,
iPhone, iPad, PC, etc.) using a bundled cross-platform CLI. Blip must be
installed and signed in, and ideally already running.

## How to run it

Use the Python launcher bundled with this plugin. Use `python3` on macOS/Linux
and `python` on Windows (where `python3` may launch the Store). The examples
below use `python3`. All commands are run from any directory.

1. **Identify the file(s)** the user means (the file they referenced or attached).
   Resolve to concrete paths. If unclear, ask which file.

2. **Identify the recipient device** from the user's phrasing ("my mac" ->
   "MacBook Pro", "my phone" -> "iPhone", etc.). If you are unsure which device
   they mean, list the known devices first:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/blip_send.py" list
   ```

3. **Send**, passing the device name to `--to` (partial, case-insensitive names
   work, e.g. `--to mac`):

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/blip_send.py" send --to "MacBook Pro" "/path/to/file"
   ```

   Multiple files: list them all after `send`. A full peer id
   (`user_id:device_id`) may be passed to `--to` instead of a name.

4. **Confirm** to the user that the transfer was dispatched and that they may
   need to accept it on the receiving device.

## Important behavior

- **Own devices only (v1).** If the requested recipient is a *person* (e.g.
  "blip this to nick"), this is not supported yet — tell the user that
  person-to-person sending is not implemented and offer to send to one of their
  own devices instead.
- If `--to` matches no device, the CLI prints the known device names; relay them
  and ask the user to pick.
- If the CLI reports it cannot find `state.dat` or the Blip binary, run
  `python3 "${CLAUDE_PLUGIN_ROOT}/blip_send.py" doctor` and share the output —
  on macOS/Linux the install paths may differ and can be set via the `BLIP_STATE`
  and `BLIP_BIN` environment variables.
- Use `--dry-run` (after `send`) to show the exact Blip command without sending,
  if the user wants to inspect it first.
