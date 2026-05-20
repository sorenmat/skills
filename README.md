# personal-skills

A personal collection of cross-platform AI-assistant agents that work with both
[Claude Code](https://claude.com/claude-code) and
[OpenCode](https://opencode.ai). Each agent ships as its own folder so it can
later grow a `SKILL.md` orchestrator and slash commands without restructuring.

## Install

```bash
./install.sh
```

The installer symlinks every agent in this repo into both `~/.claude/` and
`~/.config/opencode/`. It is idempotent — re-running replaces existing
symlinks. Real files at the target paths are backed up to
`<path>.bak-<timestamp>` before being replaced.

To uninstall, remove the symlinks under:

- `~/.claude/{skills,agents,commands}`
- `~/.config/opencode/{agents,command}`

## Agents

| Agent | Role |
|---|---|
| `code-simplifier` | Simplifies and refines code for clarity, consistency, and maintainability while preserving behavior |
| `git` | Manages git flow: branching, PRs, never pushes to `main`/`master` |
| `pr-check` | Processes PR comments, applies safe fixes, replies to remaining items |
| `primary` | Primary orchestrator coordinating the end-to-end SDD pipeline |
| `review` | Reviews code for quality, bugs, performance, security |
| `security` | Security audits: secret detection, OWASP-style vulnerability scanning |

## Adding a new skill

Create a top-level folder following this convention:

```
<skill>/
  SKILL.md          # Claude Code orchestrator (optional; auto-triggers via description)
  agents/           # Subagents (preferred location)
    *.md
  commands/         # Slash commands
    *.md
```

If you don't use an `agents/` subfolder, top-level `*.md` files in the
skill folder are treated as subagents (excluding `SKILL.md`, `README.md`,
`CHANGELOG.md`, `LICENSE.md`). Re-run `./install.sh` to wire up the new
skill.

### Dual-format subagent frontmatter

Subagents work on both platforms by combining the two YAML dialects in a
single frontmatter block. Each tool reads what it understands and ignores
the rest:

```yaml
---
name: review                     # Claude Code
description: ...                 # both
mode: subagent                   # OpenCode
temperature: 0.1                 # OpenCode
permission:                      # OpenCode (only enforced here)
  edit: ask
  bash: allow
---
```

Note: permission enforcement (`edit: ask`, `bash: allow`) only takes effect
in OpenCode. In Claude Code, subagents inherit the parent session's
permission mode, so any "no write" guarantees are prose-only on that side.
