# personal-skills

A personal collection of cross-platform AI-assistant **agents** and **skills**
that work with [Claude Code](https://claude.com/claude-code),
[OpenCode](https://opencode.ai), and Codex.

The two are different primitives:

- **Agents** (subagents) run in their own isolated context, are invoked
  explicitly (e.g. via the `Task` tool), and return a summary to the caller.
  Use them for long, isolated, parallelizable work like deep code reviews
  or security audits.
- **Skills** are procedural knowledge that the main agent loads on-demand
  when a task matches the skill's `description`. Use them for "how to do X"
  rules and workflows that the main agent should follow while doing the
  work itself.

## Install

```bash
./install.sh
```

The installer symlinks every agent and skill in this repo into `~/.claude/`,
`~/.config/opencode/`, and `~/.codex/`. It is idempotent — re-running
replaces existing symlinks, prunes dangling links to removed items, and
backs up any real files at the target paths to `<path>.bak-<timestamp>`
before replacing them.

Codex uses TOML custom-agent files instead of Markdown agent files, so
`install.sh` generates `~/.codex/agents/<name>.toml` from each Markdown agent.
The Markdown files remain the source of truth for Claude Code and OpenCode.

To uninstall, remove the symlinks under:

- `~/.claude/{agents,skills,commands}`
- `~/.config/opencode/{agents,skills,commands}`
- `~/.codex/{agents,skills}` and `~/.codex/AGENTS.md`

## Agents

| Agent | Role |
|---|---|
| `code-simplifier` | Simplifies and refines code for clarity, consistency, and maintainability while preserving behavior |
| `pr-check` | Processes PR comments, applies safe fixes, replies to remaining items |
| `review` | Reviews code for quality, bugs, performance, security |
| `security` | Security audits: secret detection, OWASP-style vulnerability scanning |

## Skills

| Skill | Purpose |
|---|---|
| `git` | Git flow rules: never push to `master`/`main`, never auto-merge PRs, branch-based development, plan before non-trivial action |
| `documentation-alignment` | Ubiquitous language, ADRs for non-obvious decisions, aligning on data relationships and behavior before writing code |
| `insta-skill` | Project-based Instagram content generation with style guides, saved post history, duplicate checks, Veo video prompts, overlays, and Buffer workflows |

## Repo layout

```
agents/
  <name>/
    <name>.md            # subagent body (frontmatter + prompt)
    commands/            # optional slash commands scoped to this agent
      *.md
skills/
  <name>/                # whole folder is symlinked into the target location
    SKILL.md             # skill body (frontmatter + procedural knowledge)
    templates/           # optional sibling files referenced from SKILL.md
    scripts/             # optional helper scripts
    commands/            # optional slash commands scoped to this skill
      *.md
```

Skill folders are symlinked as a unit, so any sibling files (templates,
reference docs, helper scripts) are reachable from the skill without
needing additional installer wiring.

### Adding an agent

Create a new folder under `agents/`:

```
agents/my-agent/my-agent.md
```

Frontmatter combines Claude Code and OpenCode dialects. For Codex, the
installer converts the Markdown agent into a TOML custom-agent file:

```yaml
---
name: my-agent                   # Claude Code
description: ...                 # both
mode: subagent                   # OpenCode
temperature: 0.1                 # OpenCode
tools:                           # OpenCode
  write: false
  edit: false
  bash: true
---
```

Re-run `./install.sh` to wire it up.

> Permission enforcement (`tools.write: false`, etc.) only applies in
> OpenCode. In Claude Code, subagents inherit the parent session's
> permission mode, so any "no write" guarantees are prose-only on that
> side. In Codex, `tools.write`, `tools.edit`, and `tools.bash` are mapped
> only to a coarse custom-agent `sandbox_mode` (`read-only` or
> `workspace-write`).

### Adding a skill

Create a new folder under `skills/` with a `SKILL.md`:

```
skills/my-skill/SKILL.md
```

Frontmatter follows the OpenCode skill spec (Claude Code uses the same
shape):

```yaml
---
name: my-skill
description: One or two sentences describing exactly when to load this
  skill. Be specific - the host agent uses this to decide.
---
```

Constraints:

- `name` must be lowercase alphanumeric with single-hyphen separators
  (`^[a-z0-9]+(-[a-z0-9]+)*$`) and match the folder name.
- `description` must be 1–1024 characters.

See the [OpenCode skills docs](https://opencode.ai/docs/skills/) for the
full spec.
