#!/usr/bin/env python3
"""zipcode: a local-first coding agent for low-connectivity places.

The prototype is intentionally small: it runs with Python stdlib only, reads a
bounded workspace, calls a local Ollama-compatible Gemma 4 model when present,
and falls back to an evidence-only offline report when no model server is
available. The fallback exists so judges can inspect the workflow without a
large model download; the Gemma path is the intended submission path.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


MAX_FILE_BYTES = 24_000
DEFAULT_MODEL = os.environ.get("GEMMA_MODEL", "gemma4:e2b")
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")


@dataclass
class Evidence:
    label: str
    content: str


class Workspace:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root.resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"Workspace does not exist: {self.root}")

    def safe_path(self, user_path: str) -> pathlib.Path:
        candidate = (self.root / user_path).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise ValueError(f"Refusing to read outside workspace: {user_path}")
        return candidate

    def read_file(self, user_path: str) -> Evidence:
        path = self.safe_path(user_path)
        if not path.is_file():
            return Evidence(f"read:{user_path}", "File not found.")
        data = path.read_bytes()[:MAX_FILE_BYTES]
        text = data.decode("utf-8", errors="replace")
        if path.stat().st_size > MAX_FILE_BYTES:
            text += "\n\n[truncated for local context budget]"
        return Evidence(f"read:{user_path}", text)

    def list_files(self, limit: int = 80) -> Evidence:
        ignored = {".git", "__pycache__", "node_modules", ".venv", "dist", "build"}
        rows: list[str] = []
        for path in sorted(self.root.rglob("*")):
            if any(part in ignored for part in path.relative_to(self.root).parts):
                continue
            if path.is_file():
                rows.append(str(path.relative_to(self.root)).replace("\\", "/"))
            if len(rows) >= limit:
                break
        return Evidence("workspace:file-list", "\n".join(rows) or "(empty)")

    def search_text(self, query: str, limit: int = 40) -> Evidence:
        if shutil.which("rg"):
            proc = subprocess.run(
                ["rg", "-n", "--hidden", "--glob", "!**/.git/**", query, str(self.root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
            )
            lines = proc.stdout.splitlines()[:limit]
            return Evidence(f"search:{query}", "\n".join(lines) or "No matches.")

        matches: list[str] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if query.lower() in line.lower():
                    rel = path.relative_to(self.root)
                    matches.append(f"{rel}:{number}:{line}")
                    if len(matches) >= limit:
                        return Evidence(f"search:{query}", "\n".join(matches))
        return Evidence(f"search:{query}", "No matches.")


class GemmaLocalClient:
    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 8192},
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("message", {}).get("content", "").strip()


def build_prompt(task: str, evidence: Iterable[Evidence]) -> list[dict[str, str]]:
    evidence_text = "\n\n".join(
        f"## {item.label}\n{item.content}" for item in evidence
    )
    system = (
        "You are zipcode, an offline AI coding helper for air-gapped, "
        "low-connectivity, and privacy-sensitive environments. Use only the "
        "provided local evidence. Be concrete, cite filenames, and return a "
        "safe patch plan with tests. Do not invent cloud services or files."
    )
    user = f"Task:\n{task}\n\nLocal evidence:\n{evidence_text}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def offline_report(task: str, evidence: list[Evidence], model: str, error: str) -> str:
    files = next((e.content for e in evidence if e.label == "workspace:file-list"), "")
    return textwrap.dedent(
        f"""
        # zipcode offline report

        Gemma model requested: `{model}`
        Model server status: unavailable in this run
        Reason: {error}

        ## Task
        {task}

        ## Local evidence inspected
        {files}

        ## Patch plan
        1. Read the files listed above and identify the smallest code path tied to the task.
        2. Make a local-only patch; do not call cloud APIs or fetch remote code.
        3. Run the project tests or a focused smoke command.
        4. Save the transcript so a field operator can audit what happened offline.

        This fallback demonstrates the no-network workflow. For the hackathon
        judging path, start Ollama with a Gemma 4 model and rerun the same command.
        """
    ).strip()


def run(args: argparse.Namespace) -> int:
    workspace = Workspace(pathlib.Path(args.root))
    evidence = [workspace.list_files()]
    for path in args.read:
        evidence.append(workspace.read_file(path))
    for query in args.search:
        evidence.append(workspace.search_text(query))

    messages = build_prompt(args.task, evidence)
    if args.dry_run:
        print(offline_report(args.task, evidence, args.model, "dry-run requested"))
        return 0

    client = GemmaLocalClient(args.model, args.ollama_url)
    try:
        print(client.chat(messages))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(offline_report(args.task, evidence, args.model, str(exc)))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run zipcode against a local workspace.")
    parser.add_argument("--root", default=".", help="workspace root to inspect")
    parser.add_argument("--task", required=True, help="coding task for the local agent")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="local Gemma 4 model name")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama base URL")
    parser.add_argument("--read", action="append", default=[], help="file to include")
    parser.add_argument("--search", action="append", default=[], help="text query to search")
    parser.add_argument("--dry-run", action="store_true", help="skip model call")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args(sys.argv[1:])))
