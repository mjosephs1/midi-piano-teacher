import json
import os

SETTINGS_FILE = "chord_settings.json"


def load_chord_settings(group_names: list[str]) -> dict:
    """Returns saved settings, falling back to all-enabled defaults on any error."""
    defaults = {"group_enabled": {name: True for name in group_names}, "sharps_enabled": True}
    if not os.path.exists(SETTINGS_FILE):
        return defaults
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
        group_enabled = {name: data.get("group_enabled", {}).get(name, True) for name in group_names}
        sharps_enabled = bool(data.get("sharps_enabled", True))
        return {"group_enabled": group_enabled, "sharps_enabled": sharps_enabled}
    except Exception:
        return defaults


def save_chord_settings(group_enabled: dict, sharps_enabled: bool) -> None:
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"group_enabled": group_enabled, "sharps_enabled": sharps_enabled}, f, indent=2)
