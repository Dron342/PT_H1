import argparse
from pathlib import Path

from hackerone_research.collector import collect
from hackerone_research.config import (
    DEFAULT_CSV_OUTPUT,
    DEFAULT_DELAY_SECONDS,
    DEFAULT_HACKTIVITY_CSV_OUTPUT,
    DEFAULT_HACKTIVITY_LIMIT,
    DEFAULT_HACKTIVITY_PAGE_SIZE,
    DEFAULT_JSON_OUTPUT,
    DEFAULT_LEADERBOARD_CSV_OUTPUT,
    DEFAULT_LIMIT,
    DEFAULT_QUARTERS,
    DEFAULT_USER_TYPE,
    DEFAULT_YEAR,
)
from hackerone_research.output.exporters import (
    write_csv,
    write_hacktivity_csv,
    write_json,
    write_leaderboard_entries_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect a small HackerOne researcher sample for analysis."
    )
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument(
        "--quarters",
        default=",".join(str(quarter) for quarter in DEFAULT_QUARTERS),
        help="Comma-separated quarters to collect, for example: 1,2",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--user-type", default=DEFAULT_USER_TYPE)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_OUTPUT)
    parser.add_argument(
        "--leaderboard-csv-output",
        type=Path,
        default=DEFAULT_LEADERBOARD_CSV_OUTPUT,
    )
    parser.add_argument(
        "--hacktivity-csv-output",
        type=Path,
        default=DEFAULT_HACKTIVITY_CSV_OUTPUT,
    )
    parser.add_argument("--hacktivity-start-date", default=None)
    parser.add_argument("--hacktivity-end-date", default=None)
    parser.add_argument("--hacktivity-limit", type=int, default=DEFAULT_HACKTIVITY_LIMIT)
    parser.add_argument("--hacktivity-page-size", type=int, default=DEFAULT_HACKTIVITY_PAGE_SIZE)
    parser.add_argument("--skip-hacktivity", action="store_true")
    parser.add_argument(
        "--max-profiles",
        type=int,
        default=0,
        help="Optional cap for profile enrichment. 0 means all unique usernames from leaderboards.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = collect(args)
    write_json(args.json_output, payload)
    write_csv(args.csv_output, payload["researchers"])
    write_leaderboard_entries_csv(args.leaderboard_csv_output, payload["researchers"])
    write_hacktivity_csv(args.hacktivity_csv_output, payload["researchers"])
    print(f"JSON written to {args.json_output}")
    print(f"CSV written to {args.csv_output}")
    print(f"Leaderboard CSV written to {args.leaderboard_csv_output}")
    print(f"Hacktivity CSV written to {args.hacktivity_csv_output}")
    print(f"Researchers: {len(payload['researchers'])}")


if __name__ == "__main__":
    main()
