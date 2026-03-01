import json
import os
from pathlib import Path

# Always relative to this file's location — works regardless of cwd
SETTINGS_PATH = Path(__file__).parent.parent / 'assets' / 'settings.json'

DEFAULTS = {
    'base_speed': 10,
    'acceleration_enabled': True,
    'passthrough_mode': False,
}


def load() -> dict:
    """Load settings from file, falling back to defaults for missing keys."""
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH) as f:
                data = json.load(f)
            # Merge with defaults so new keys are always present
            return {**DEFAULTS, **data}
    except Exception as e:
        print(f"[SETTINGS] Could not load settings: {e}")
    return dict(DEFAULTS)


def save(settings: dict):
    """Save settings to file. Only saves known keys."""
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {k: settings[k] for k in DEFAULTS if k in settings}
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[SETTINGS] Could not save settings: {e}")