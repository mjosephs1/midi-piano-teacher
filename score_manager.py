import json
import os
from datetime import datetime

SCORES_FILE = "score_history.json"


def settings_key(group_enabled: dict, sharps_mode: str, hands_enabled: dict) -> str:
    enabled = sorted(k for k, v in group_enabled.items() if v)
    if hands_enabled.get("left") and hands_enabled.get("right"):
        hands_mode = "both"
    elif hands_enabled.get("left"):
        hands_mode = "left"
    else:
        hands_mode = "right"
    return ",".join(enabled) + f"|sharps={sharps_mode}|hands={hands_mode}"


def _load() -> dict:
    if not os.path.exists(SCORES_FILE):
        return {}
    try:
        with open(SCORES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_top_scores(group_enabled: dict, sharps_mode: str, hands_enabled: dict) -> list[dict]:
    return _load().get(settings_key(group_enabled, sharps_mode, hands_enabled), [])[:10]


def get_best_score(group_enabled: dict, sharps_mode: str, hands_enabled: dict) -> int | None:
    scores = get_top_scores(group_enabled, sharps_mode, hands_enabled)
    return scores[0]["score"] if scores else None


def record_score(group_enabled: dict, sharps_mode: str, score: int, errors: int = 0, hands_enabled: dict = None) -> None:
    if hands_enabled is None:
        hands_enabled = {"left": False, "right": True}
    data = _load()
    key = settings_key(group_enabled, sharps_mode, hands_enabled)
    entries = data.get(key, [])
    entries.append({"score": score, "errors": errors, "datetime": datetime.now().isoformat(timespec="seconds")})
    entries.sort(key=lambda e: (e["score"], -e.get("errors", 0)), reverse=True)
    data[key] = entries
    _save(data)
