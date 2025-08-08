from pathlib import Path
from typing import Any
from blake3 import blake3
import orjson


ART_DIR = Path(".mrp/artifacts")


def ensure_dirs() -> None:
    ART_DIR.mkdir(parents=True, exist_ok=True)


def digest_json(obj: Any) -> str:
    data = orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
    return blake3(data).hexdigest()


def put_json(obj: Any) -> str:
    ensure_dirs()
    d = digest_json(obj)
    p = ART_DIR / f"{d}.json"
    if not p.exists():
        p.write_bytes(orjson.dumps(obj, option=orjson.OPT_SORT_KEYS))
    return d


def get_json(digest: str) -> Any:
    p = ART_DIR / f"{digest}.json"
    return orjson.loads(p.read_bytes())


