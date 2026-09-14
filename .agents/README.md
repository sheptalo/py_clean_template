# .agents

Vendor-neutral guidance and skills for AI coding tools working in this repo, kept as plain files (not locked behind Claude-specific mechanisms) so any tool that reads a project's files can pick them up.

- [`skills/karpathy-guidelines/`](skills/karpathy-guidelines/) — behavioral guidelines (think before coding, simplicity first, surgical changes, goal-driven execution).
- [`skills/code-review/`](skills/code-review/) — multi-agent PR review skill (Claude Code + `gh` specific; see its README for caveats).
