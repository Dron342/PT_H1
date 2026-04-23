import math
from typing import Any

from hackerone_research.hackerone.profiles import compact_socials


def build_scope_metrics(
    profile: dict[str, Any],
    entries: list[dict[str, Any]],
    hacktivity: dict[str, Any],
) -> dict[str, Any]:
    reputation = number(profile.get("reputation"))
    counts = profile.get("resolved_report_counts") or {}
    valid_count = number(counts.get("valid_vulnerability_count"))
    snapshot = profile.get("statistics_snapshot") or {}
    signal = number(snapshot.get("signal"))
    impact = number(snapshot.get("impact"))
    ranks = [entry["rank"] for entry in entries if entry.get("rank")]
    best_rank = min(ranks, default=None)
    hacktivity_items = hacktivity.get("items") or []
    hacktivity_programs = {
        item["team_handle"] or item["team_name"]
        for item in hacktivity_items
        if item.get("team_handle") or item.get("team_name")
    }
    visible_awards = [
        number(item.get("total_awarded_amount"))
        for item in hacktivity_items
        if item.get("total_awarded_amount") is not None
    ]
    high_signal_entries = [
        entry
        for entry in entries
        if entry.get("leaderboard_key") == "HIGH_CRIT_REPUTATION"
    ]
    owasp_categories = {
        entry.get("filter")
        for entry in entries
        if entry.get("leaderboard_key") == "OWASP_TOP_10" and entry.get("filter")
    }
    asset_type_categories = {
        entry.get("filter")
        for entry in entries
        if entry.get("leaderboard_key") == "ASSET_TYPES" and entry.get("filter")
    }

    return {
        "leaderboard_entries_count": len(entries),
        "leaderboard_periods_count": len(
            {entry.get("period") for entry in entries if entry.get("period")}
        ),
        "leaderboard_categories_count": len(
            {entry.get("leaderboard") for entry in entries if entry.get("leaderboard")}
        ),
        "owasp_categories_count": len(owasp_categories),
        "asset_type_categories_count": len(asset_type_categories),
        "high_critical_entries_count": len(high_signal_entries),
        "top_3_entries_count": sum(1 for rank in ranks if rank <= 3),
        "top_10_entries_count": sum(1 for rank in ranks if rank <= 10),
        "top_30_entries_count": sum(1 for rank in ranks if rank <= 30),
        "best_rank": best_rank,
        "average_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
        "profile_reputation": reputation,
        "valid_vulnerability_count": valid_count,
        "past_year_signal": signal,
        "past_year_impact": impact,
        "cleared": bool(profile.get("cleared")),
        "verified": bool(profile.get("verified")),
        "has_socials": bool(compact_socials(profile)),
        "hacktivity_total_count_last_year": hacktivity.get("total_count", 0),
        "hacktivity_sample_count": hacktivity.get("sample_count", 0),
        "hacktivity_program_count": len(hacktivity_programs),
        "hacktivity_visible_awards_count": len(visible_awards),
        "hacktivity_visible_awards_sum": round(sum(visible_awards), 2),
    }


def priority_score(scope_metrics: dict[str, Any]) -> float:
    reputation = number(scope_metrics.get("profile_reputation"))
    valid_count = number(scope_metrics.get("valid_vulnerability_count"))
    signal = number(scope_metrics.get("past_year_signal"))
    impact = number(scope_metrics.get("past_year_impact"))
    hacktivity_total_count = int(scope_metrics.get("hacktivity_total_count_last_year") or 0)

    score = 0.0
    score += min(math.log10(reputation + 1) * 8, 40)
    score += min(math.log10(valid_count + 1) * 7, 25)
    score += min(signal * 2, 15)
    score += min(impact, 15)
    score += min(number(scope_metrics.get("leaderboard_entries_count")) * 0.8, 18)
    score += min(number(scope_metrics.get("leaderboard_periods_count")) * 4, 8)
    score += min(number(scope_metrics.get("owasp_categories_count")) * 2, 12)
    score += min(number(scope_metrics.get("asset_type_categories_count")) * 2, 12)
    score += min(number(scope_metrics.get("high_critical_entries_count")) * 3, 12)
    score += min(number(scope_metrics.get("top_3_entries_count")) * 2, 10)
    score += min(math.log10(hacktivity_total_count + 1) * 3, 10)
    score += min(number(scope_metrics.get("hacktivity_program_count")) * 1.5, 10)
    if scope_metrics.get("cleared"):
        score += 2
    if scope_metrics.get("verified"):
        score += 2
    if scope_metrics.get("has_socials"):
        score += 2

    return round(score, 2)


def number(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
