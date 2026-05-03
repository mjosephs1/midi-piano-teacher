import json
import os
from datetime import datetime

SCORES_FILE = "score_history.json"


def settings_key(group_enabled: dict, sharps_enabled: bool) -> str:
    enabled = sorted(k for k, v in group_enabled.items() if v)
    return ",".join(enabled) + f"|sharps={'true' if sharps_enabled else 'false'}"


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


def get_top_scores(group_enabled: dict, sharps_enabled: bool) -> list[dict]:
    return _load().get(settings_key(group_enabled, sharps_enabled), [])[:10]


def get_best_score(group_enabled: dict, sharps_enabled: bool) -> int | None:
    scores = get_top_scores(group_enabled, sharps_enabled)
    return scores[0]["score"] if scores else None


def record_score(group_enabled: dict, sharps_enabled: bool, score: int, errors: int = 0) -> None:
    data = _load()
    key = settings_key(group_enabled, sharps_enabled)
    entries = data.get(key, [])
    entries.append({"score": score, "errors": errors, "datetime": datetime.now().isoformat(timespec="seconds")})
    entries.sort(key=lambda e: (e["score"], -e.get("errors", 0)), reverse=True)
    data[key] = entries
    _save(data)
