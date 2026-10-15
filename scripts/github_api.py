"""Small GitHub REST client with explicit token scope and owned-repository paging."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class GitHubError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(f"GitHub HTTP {status}: {message}")


class GitHubRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        if target.scheme != "https" or target.hostname != "api.github.com":
            raise GitHubError(code, "unexpected API redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class GitHub:
    def __init__(self, token="", mode="public", opener=None):
        if mode not in ("public", "repository", "installation", "user"):
            raise ValueError("unsupported GitHub token kind")
        if mode in ("installation", "user") and not token:
            raise ValueError("account token is required for this token kind")
        self.token = token
        self.mode = mode
        self.opener = opener or urllib.request.build_opener(GitHubRedirect()).open

    @property
    def coverage(self):
        return {
            "public": "public_only",
            "repository": "public_only",
            "installation": "installation_accessible",
            "user": "token_accessible",
        }[self.mode]

    def request(self, method, path, data=None):
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("API paths must be relative to api.github.com")
        headers = {"Accept": "application/vnd.github+json",
                   "User-Agent": "HSI-Account-Controller/1.1",
                   "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        body = None if data is None else json.dumps(data).encode()
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request("https://api.github.com" + path,
                                     data=body, method=method, headers=headers)
        try:
            with self.opener(req, timeout=30) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            # Do not copy response bodies or authorization material into certificates.
            raise GitHubError(exc.code, exc.reason) from None
        if len(raw) > 8 * 1024 * 1024:
            raise GitHubError(0, "API response exceeds byte budget")
        return json.loads(raw) if raw else None


def owned_repositories(api, owner, limit=1000):
    if not 1 <= limit <= 10000:
        raise ValueError("repository budget must be in 1..10000")
    repos = {}
    page = 1
    while True:
        if api.mode == "installation":
            path = f"/installation/repositories?per_page=100&page={page}"
        elif api.mode == "user":
            path = f"/user/repos?affiliation=owner&sort=full_name&per_page=100&page={page}"
        else:
            login = urllib.parse.quote(owner, safe="")
            path = f"/users/{login}/repos?type=owner&sort=full_name&per_page=100&page={page}"
        payload = api.request("GET", path)
        batch = payload["repositories"] if api.mode == "installation" else payload
        if not isinstance(batch, list):
            raise GitHubError(0, "invalid repository list")
        for repo in batch:
            if repo.get("owner", {}).get("login", "").casefold() != owner.casefold():
                continue
            name = repo.get("full_name", "")
            if not name or name.count("/") != 1:
                raise GitHubError(0, "invalid repository identity")
            repos[name] = repo
        if len(repos) > limit:
            return sorted(repos.values(), key=lambda r: r["full_name"].casefold())[:limit], True
        if len(batch) < 100:
            return sorted(repos.values(), key=lambda r: r["full_name"].casefold()), False
        page += 1
        if page > 101:
            raise GitHubError(0, "repository pagination exceeds budget")
