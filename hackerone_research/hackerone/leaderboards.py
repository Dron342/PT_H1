import urllib.parse
from dataclasses import dataclass
from typing import Any

from hackerone_research.config import HACKERONE_BASE_URL
from hackerone_research.hackerone.client import HackerOneClient
from hackerone_research.hackerone.queries import LEADERBOARD_QUERY


@dataclass(frozen=True)
class LeaderboardSpec:
    slug: str
    title: str
    key: str
    type_name: str
    metric_fields: tuple[str, ...]
    filter_value: str | None = None
    filter_label: str | None = None


OWASP_CATEGORIES = (
    ("a1", "Injection"),
    ("a2", "Broken Authentication"),
    ("a3", "Sensitive Data Exposure"),
    ("a4", "XXE"),
    ("a5", "Broken Access Control"),
    ("a6", "Security Misconfiguration"),
    ("a7", "XSS"),
    ("a8", "Insecure Deserialization"),
)

ASSET_TYPE_CATEGORIES = (
    ("WEB_APP", "Web Application"),
    ("MOBILE_ANDROID", "Android Mobile App"),
    ("MOBILE_IOS", "iOS Mobile App"),
    ("INFRASTRUCTURE", "Infrastructure"),
    ("SOURCE_CODE", "Source Code"),
    ("AI_MODEL", "AI Model"),
)

BASE_LEADERBOARDS = (
    LeaderboardSpec(
        slug="highest_reputation",
        title="Highest Reputation",
        key="HIGHEST_REPUTATION",
        type_name="HighestReputationLeaderboardEntry",
        metric_fields=("reputation", "signal", "impact"),
    ),
    LeaderboardSpec(
        slug="high_critical",
        title="Highest Critical Reputation",
        key="HIGH_CRIT_REPUTATION",
        type_name="HighCritReputationLeaderboardEntry",
        metric_fields=("reputation", "signal", "impact"),
    ),
    LeaderboardSpec(
        slug="most_upvoted",
        title="Most Upvoted Hacktivity",
        key="HACKTIVITY_UPVOTES",
        type_name="HacktivityUpvotesLeaderboardEntry",
        metric_fields=("votes",),
    ),
    LeaderboardSpec(
        slug="up_and_comers",
        title="Up and Comers",
        key="UP_AND_COMERS",
        type_name="UpAndComersLeaderboardEntry",
        metric_fields=("reputation",),
    ),
)

OWASP_LEADERBOARDS = tuple(
    LeaderboardSpec(
        slug=f"owasp_{code}",
        title=f"OWASP {label}",
        key="OWASP_TOP_10",
        type_name="OwaspTopTenLeaderboardEntry",
        metric_fields=("reputation", "signal", "impact"),
        filter_value=code,
        filter_label=f"OWASP {code.upper()} {label}",
    )
    for code, label in OWASP_CATEGORIES
)

ASSET_TYPE_LEADERBOARDS = tuple(
    LeaderboardSpec(
        slug=f"asset_{asset_type.lower()}",
        title=f"Asset Type: {label}",
        key="ASSET_TYPES",
        type_name="AssetTypesLeaderboardEntry",
        metric_fields=("reputation", "signal", "impact"),
        filter_value=asset_type,
        filter_label=asset_type,
    )
    for asset_type, label in ASSET_TYPE_CATEGORIES
)

LEADERBOARDS = BASE_LEADERBOARDS + OWASP_LEADERBOARDS + ASSET_TYPE_LEADERBOARDS


def leaderboard_url(
    spec: LeaderboardSpec,
    year: int,
    quarter: int,
    user_type: str,
) -> str:
    if spec.key == "OWASP_TOP_10":
        detail = "owasp"
    elif spec.key == "ASSET_TYPES":
        detail = "asset_type"
    else:
        detail = {
            "highest_reputation": "reputation",
            "high_critical": "high_critical",
            "most_upvoted": "most_upvoted",
            "up_and_comers": "up_and_comers",
        }[spec.slug]
    query = {
        "year": year,
        "quarter": quarter,
        "tab": "bbp",
        "userTypeTab": user_type,
    }
    if spec.filter_value:
        if spec.key == "OWASP_TOP_10":
            query["owasp"] = spec.filter_value
        elif spec.key == "ASSET_TYPES":
            query["assetType"] = spec.filter_value

    return f"{HACKERONE_BASE_URL}/leaderboard/{detail}?{urllib.parse.urlencode(query)}"


def fetch_leaderboard(
    client: HackerOneClient,
    spec: LeaderboardSpec,
    year: int,
    quarter: int,
    limit: int,
    user_type: str,
) -> list[dict[str, Any]]:
    query = LEADERBOARD_QUERY.replace("__TYPE_NAME__", spec.type_name).replace(
        "__METRIC_FIELDS__", "\n          ".join(spec.metric_fields)
    )
    data = client.graphql(
        operation_name="LeaderboardSample",
        query=query,
        variables={
            "year": year,
            "quarter": quarter,
            "first": limit,
            "key": spec.key,
            "filter": spec.filter_value,
            "user_type": user_type,
        },
        product_area="leaderboard",
        product_feature=spec.slug,
    )
    edges = data["leaderboard_entries"]["edges"]
    rows: list[dict[str, Any]] = []
    for edge in edges:
        node = edge.get("node") or {}
        if not node:
            continue
        user = node.get("user") or {}
        row = {
            "year": year,
            "quarter": quarter,
            "period": f"{year}Q{quarter}",
            "leaderboard": spec.slug,
            "leaderboard_title": spec.title,
            "leaderboard_key": spec.key,
            "filter": spec.filter_value,
            "filter_label": spec.filter_label,
            "rank": node.get("rank"),
            "previous_rank": node.get("previous_rank"),
            "user_id": user.get("id"),
            "username": user.get("username"),
            "profile_url": f"{HACKERONE_BASE_URL}/{user.get('username')}?type=user"
            if user.get("username")
            else None,
            "mark_as_company_on_leaderboards": user.get("mark_as_company_on_leaderboards"),
        }
        for field in spec.metric_fields:
            row[field] = node.get(field)
        rows.append(row)
    return rows
