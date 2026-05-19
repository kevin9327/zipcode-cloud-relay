#!/usr/bin/env python3
"""zipcode Cloud Relay dry-run.

This connected-side companion turns an approved local zipcode report into a
structured handoff bundle for Google Cloud Agent Builder and GitLab MCP style
workflow actions. By default it writes local JSON only, so judges can inspect
the relay without credentials. If GitLab variables are present, it can also
open a real GitLab issue through the REST API as a practical MCP-compatible
action target.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass


DEFAULT_OUTBOX = pathlib.Path("relay_outbox")


@dataclass
class RelayBundle:
    project: str
    task: str
    local_report: str
    approved_by: str
    created_at: str
    source_policy: str


def read_text(path: pathlib.Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")


def build_agent_builder_payload(bundle: RelayBundle) -> dict[str, object]:
    return {
        "agent": "zipcode-cloud-relay",
        "runtime": "google-cloud-agent-builder",
        "model": os.environ.get("GEMINI_MODEL", "gemini-1.5-pro"),
        "goal": "Turn approved offline coding evidence into connected workflow actions.",
        "constraints": [
            "Do not request the full repository unless the human operator approves it.",
            "Use only the approved local report as initial source evidence.",
            "Create traceable GitLab work items before any code-changing action.",
        ],
        "input": asdict(bundle),
    }


def build_gitlab_mcp_actions(bundle: RelayBundle) -> list[dict[str, object]]:
    issue_body = textwrap.dedent(
        f"""
        zipcode Cloud Relay received an approved offline coding report.

        Task:
        {bundle.task}

        Source policy:
        {bundle.source_policy}

        Local report:
        {bundle.local_report}
        """
    ).strip()
    return [
        {
            "tool": "gitlab.create_issue",
            "args": {
                "title": f"zipcode relay: {bundle.task[:80]}",
                "description": issue_body,
                "labels": ["zipcode", "agent-builder", "human-approved"],
            },
        },
        {
            "tool": "gitlab.create_merge_request_draft",
            "args": {
                "title": f"Draft fix from zipcode relay: {bundle.task[:72]}",
                "description": "Attach the approved patch after connected review.",
                "source_branch": "zipcode/approved-field-fix",
                "target_branch": "main",
            },
        },
        {
            "tool": "gitlab.add_review_note",
            "args": {
                "body": "Agent Builder should preserve the offline evidence transcript in the MR audit trail.",
            },
        },
    ]


def maybe_create_gitlab_issue(project_id: str, action: dict[str, object]) -> str:
    token = os.environ.get("GITLAB_TOKEN")
    base_url = os.environ.get("GITLAB_URL", "https://gitlab.com").rstrip("/")
    if not token:
        return "skipped: GITLAB_TOKEN is not set"
    if not project_id:
        return "skipped: GITLAB_PROJECT_ID is not set"

    args = action["args"]
    data = urllib.parse.urlencode(
        {
            "title": args["title"],
            "description": args["description"],
            "labels": ",".join(args["labels"]),
        }
    ).encode("utf-8")
    encoded_project = urllib.parse.quote_plus(project_id)
    request = urllib.request.Request(
        f"{base_url}/api/v4/projects/{encoded_project}/issues",
        data=data,
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return f"created: {payload.get('web_url', '(no web_url returned)')}"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return f"failed: {exc}"


def run(args: argparse.Namespace) -> int:
    report = read_text(pathlib.Path(args.report))
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    bundle = RelayBundle(
        project=args.project,
        task=args.task,
        local_report=report,
        approved_by=args.approved_by,
        created_at=now,
        source_policy="bounded local evidence only; full repository upload is not approved",
    )
    payload = build_agent_builder_payload(bundle)
    actions = build_gitlab_mcp_actions(bundle)

    outbox = pathlib.Path(args.outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "agent_builder_payload.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (outbox / "gitlab_mcp_actions.json").write_text(
        json.dumps(actions, indent=2), encoding="utf-8"
    )

    status = "dry-run: wrote local relay payloads"
    if args.dispatch_gitlab_issue:
        status = maybe_create_gitlab_issue(args.gitlab_project_id, actions[0])

    print(json.dumps({"outbox": str(outbox), "status": status}, indent=2))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a zipcode Cloud Relay handoff.")
    parser.add_argument("--project", default="zipcode Cloud Relay")
    parser.add_argument("--task", required=True)
    parser.add_argument("--report", required=True, help="approved local zipcode report")
    parser.add_argument("--approved-by", default="field operator")
    parser.add_argument("--outbox", default=str(DEFAULT_OUTBOX))
    parser.add_argument("--dispatch-gitlab-issue", action="store_true")
    parser.add_argument("--gitlab-project-id", default=os.environ.get("GITLAB_PROJECT_ID", ""))
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
