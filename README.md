# keycursor

We have all been there, tired and of switching over to the mouse for just a small click. I feel that pain, that is why I made KeyCursor - for those who hate mouse!
Control your mouse with your keyboard. Built for Linux (Wayland + X11) using `evdev` and `ydotool`.

## Requirements

- Python 3.10+
- `ydotoold` running (`sudo systemctl start ydotool`)
- User in `input` group or run with `sudo`
- `gtk-layer-shell` installed (`pkg-config --exists gtk-layer-shell-0 && echo yes`)

## Setup

```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install evdev pygobject
```

> `--system-site-packages` is required so the venv can access `gi` (GTK bindings) which are system-level packages.

## Run

```bash
venv/bin/python3 python/main.py
```

## Controls

| Key | Action |
|-----|--------|
| `CapsLock` | Toggle mouse mode on/off |
| `Ctrl + CapsLock` | Toggle passthrough mode (script disabled) |
| `WASD` | Move cursor |
| `Enter` | Left click (hold to drag) |
| `Backspace` | Right click |
| `\` | Middle click |
| `PageUp / PageDown` | Scroll up / down (hold for continuous) |
| `Q` | Toggle precision mode (speed 2 with acceleration) |
| `TAB` | Toggle acceleration |
| `1–9, 0` | Set speed (2–50) |

## Modes & Indicator

A thin bar at the top of the screen shows the current mode:

| Color | Mode |
|-------|------|
| ⬜ White | Mouse mode ON, acceleration ON |
| 🔵 Blue | Mouse mode ON, acceleration OFF |
| 🟢 Green | Precision mode |
| 🔴 Red blink | Passthrough mode reminder (CapsLock pressed while disabled) |
| *(no bar)* | Mouse mode OFF / passthrough mode |

## Passthrough Mode

Press `Ctrl + CapsLock` to fully disable the script — all keys pass through untouched as if the script wasn't running. Press `Ctrl + CapsLock` again to re-enable.

While in passthrough mode, pressing `CapsLock` alone will blink the red bar 6 times as a reminder that the script is disabled. `CapsLock` itself is blocked (won't toggle caps).

## Settings

Settings are auto-saved to `assets/settings.json` and restored on next launch:
- `base_speed` — last used speed
- `acceleration_enabled` — acceleration on/off
- `passthrough_mode` — whether passthrough was active when the script exited

## Auto-exit Mouse Mode

- Any non-mouse key exits mouse mode automatically
- All modifier combos exit (Ctrl+C, Alt+Tab, etc.)
- **Exception:** Ctrl / Shift / Alt + Click or RightClick (modifier clicks are passed through)

## Device Management

The script automatically handles:
- Hot-plugging keyboards (USB connect/disconnect)
- Keyboard wake from sleep
- Multiple keyboards simultaneously

## Known Issues / TODO

- [ ] CapsLock LED blinking as mode indicator (kernel grab/ungrab limitations make this tricky)
- [ ] No installation / uninstallation script (coming soon)
- [ ] No startup script / service (coming soon)

#### Feedback? Issue? Want a feature? Feel free to post it on git! 
> If you Liked this repo please consider giving it a star!

## License

MIT