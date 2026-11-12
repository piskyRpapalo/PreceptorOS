"""Notebook reports producer · benchmark receipts on disk -> weekly and monthly review files.

The Notebook reader shows a weekly review (WBR) and a monthly review (MBR) from
two small files in `<home>/notebook/`. Nothing produced them. This module makes
them from the one thing that is already measured and dated: the receipt files of
the local benchmarks (`YYYYMMDD-name.json` or `.md` in a folder the caller names).

A review here is a list, not a judgement: how many receipts fall in the period,
which ones, and a fingerprint of exactly those files. No figure is copied out of
a receipt, so nothing can drift from its source. The reader labels the result
as declared, which is what it is: nobody has checked the receipts independently.

A period with no receipt writes no file: the reader then says NO_DATA with its
cause, which is true. No network, no subprocess, no scheduler.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

_NAME = re.compile(r"^(\d{4})(\d{2})(\d{2})-([a-z0-9][a-z0-9._-]{0,80})\.(json|md)$")
MAX_FILE = 4096           # the reader refuses a larger review
MAX_SUMMARY = 420
MAX_RECEIPT = 1 << 20     # a receipt larger than 1 MiB is not hashed; it is counted as skipped


def receipts(folder):
    """Dated receipt files in `folder` -> [(date, name, sha256)], oldest first. Symlinks are skipped."""
    out, skipped = [], 0
    try:
        entries = sorted(os.listdir(folder))
    except OSError:
        return [], "folder_unreadable"
    for name in entries:
        m = _NAME.fullmatch(name)
        path = Path(folder) / name
        if not m or path.is_symlink() or not path.is_file():
            continue
        try:
            day = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if path.stat().st_size > MAX_RECEIPT:
                skipped += 1
                continue
            out.append((day, name, hashlib.sha256(path.read_bytes()).hexdigest()))
        except (ValueError, OSError):
            skipped += 1
    return out, ("skipped_%d" % skipped if skipped else None)


def week_of(day):
    year, week, _ = day.isocalendar()
    return "%04d-W%02d" % (year, week)


def month_of(day):
    return "%04d-%02d" % (day.year, day.month)


def review(kind, period, found, now):
    """One review dict in the reader's schema, or None when the period has no receipt."""
    key = week_of if kind == "wbr" else month_of
    mine = [(d, n, h) for d, n, h in found if key(d) == period]
    if not mine:
        return None
    names = list(dict.fromkeys(n.rsplit(".", 1)[0][9:] for _, n, _ in mine))   # one name per benchmark, in order
    head = "%d receipt file%s for %d benchmark%s dated in %s: " % (
        len(mine), "" if len(mine) == 1 else "s", len(names), "" if len(names) == 1 else "s", period)
    tail = " Newest: %s. Figures stay in the receipts; none is copied here." % mine[-1][1]
    room = MAX_SUMMARY - len(head) - len(tail)
    listed = ", ".join(names)
    if len(listed) > room:
        listed = listed[:max(0, room - 2)].rsplit(",", 1)[0] + ", …"
    digest = hashlib.sha256("\n".join(n + " " + h for _, n, h in mine).encode("utf-8")).hexdigest()
    return {"schema": "preceptoros.%s/1" % kind, "period": period, "summary": (head + listed + "." + tail)[:MAX_SUMMARY],
            "measured_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "receipt_sha256": digest}


def write(root, kind, doc):
    """Atomically replace <root>/notebook/<kind>.json (mode 0600). Refuses symlinks and oversized files."""
    directory = Path(root) / "notebook"
    target = directory / (kind + ".json")
    if Path(root).is_symlink() or directory.is_symlink() or target.is_symlink():
        raise OSError("symlink_forbidden")
    payload = (json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    if len(payload) > MAX_FILE:
        raise ValueError("review_oversized")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    temp = directory / (".%s.%d.tmp" % (kind, os.getpid()))
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write the weekly and monthly review files from local benchmark receipts.")
    parser.add_argument("--receipts", required=True, help="folder holding YYYYMMDD-name.json|md receipt files")
    parser.add_argument("--root", default=None, help="personal folder (default: the product's own)")
    parser.add_argument("--dry-run", action="store_true", help="measure and print, write nothing")
    args = parser.parse_args(argv)
    now = dt.datetime.now(dt.timezone.utc)
    found, cause = receipts(args.receipts)
    root = args.root
    said = {"receipts": len(found), "cause": cause, "written": []}
    for kind, period in (("wbr", week_of(now.date())), ("mbr", month_of(now.date()))):
        doc = review(kind, period, found, now)
        said[kind] = {"period": period, "status": "DECLARED" if doc else "NO_DATA",
                      "cause": None if doc else "no_receipt_in_period"}
        if doc and not args.dry_run:
            if root is None:
                import casa
                root = casa.raiz()
            write(root, kind, doc)
            said["written"].append(kind + ".json")
    print(json.dumps(said, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
