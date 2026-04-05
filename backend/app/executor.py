"""
Real action executor — uses the scoped token to perform the actual API call.
Supports Slack and GitHub out of the box.
"""
import httpx

async def execute_action(
    service: str,
    action: str,
    parameters: dict,
    access_token: str,
) -> dict:
    """Execute the real API call using the scoped token from Token Vault."""

    if service == "slack":
        return await _slack_action(action, parameters, access_token)
    elif service == "github":
        return await _github_action(action, parameters, access_token)
    elif service == "gmail":
        return await _gmail_action(action, parameters, access_token)
    else:
        raise ValueError(f"Unsupported service: {service}")


async def _slack_action(action: str, params: dict, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        if action == "send_message":
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json={
                    "channel": params["channel"],
                    "text": params["text"],
                },
            )
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Slack error: {data.get('error')}")
            return {"message_ts": data["ts"], "channel": data["channel"]}

        elif action == "read_channel":
            resp = await client.get(
                "https://slack.com/api/conversations.history",
                headers=headers,
                params={"channel": params["channel"], "limit": params.get("limit", 10)},
            )
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Slack error: {data.get('error')}")
            return {"messages": data["messages"]}

        elif action == "list_users":
            resp = await client.get(
                "https://slack.com/api/users.list",
                headers=headers,
            )
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Slack error: {data.get('error')}")
            return {"members": [{"id": m["id"], "name": m["name"]} for m in data["members"]]}

    raise ValueError(f"Unknown Slack action: {action}")


async def _github_action(action: str, params: dict, token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    owner = params.get("owner")
    repo = params.get("repo")

    async with httpx.AsyncClient() as client:
        if action == "create_issue":
            resp = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
                headers=headers,
                json={"title": params["title"], "body": params.get("body", "")},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"issue_number": data["number"], "url": data["html_url"]}

        elif action == "read_repo":
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"name": data["name"], "description": data["description"], "stars": data["stargazers_count"]}

        elif action == "create_pr":
            resp = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                headers=headers,
                json={
                    "title": params["title"],
                    "body": params.get("body", ""),
                    "head": params["head"],
                    "base": params["base"],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"pr_number": data["number"], "url": data["html_url"]}

    raise ValueError(f"Unknown GitHub action: {action}")


async def _gmail_action(action: str, params: dict, token: str) -> dict:
    import base64
    from email.mime.text import MIMEText

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        if action == "send_email":
            msg = MIMEText(params["body"])
            msg["to"] = params["to"]
            msg["subject"] = params["subject"]
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            resp = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers=headers,
                json={"raw": raw},
            )
            resp.raise_for_status()
            return {"message_id": resp.json()["id"]}

    raise ValueError(f"Unknown Gmail action: {action}")
