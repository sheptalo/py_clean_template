# karpathy-guidelines

Vendored from https://github.com/forrestchang/andrej-karpathy-skills (MIT license), 2026-09-08.

Four behavioral principles that curb common LLM coding mistakes: think before coding, simplicity first, surgical changes, goal-driven execution.

Same content, three formats so any tool in this repo can pick it up:

| File | Consumed by |
|---|---|
| [`SKILL.md`](SKILL.md) | Claude Code Agent Skills (`Skill` tool / `~/.claude/skills`) |
| [`CLAUDE.md`](CLAUDE.md) | Any tool that reads a root/merged `CLAUDE.md` — copy or `@`-import its contents |

Claude Code itself already has this as a global plugin (`andrej-karpathy-skills:karpathy-guidelines`, see `~/.claude/SKILL_DEFAULTS.md`), so this copy exists for other tools/agents working in this repo, not to replace the global plugin.
