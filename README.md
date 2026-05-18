# zipcode: Offline AI Coding Help for Places the Cloud Cannot Go

`zipcode` is a Gemma 4 powered local coding agent for air-gapped, low-connectivity,
and privacy-sensitive environments. It helps field teams inspect a local codebase,
reason over files, and produce a patch plan without sending source code to the
cloud.

The prototype is intentionally small enough to audit:

- Python stdlib only
- local workspace sandboxing
- local search and file-reading tools
- Ollama-compatible Gemma 4 chat backend
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

With a local Gemma 4 model running through Ollama:

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

`zipcode` turns Gemma 4 into a local coding loop:

1. collect only local evidence,
2. ask the local model for a grounded plan,
3. preserve a transcript for audit,
4. let a human operator approve changes.

## Architecture

```text
operator task
  -> workspace sandbox
  -> local tools: list_files, read_file, search_text
  -> Gemma 4 through local Ollama-compatible chat
  -> patch plan + tests + audit transcript
```

The agent refuses to read outside the selected workspace. It does not need
network access after the model is installed.

## Hackathon Track Fit

- Main Track: practical real-world impact with working code.
- Impact Track: Digital Equity & Inclusivity, because it brings coding help to
  places with weak connectivity and limited infrastructure.
- Special Technology Track: Ollama/local operations when run with Gemma 4 locally.

## Relationship to Hollow AgentOS

This submission is a focused, judge-friendly slice inspired by the local-agent
work in `hollow-agentOS`. Hollow explores long-running autonomous local agents;
`zipcode` narrows that idea into one clear workflow: local coding help for
air-gapped places.

## License

MIT
