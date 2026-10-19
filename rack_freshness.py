"""Pure freshness calculation for rack observations."""
import argparse
import datetime as dt
import json

TTL_DAYS = 7
TTL_SECONDS = TTL_DAYS * 86400
STAMPS = {"LIVE", "STALE", "STATIC", "SIMULATED", "NO_DATA", "ERROR"}


def parse_utc(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise argparse.ArgumentTypeError("timestamp must include UTC offset Z or +00:00")
    return parsed.astimezone(dt.timezone.utc)


def freshness(state, observed_at, now=None):
    if state not in STAMPS:
        raise ValueError("unknown stamp")
    if state != "LIVE":
        return state
    if observed_at is None:
        return "NO_DATA"
    current = now or dt.datetime.now(dt.timezone.utc)
    return "STALE" if (current - observed_at).total_seconds() >= TTL_SECONDS else "LIVE"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--observed-at", required=True, type=parse_utc)
    parser.add_argument("--now", type=parse_utc, default=None)
    args = parser.parse_args()
    args.now = args.now or dt.datetime.now(dt.timezone.utc)
    state = freshness("LIVE", args.observed_at, args.now)
    print(json.dumps({"state": state, "ttl_days": TTL_DAYS,
                      "observed_at": args.observed_at.isoformat().replace("+00:00", "Z"),
                      "evaluated_at": args.now.isoformat().replace("+00:00", "Z")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
