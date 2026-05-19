# zipcode Cloud Relay: Field Coding Agent for Low-Connectivity Teams

`zipcode Cloud Relay` is a local-first coding agent prototype for field teams
working in air-gapped, low-connectivity, and privacy-sensitive environments. The
Google Cloud Rapid Agent Hackathon direction extends the local agent into a
hybrid workflow: local evidence gathering first, then a human-approved relay to
Gemini, Google Cloud Agent Builder, and GitLab MCP when connectivity returns.

The prototype is intentionally small enough to audit:

- Python stdlib only
- local workspace sandboxing
- local search and file-reading tools
- Ollama-compatible local model backend in the offline prototype
- planned Gemini + Google Cloud Agent Builder connected relay
- planned GitLab MCP workflow handoff for issues, merge requests, and review notes
- deterministic dry-run mode for judges without the model installed

## Quick Demo

```powershell
python zipcode_agent.py `
  --root examples/airgap_demo_workspace `
  --task "Find the bug in the water sensor parser and propose a safe fix." `
  --read README.md `
  --search TODO `
  --dry-run
```

With a local model running through Ollama:

```powershell
$env:GEMMA_MODEL="gemma4:e2b"
python zipcode_agent.py `
  --root examples/airgap_demo_workspace `
  --task "Find the bug in the water sensor parser and propose a safe fix." `
  --read README.md `
  --search TODO
```

## Why This Matters

Many useful coding situations are not cloud-friendly: disaster-response laptops,
clinics with sensitive patient tooling, rural schools, public-interest NGOs, and
teams working under unstable connectivity. In those places, a cloud coding
assistant is either unavailable or inappropriate.

`zipcode` turns local model reasoning into a field coding loop:

1. collect only local evidence,
2. ask the local model for a grounded plan,
3. preserve a transcript for audit,
4. let a human operator approve changes.

## Architecture

```text
operator task
  -> workspace sandbox
  -> local tools: list_files, read_file, search_text
  -> local model through Ollama-compatible chat
  -> patch plan + tests + audit transcript
```

The agent refuses to read outside the selected workspace. It does not need
network access after the local model is installed. The Cloud Relay direction
adds a connected approval queue so approved evidence bundles can be routed to
Gemini and GitLab MCP without uploading an entire repository blindly.

## Google Cloud Rapid Agent Track Fit

- Partner track: GitLab.
- Google Cloud fit: Agent Builder + Gemini can orchestrate the connected relay.
- GitLab MCP fit: code-agent output naturally maps to issues, merge requests,
  review summaries, and audit updates.
- Impact fit: low-connectivity field teams keep sensitive source local while
  still getting structured software workflow help.

## Relationship to Hollow AgentOS

This submission is a focused, judge-friendly slice inspired by the local-agent
work in `hollow-agentOS`. Hollow explores long-running autonomous local agents;
`zipcode` narrows that idea into one clear workflow: local coding help for
air-gapped places.

## License

MIT
