"""Verify imported upstream bytes using the pinned Git blob SHA inventory."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
    errors = []
    checked = 0
    seen = set()
    for source in lock["sources"]:
        for item in source["files"]:
            relative = item["destination"]
            path = (ROOT / relative).resolve()
            try:
                path.relative_to(ROOT)
            except ValueError:
                errors.append(f"Path outside repository: {relative}")
                continue
            if relative in seen:
                errors.append(f"Duplicate inventory path: {relative}")
                continue
            seen.add(relative)
            if not path.is_file():
                errors.append(f"Missing: {relative}")
                continue
            data = path.read_bytes()
            actual = hashlib.sha1(
                b"blob " + str(len(data)).encode("ascii") + b"\0" + data
            ).hexdigest()
            if actual != item["git_blob_sha"]:
                errors.append(f"Changed: {relative}")
            checked += 1
    for skill in lock["skills"]:
        if not (ROOT / skill["path"]).is_file():
            errors.append(f"Missing skill entry: {skill['path']}")
    expected = sum(len(s["files"]) for s in lock["sources"])
    if errors:
        print("\n".join(errors))
        return 1
    print(
        f"Verified {checked}/{expected} upstream files, "
        f"{sum(not s['template'] for s in lock['skills'])} skills and "
        f"{sum(s['template'] for s in lock['skills'])} template(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
