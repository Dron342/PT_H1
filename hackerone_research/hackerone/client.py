import json
import re
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from typing import Any

from hackerone_research.config import HACKERONE_BASE_URL


class HackerOneClient:
    def __init__(self, base_url: str = HACKERONE_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.csrf_token: str | None = None

    def ensure_csrf_token(self) -> str:
        if self.csrf_token:
            return self.csrf_token

        html = self.get_text("/leaderboard")
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
        if not match:
            raise RuntimeError("Could not find CSRF token on HackerOne page.")

        self.csrf_token = match.group(1)
        return self.csrf_token

    def get_text(self, path: str) -> str:
        url = urllib.parse.urljoin(self.base_url, path)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "Mozilla/5.0 hackerone-research-sample/1.0",
            },
        )
        with self.opener.open(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")

    def graphql(
        self,
        operation_name: str,
        query: str,
        variables: dict[str, Any],
        product_area: str,
        product_feature: str,
    ) -> dict[str, Any]:
        payload = json.dumps(
            {
                "operationName": operation_name,
                "query": query,
                "variables": variables,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/graphql",
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 hackerone-research-sample/1.0",
                "x-csrf-token": self.ensure_csrf_token(),
                "x-product-area": product_area,
                "x-product-feature": product_feature,
            },
        )

        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GraphQL HTTP {error.code}: {body[:500]}") from error

        data = json.loads(body)
        if data.get("errors"):
            messages = "; ".join(error.get("message", "Unknown error") for error in data["errors"])
            raise RuntimeError(f"GraphQL error in {operation_name}: {messages}")
        return data["data"]
