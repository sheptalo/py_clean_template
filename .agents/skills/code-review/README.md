# code-review

Vendored from Anthropic's official Claude Code plugin marketplace (`claude-plugins-official`, plugin `code-review`), 2026-09-08.

Multi-agent, confidence-scored PR review: launches parallel agents to check CLAUDE.md compliance, scan for bugs, and read git/PR history, scores each finding 0-100, and posts only findings scoring ≥80 as a PR comment via `gh`.

**Not tool-agnostic like `karpathy-guidelines`** — this one assumes an agent runtime that can launch parallel subagents (Claude Code's `Task`/`Agent` tool) and the GitHub CLI (`gh`) with a GitHub remote. Kept here as [`SKILL.md`](SKILL.md) as the closest thing to a portable copy of the skill content; it won't run as-is in a tool without equivalent subagent orchestration.

Claude Code itself already exposes the newer, built-in `/code-review` skill (effort levels, `--comment`/`--fix`, `ultra` cloud review — see the root `CLAUDE.md`/session docs) which supersedes this plugin day-to-day; that built-in skill ships inside the app and isn't available as a separate file to vendor here.
