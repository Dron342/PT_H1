from typing import Any

from hackerone_research.hackerone.client import HackerOneClient
from hackerone_research.hackerone.queries import PROFILE_QUERY


def fetch_profile(client: HackerOneClient, username: str) -> dict[str, Any]:
    data = client.graphql(
        operation_name="UserProfilePageQuery",
        query=PROFILE_QUERY,
        variables={"resourceIdentifier": username},
        product_area="profile",
        product_feature="profile",
    )
    return data.get("user") or {}


def compact_socials(profile: dict[str, Any]) -> dict[str, str]:
    handles = {
        "website": profile.get("website"),
        "bugcrowd": profile.get("bugcrowd_handle"),
        "hack_the_box": profile.get("hack_the_box_handle"),
        "github": profile.get("github_handle"),
        "gitlab": profile.get("gitlab_handle"),
        "linkedin": profile.get("linkedin_handle"),
        "twitter": profile.get("twitter_handle"),
    }
    return {key: value for key, value in handles.items() if value}
