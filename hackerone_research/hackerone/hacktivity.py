from typing import Any

from hackerone_research.hackerone.client import HackerOneClient
from hackerone_research.hackerone.queries import HACKTIVITY_QUERY


def fetch_hacktivity(
    client: HackerOneClient,
    username: str,
    start_date: str,
    end_date: str,
    limit: int,
    page_size: int,
) -> dict[str, Any]:
    query_string = (
        f'reporter:("{username}") '
        f"AND latest_disclosable_activity_at:>={start_date} "
        f"AND latest_disclosable_activity_at:<={end_date}"
    )
    items: list[dict[str, Any]] = []
    total_count = 0
    offset = 0
    sort = {"field": "latest_disclosable_activity_at", "direction": "DESC"}

    while len(items) < limit:
        size = min(page_size, limit - len(items))
        data = client.graphql(
            operation_name="HacktivitySearchQuery",
            query=HACKTIVITY_QUERY,
            variables={
                "queryString": query_string,
                "from": offset,
                "size": size,
                "sort": sort,
            },
            product_area="hacktivity",
            product_feature="user_hacktivity",
        )
        search = data.get("search") or {}
        total_count = search.get("total_count") or 0
        nodes = search.get("nodes") or []
        if not nodes:
            break

        for node in nodes:
            if node.get("__typename") == "HacktivityDocument":
                items.append(normalize_hacktivity_item(username, node))

        offset += len(nodes)
        if offset >= total_count:
            break

    return {
        "username": username,
        "query_string": query_string,
        "start_date": start_date,
        "end_date": end_date,
        "total_count": total_count,
        "sample_count": len(items),
        "items": items,
    }


def normalize_hacktivity_item(username: str, node: dict[str, Any]) -> dict[str, Any]:
    report = node.get("report") or {}
    team = node.get("team") or {}
    reporter = node.get("reporter") or {}
    generated_content = report.get("report_generated_content") or {}
    return {
        "username": username,
        "reporter_username": reporter.get("username"),
        "hacktivity_id": node.get("_id") or node.get("id"),
        "graphql_id": node.get("id"),
        "report_id": report.get("databaseId"),
        "report_title": report.get("title"),
        "report_url": report.get("url"),
        "report_substate": report.get("substate"),
        "disclosed_at": report.get("disclosed_at"),
        "submitted_at": node.get("submitted_at"),
        "latest_disclosable_activity_at": node.get("latest_disclosable_activity_at"),
        "latest_disclosable_action": node.get("latest_disclosable_action"),
        "team_handle": team.get("handle"),
        "team_name": team.get("name"),
        "team_url": team.get("url"),
        "currency": team.get("currency"),
        "severity_rating": node.get("severity_rating"),
        "cwe": node.get("cwe"),
        "cve_ids": node.get("cve_ids") or [],
        "votes": node.get("votes"),
        "total_awarded_amount": node.get("total_awarded_amount"),
        "public": node.get("public"),
        "disclosed": node.get("disclosed"),
        "has_collaboration": node.get("has_collaboration"),
        "collaborators": [
            collaborator.get("username")
            for collaborator in (node.get("collaborators") or [])
            if collaborator.get("username")
        ],
        "hacktivity_summary": generated_content.get("hacktivity_summary"),
    }
