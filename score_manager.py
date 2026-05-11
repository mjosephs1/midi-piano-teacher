import json
import os
from datetime import datetime

SCORES_FILE = "score_history.json"


def settings_key(group_enabled: dict, sharps_mode: str) -> str:
    enabled = sorted(k for k, v in group_enabled.items() if v)
    return ",".join(enabled) + f"|sharps={sharps_mode}"


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


def get_top_scores(group_enabled: dict, sharps_mode: str) -> list[dict]:
    return _load().get(settings_key(group_enabled, sharps_mode), [])[:10]


def get_best_score(group_enabled: dict, sharps_mode: str) -> int | None:
    scores = get_top_scores(group_enabled, sharps_mode)
    return scores[0]["score"] if scores else None


def record_score(group_enabled: dict, sharps_mode: str, score: int, errors: int = 0) -> None:
    data = _load()
    key = settings_key(group_enabled, sharps_mode)
    entries = data.get(key, [])
    entries.append({"score": score, "errors": errors, "datetime": datetime.now().isoformat(timespec="seconds")})
    entries.sort(key=lambda e: (e["score"], -e.get("errors", 0)), reverse=True)
    data[key] = entries
    _save(data)
