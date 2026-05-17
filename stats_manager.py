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


def _hands_key(hands_enabled: dict[str, bool]) -> str:
    left = hands_enabled.get("left", False)
    right = hands_enabled.get("right", False)
    if left and right:
        return "both"
    elif left:
        return "left"
    else:
        return "right"


def record_transition(from_chord: str, to_chord: str, elapsed_seconds: float, errors: int, hands_enabled: dict[str, bool]) -> None:
    data = _load()
    key = f"{from_chord}{to_chord}"
    hand_key = _hands_key(hands_enabled)

    if key not in data:
        data[key] = {}

    entry = data[key]
    entry.setdefault("from_chord", from_chord)
    entry.setdefault("to_chord", to_chord)
    if hand_key not in entry:
        entry[hand_key] = {"time": round(elapsed_seconds, 3), "errors": float(errors), "count": 1}
    else:
        sub = entry[hand_key]
        count = sub["count"]
        sub["time"] = round((sub["time"] * count + elapsed_seconds) / (count + 1), 3)
        sub["errors"] = round((sub["errors"] * count + errors) / (count + 1), 3)
        sub["count"] = count + 1

    _save(data)


def get_all_stats(hand_key: str) -> list[dict]:
    data = _load()
    result = []
    for entry in data.values():
        if hand_key not in entry:
            continue
        from_chord = entry.get("from_chord")
        to_chord = entry.get("to_chord")
        if not from_chord or not to_chord:
            continue
        sub = entry[hand_key]
        result.append({
            "from_chord": from_chord,
            "to_chord": to_chord,
            "time": sub["time"],
            "errors": sub["errors"],
            "count": sub["count"],
        })
    return result
