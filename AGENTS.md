# AGENTS.md — Instructions for Codex

## Core rule
Execute tasks strictly in order from TASKS_CODEX.md.
After EACH step, append a log entry to WORKLOG.md.

## Safety & scope
- Minimal dependencies. Prefer stdlib and existing repo deps.
- Keep existing style and structure.
- Do NOT touch unrelated files.
- Ask before running destructive commands (rm, reset, migrations, DB schema changes).
- Do NOT change product requirements unless TASKS_CODEX.md says so.

## Logging requirement (mandatory)
After each step, append to WORKLOG.md:
- Step number + title
- What you did (bullets)
- Files changed (list)
- Commands run + results
- Notes / next risks

## Verification
- Run the relevant verify command after each step (if available).
- If no tests exist, add a minimal smoke test or runtime check when feasible.

