# keycursor

Control your mouse with your keyboard. Built for Linux (Wayland + X11) using `evdev` and `ydotool`.

## Requirements

- Python 3
- `ydotoold` running (`sudo systemctl start ydotool`)
- User in `input` group or run with `sudo`

## Setup

```bash
bash setup_venv.sh
```

## Run

```bash
GDK_BACKEND=x11 venv/bin/python3 python/main.py
```

## Controls

| Key | Action |
|-----|--------|
| CapsLock | Toggle mouse mode |
| WASD | Move cursor |
| Enter | Left click (hold to drag) |
| Backspace | Right click |
| `\` | Middle click |
| PageUp / PageDown | Scroll up / down (hold for continuous) |
| Q | Toggle precision mode (speed 2) |
| TAB | Toggle acceleration |
| 1–9, 0 | Set speed (2–50) |

### Auto-exit mouse mode
- Any non-mouse key exits mouse mode
- All modifier combos exit (Ctrl+C, Alt+Tab, etc.)
- **Exception:** Ctrl / Shift / Alt + Click or RightClick

## Known Issues / TODO

- [ ] Bluetooth keyboard wake-up: first keypress after sleep is dropped
- [ ] CapsLock state can desync if script crashes mid-session
- [ ] CapsLock LED blinking as mode indicator
- [ ] Holding a key before entering mouse mode causes key spam

## License

MIT