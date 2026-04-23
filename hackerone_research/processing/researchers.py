from typing import Any

from hackerone_research.config import HACKERONE_BASE_URL
from hackerone_research.hackerone.profiles import compact_socials
from hackerone_research.processing.scoring import build_scope_metrics, priority_score


def build_researcher_records(
    profiles: dict[str, dict[str, Any]],
    leaderboard_rows: list[dict[str, Any]],
    hacktivity_by_user: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    hacktivity_by_user = hacktivity_by_user or {}
    rows_by_user: dict[str, list[dict[str, Any]]] = {}
    for row in leaderboard_rows:
        username = row.get("username")
        if username:
            rows_by_user.setdefault(username, []).append(row)

    researchers = []
    for username, entries in sorted(rows_by_user.items()):
        profile = profiles.get(username, {})
        counts = profile.get("resolved_report_counts") or {}
        snapshot = profile.get("statistics_snapshot") or {}
        streak = profile.get("user_streak") or {}
        hacktivity = hacktivity_by_user.get(username) or {}
        hacktivity_items = hacktivity.get("items") or []
        best_rank = min((entry["rank"] for entry in entries if entry.get("rank")), default=None)
        categories = sorted({entry["leaderboard"] for entry in entries})
        periods = sorted({entry["period"] for entry in entries if entry.get("period")})
        hacktivity_programs = sorted(
            {
                item["team_handle"] or item["team_name"]
                for item in hacktivity_items
                if item.get("team_handle") or item.get("team_name")
            }
        )
        scope_metrics = build_scope_metrics(profile, entries, hacktivity)
        researchers.append(
            {
                "username": username,
                "name": profile.get("name"),
                "profile_url": f"{HACKERONE_BASE_URL}/{username}?type=user",
                "created_at": profile.get("created_at"),
                "location": profile.get("location"),
                "intro": profile.get("intro"),
                "bio": profile.get("bio"),
                "reputation": profile.get("reputation"),
                "cleared": profile.get("cleared"),
                "verified": profile.get("verified"),
                "open_for_employment": profile.get("open_for_employment"),
                "profile_activated": profile.get("profile_activated"),
                "socials": compact_socials(profile),
                "valid_vulnerability_count": counts.get("valid_vulnerability_count"),
                "severity_low_count": counts.get("severity_low_count"),
                "severity_medium_count": counts.get("severity_medium_count"),
                "severity_high_count": counts.get("severity_high_count"),
                "severity_critical_count": counts.get("severity_critical_count"),
                "past_year_signal": snapshot.get("signal"),
                "past_year_impact": snapshot.get("impact"),
                "streak_length": streak.get("length"),
                "streak_start_date": streak.get("start_date"),
                "streak_end_date": streak.get("end_date"),
                "best_observed_rank": best_rank,
                "leaderboard_appearances": len(entries),
                "leaderboard_categories": categories,
                "leaderboard_periods": periods,
                "hacktivity_total_count_last_year": hacktivity.get("total_count", 0),
                "hacktivity_sample_count": hacktivity.get("sample_count", 0),
                "hacktivity_program_count": len(hacktivity_programs),
                "hacktivity_programs": hacktivity_programs,
                "hacktivity_items": hacktivity_items,
                "scope_metrics": scope_metrics,
                "standoff_priority_score": priority_score(scope_metrics),
                "leaderboard_entries": sorted(
                    entries,
                    key=lambda item: (
                        item.get("year") or 0,
                        item.get("quarter") or 0,
                        item["leaderboard"],
                        item["rank"] or 9999,
                    ),
                ),
            }
        )

    return sorted(
        researchers,
        key=lambda item: (
            -(item.get("standoff_priority_score") or 0),
            item.get("best_observed_rank") or 9999,
            item["username"],
        ),
    )
