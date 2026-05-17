import json
import os

STATS_FILE = "stats.json"


def _load() -> dict:
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_transition(from_chord: str, to_chord: str, elapsed_seconds: float, errors: int) -> None:
    data = _load()
    key = f"{from_chord}{to_chord}"
    if key in data:
        entry = data[key]
        count = entry["count"]
        entry["time"] = round((entry["time"] * count + elapsed_seconds) / (count + 1), 3)
        entry["errors"] = round((entry["errors"] * count + errors) / (count + 1), 3)
        entry["count"] = count + 1
    else:
        data[key] = {"time": round(elapsed_seconds, 3), "errors": float(errors), "count": 1}
    _save(data)
