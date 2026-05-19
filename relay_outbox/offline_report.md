# zipcode offline report

        Gemma model requested: `gemma4:e2b`
        Model server status: unavailable in this run
        Reason: dry-run requested

        ## Task
        Find the bug in the water sensor parser and propose a safe fix.

        ## Local evidence inspected
        README.md
sensor_parser.py

        ## Patch plan
        1. Read the files listed above and identify the smallest code path tied to the task.
        2. Make a local-only patch; do not call cloud APIs or fetch remote code.
        3. Run the project tests or a focused smoke command.
        4. Save the transcript so a field operator can audit what happened offline.

        This fallback demonstrates the no-network workflow. For the hackathon
        judging path, start Ollama with a Gemma 4 model and rerun the same command.