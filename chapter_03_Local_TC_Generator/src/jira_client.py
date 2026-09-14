import re
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth

from config_store import get_setting


class JiraError(Exception):
    pass


class ConnectionError(JiraError):
    pass


class AuthenticationError(JiraError):
    pass


class NotFoundError(JiraError):
    pass


def _normalize_jira_url(raw_url: str) -> str:
    value = (raw_url or "").strip()
    if not value:
        return ""
    if "//" in value:
        parsed = urlparse(value)
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return value.rstrip("/")


def _build_url(path: str) -> str:
    base = _normalize_jira_url(get_setting("jira_url")).rstrip("/")
    if not base:
        raise ConnectionError("Jira URL is not configured. Add it in Settings.")
    return f"{base}{path}"


def fetch_ticket(ticket_key: str) -> dict:
    """Fetch a Jira ticket and return needed fields for test case generation."""
    email = get_setting("jira_email")
    token = get_setting("jira_api_token")

    if not email or not token:
        raise AuthenticationError(
            "Jira credentials not configured. Go to Settings page to set them up."
        )

    url = _build_url(f"/rest/api/3/issue/{ticket_key}")

    try:
        resp = requests.get(
            url,
            auth=HTTPBasicAuth(email, token),
            headers={"Accept": "application/json"},
            timeout=20,
        )
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(f"Cannot reach Jira at {get_setting('jira_url')}. Check the URL in Settings.") from exc
    except requests.exceptions.Timeout as exc:
        raise ConnectionError("Jira request timed out. Check your network or Jira URL.") from exc

    if resp.status_code == 401:
        raise AuthenticationError(
            "Jira authentication failed. Check your email and API token in Settings."
        )
    if resp.status_code == 404:
        raise NotFoundError(f"Ticket **{ticket_key}** not found.")
    if not resp.ok:
        raise JiraError(f"Jira error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    fields = data.get("fields", {})

    summary = fields.get("summary", "")
    description_raw = fields.get("description", {})

    if isinstance(description_raw, dict):
        description = _extract_text_from_adf(description_raw)
    else:
        description = str(description_raw) if description_raw else ""

    acceptance_criteria = _extract_acceptance_criteria(description, fields)

    return {
        "key": data.get("key", ticket_key),
        "summary": summary,
        "description": description,
        "acceptance_criteria": acceptance_criteria,
    }


def _extract_text_from_adf(doc: dict) -> str:
    """Extract plain text from ADF JSON from Jira Cloud."""
    texts = []

    def walk(node):
        if node.get("type") == "text":
            texts.append(node.get("text", ""))
        for child in node.get("content", []):
            walk(child)

    walk(doc)
    return "\n".join(texts)


def _extract_acceptance_criteria(description: str, fields: dict) -> str:
    """Try to extract acceptance criteria from the description or matching field names."""
    patterns = [
        r"(?is)acceptance\s*criteria\s*:?(?:\n|\r\n)(.*?)(?=\n\s*\n\w|\Z)",
        r"(?is)##\s*acceptance\s*criteria\s*(?:\n|\r\n)(.*?)(?=\n#|\Z)",
        r"(?is)ac\s*:?(?:\n|\r\n)(.*?)(?=\n\s*\n\w|\Z)",
    ]
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return match.group(1).strip()

    for key, value in fields.items():
        if "acceptance" in key.lower() and value:
            return str(value)

    return ""


def test_connection() -> str:
    """Verify Jira credentials. Returns the display name on success."""
    url = _build_url("/rest/api/3/myself")
    email = get_setting("jira_email")
    token = get_setting("jira_api_token")

    resp = requests.get(
        url,
        auth=HTTPBasicAuth(email, token),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    if resp.ok:
        return resp.json().get("displayName", "Connected")
    if resp.status_code == 401:
        raise AuthenticationError("Invalid Jira credentials")
    raise JiraError(f"Error {resp.status_code}: {resp.text[:200]}")
