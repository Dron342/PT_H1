import csv
import json
import urllib.parse
from pathlib import Path
from typing import Any

from hackerone_research.config import HACKERONE_BASE_URL
from hackerone_research.hackerone.leaderboards import LEADERBOARDS


EXCEL_HYPERLINK_FUNCTION = "".join(
    chr(code)
    for code in (
        0x0413,
        0x0418,
        0x041F,
        0x0415,
        0x0420,
        0x0421,
        0x0421,
        0x042B,
        0x041B,
        0x041A,
        0x0410,
    )
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def excel_hyperlink(url: str | None, label: str | None = None) -> str | None:
    if not url:
        return None
    safe_url = str(url).replace('"', '""')
    safe_label = str(label or url).replace('"', '""')
    return f'={EXCEL_HYPERLINK_FUNCTION}("{safe_url}";"{safe_label}")'


def ensure_url(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def absolute_url(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.startswith(("http://", "https://")):
        return value
    return urllib.parse.urljoin(HACKERONE_BASE_URL, value)


def social_url(kind: str, value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lstrip("@")
    if not value:
        return None
    if value.startswith(("http://", "https://")):
        return value

    prefixes = {
        "github": "https://github.com/",
        "twitter": "https://x.com/",
        "linkedin": "https://www.linkedin.com/in/",
        "bugcrowd": "https://bugcrowd.com/",
        "gitlab": "https://gitlab.com/",
    }
    prefix = prefixes.get(kind)
    if not prefix:
        return None
    return f"{prefix}{value}"


def social_cell(kind: str, value: str | None) -> str | None:
    url = ensure_url(value) if kind == "website" else social_url(kind, value)
    return excel_hyperlink(url, value) if url else value


def excel_number(value: Any) -> Any:
    if value is None or value == "":
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.10f}".rstrip("0").rstrip(".").replace(".", ",")
    return value


def excel_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: excel_number(value) for key, value in row.items()}


def write_csv(path: Path, researchers: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    leaderboard_flag_fields = [f"in_{spec.slug}" for spec in LEADERBOARDS]
    fieldnames = [
        "username",
        "name",
        "profile_url",
        "location",
        "reputation",
        "valid_vulnerability_count",
        "past_year_signal",
        "past_year_impact",
        "streak_length",
        "cleared",
        "verified",
        "best_observed_rank",
        "leaderboard_appearances",
        "leaderboard_periods_count",
        "leaderboard_categories_count",
        "owasp_categories_count",
        "asset_type_categories_count",
        "high_critical_entries_count",
        "top_3_entries_count",
        "top_10_entries_count",
        "top_30_entries_count",
        "average_rank",
        *leaderboard_flag_fields,
        "hacktivity_total_count_last_year",
        "hacktivity_sample_count",
        "hacktivity_program_count",
        "hacktivity_visible_awards_count",
        "hacktivity_visible_awards_sum",
        "standoff_priority_score",
        "website",
        "github",
        "twitter",
        "linkedin",
        "bugcrowd",
        "hack_the_box",
        "gitlab",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for researcher in researchers:
            categories = set(researcher.get("leaderboard_categories") or [])
            socials = researcher.get("socials") or {}
            scope_metrics = researcher.get("scope_metrics") or {}
            leaderboard_flags = {
                f"in_{spec.slug}": "yes" if spec.slug in categories else ""
                for spec in LEADERBOARDS
            }
            row = {
                **{name: researcher.get(name) for name in fieldnames},
                **leaderboard_flags,
                "profile_url": excel_hyperlink(
                    researcher.get("profile_url"),
                    researcher.get("username"),
                ),
                "leaderboard_periods_count": len(researcher.get("leaderboard_periods") or []),
                "leaderboard_categories_count": scope_metrics.get("leaderboard_categories_count"),
                "owasp_categories_count": scope_metrics.get("owasp_categories_count"),
                "asset_type_categories_count": scope_metrics.get("asset_type_categories_count"),
                "high_critical_entries_count": scope_metrics.get("high_critical_entries_count"),
                "top_3_entries_count": scope_metrics.get("top_3_entries_count"),
                "top_10_entries_count": scope_metrics.get("top_10_entries_count"),
                "top_30_entries_count": scope_metrics.get("top_30_entries_count"),
                "average_rank": scope_metrics.get("average_rank"),
                "hacktivity_visible_awards_count": scope_metrics.get("hacktivity_visible_awards_count"),
                "hacktivity_visible_awards_sum": scope_metrics.get("hacktivity_visible_awards_sum"),
                "website": social_cell("website", socials.get("website")),
                "github": social_cell("github", socials.get("github")),
                "twitter": social_cell("twitter", socials.get("twitter")),
                "linkedin": social_cell("linkedin", socials.get("linkedin")),
                "bugcrowd": social_cell("bugcrowd", socials.get("bugcrowd")),
                "hack_the_box": socials.get("hack_the_box"),
                "gitlab": social_cell("gitlab", socials.get("gitlab")),
            }
            writer.writerow(excel_row(row))


def write_leaderboard_entries_csv(path: Path, researchers: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "username",
        "year",
        "quarter",
        "period",
        "leaderboard",
        "leaderboard_title",
        "leaderboard_key",
        "filter",
        "filter_label",
        "rank",
        "previous_rank",
        "reputation",
        "signal",
        "impact",
        "votes",
        "profile_url",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for researcher in researchers:
            for entry in researcher.get("leaderboard_entries") or []:
                row = {name: entry.get(name) for name in fieldnames}
                row["profile_url"] = excel_hyperlink(entry.get("profile_url"), entry.get("username"))
                writer.writerow(excel_row(row))


def write_hacktivity_csv(path: Path, researchers: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "username",
        "hacktivity_id",
        "report_id",
        "report_title",
        "report_url",
        "report_substate",
        "team_handle",
        "team_name",
        "team_url",
        "severity_rating",
        "cwe",
        "cve_ids",
        "votes",
        "total_awarded_amount",
        "currency",
        "submitted_at",
        "latest_disclosable_activity_at",
        "latest_disclosable_action",
        "disclosed_at",
        "public",
        "disclosed",
        "has_collaboration",
        "collaborators",
        "hacktivity_summary",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for researcher in researchers:
            for item in researcher.get("hacktivity_items") or []:
                row = {name: item.get(name) for name in fieldnames}
                row["report_url"] = excel_hyperlink(
                    absolute_url(item.get("report_url")),
                    item.get("report_title"),
                )
                row["team_url"] = excel_hyperlink(
                    absolute_url(item.get("team_url")),
                    item.get("team_handle"),
                )
                row["cve_ids"] = " | ".join(item.get("cve_ids") or [])
                row["collaborators"] = " | ".join(item.get("collaborators") or [])
                writer.writerow(excel_row(row))
