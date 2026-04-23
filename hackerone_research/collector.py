import time
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from typing import Any

from hackerone_research.config import DEFAULT_QUARTERS
from hackerone_research.hackerone.client import HackerOneClient
from hackerone_research.hackerone.hacktivity import fetch_hacktivity
from hackerone_research.hackerone.leaderboards import LEADERBOARDS, fetch_leaderboard, leaderboard_url
from hackerone_research.hackerone.profiles import fetch_profile
from hackerone_research.processing.researchers import build_researcher_records


def parse_quarters(value: str) -> list[int]:
    quarters = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        quarter = int(part)
        if quarter not in {1, 2, 3, 4}:
            raise ValueError(f"Quarter must be between 1 and 4: {quarter}")
        quarters.append(quarter)
    return quarters or list(DEFAULT_QUARTERS)


def default_hacktivity_dates() -> tuple[str, str]:
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=365)
    return start_date.isoformat(), end_date.isoformat()


def collect(args: Namespace) -> dict[str, Any]:
    client = HackerOneClient()
    leaderboards: dict[str, list[dict[str, Any]]] = {}
    all_rows: list[dict[str, Any]] = []
    quarters = parse_quarters(args.quarters)

    total_leaderboard_jobs = len(quarters) * len(LEADERBOARDS)
    job_index = 0
    for quarter in quarters:
        for spec in LEADERBOARDS:
            job_index += 1
            rows = fetch_leaderboard(
                client=client,
                spec=spec,
                year=args.year,
                quarter=quarter,
                limit=args.limit,
                user_type=args.user_type,
            )
            leaderboard_key = f"{args.year}_q{quarter}_{spec.slug}"
            leaderboards[leaderboard_key] = rows
            all_rows.extend(rows)
            print(
                f"[{job_index}/{total_leaderboard_jobs}] "
                f"{args.year} Q{quarter} {spec.title}: {len(rows)} rows"
            )
            time.sleep(args.delay)

    usernames = sorted({row["username"] for row in all_rows if row.get("username")})
    if args.max_profiles:
        usernames = usernames[: args.max_profiles]

    profiles: dict[str, dict[str, Any]] = {}
    profile_errors: dict[str, str] = {}
    for index, username in enumerate(usernames, start=1):
        try:
            profiles[username] = fetch_profile(client, username)
            print(f"[profile {index}/{len(usernames)}] {username}")
        except Exception as error:
            profile_errors[username] = str(error)
            print(f"[profile {index}/{len(usernames)}] {username}: {error}")
        time.sleep(args.delay)

    hacktivity_start_date = args.hacktivity_start_date
    hacktivity_end_date = args.hacktivity_end_date
    if not hacktivity_start_date or not hacktivity_end_date:
        default_start, default_end = default_hacktivity_dates()
        hacktivity_start_date = hacktivity_start_date or default_start
        hacktivity_end_date = hacktivity_end_date or default_end

    hacktivity_by_user: dict[str, dict[str, Any]] = {}
    hacktivity_errors: dict[str, str] = {}
    if not args.skip_hacktivity:
        for index, username in enumerate(usernames, start=1):
            try:
                hacktivity_by_user[username] = fetch_hacktivity(
                    client=client,
                    username=username,
                    start_date=hacktivity_start_date,
                    end_date=hacktivity_end_date,
                    limit=args.hacktivity_limit,
                    page_size=args.hacktivity_page_size,
                )
                total_count = hacktivity_by_user[username].get("total_count", 0)
                sample_count = hacktivity_by_user[username].get("sample_count", 0)
                print(
                    f"[hacktivity {index}/{len(usernames)}] "
                    f"{username}: {sample_count}/{total_count}"
                )
            except Exception as error:
                hacktivity_errors[username] = str(error)
                print(f"[hacktivity {index}/{len(usernames)}] {username}: {error}")
            time.sleep(args.delay)

    researchers = build_researcher_records(profiles, all_rows, hacktivity_by_user)
    collected_at = datetime.now(timezone.utc).isoformat()
    return {
        "metadata": {
            "collected_at": collected_at,
            "source": "HackerOne public web GraphQL used by hackerone.com",
            "year": args.year,
            "quarters": quarters,
            "limit_per_leaderboard": args.limit,
            "user_type": args.user_type,
            "hacktivity_start_date": hacktivity_start_date,
            "hacktivity_end_date": hacktivity_end_date,
            "hacktivity_limit_per_user": args.hacktivity_limit,
            "leaderboard_urls": {
                f"{args.year}_q{quarter}_{spec.slug}": leaderboard_url(
                    spec,
                    args.year,
                    quarter,
                    args.user_type,
                )
                for quarter in quarters
                for spec in LEADERBOARDS
            },
            "notes": [
                "The official HackerOne REST API requires an API token for many program/report resources.",
                "This sample intentionally uses a small public dataset and keeps delays between requests.",
                "Derived scores are ranking aids for analysis, not HackerOne-provided metrics.",
            ],
            "profile_errors": profile_errors,
            "hacktivity_errors": hacktivity_errors,
        },
        "leaderboards": leaderboards,
        "hacktivity": hacktivity_by_user,
        "researchers": researchers,
    }
