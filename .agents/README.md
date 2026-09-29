# .agents

Vendor-neutral guidance and skills for AI coding tools working in this repo, kept as plain files (not locked behind Claude-specific mechanisms) so any tool that reads a project's files can pick them up.

Files ending in `.jinja` are copier templates: in a generated project they become plain `SKILL.md`.

- [`skills/vertical-slice/`](skills/vertical-slice/) — the order of a whole feature: from the domain entity to the entrypoint and the tests.
- [`skills/green/`](skills/green/) — the order of the checks and what each common failure means.
- [`skills/karpathy-guidelines/`](skills/karpathy-guidelines/) — behavioral guidelines (think before coding, simplicity first, surgical changes, goal-driven execution).
- [`skills/ponytail/`](skills/ponytail/) — the laziest working solution: YAGNI, stdlib first, no unrequested abstractions.
- [`skills/code-review/`](skills/code-review/) — multi-agent PR review skill (Claude Code + `gh` specific; see its README for caveats).
