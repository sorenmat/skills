#!/usr/bin/env bash
# Installs every skill in this repo into Claude Code (~/.claude) and OpenCode
# (~/.config/opencode). Idempotent: re-running replaces symlinks; existing real
# files are backed up to <path>.bak-<timestamp> before being replaced.
#
# Skill folder convention (each top-level dir in this repo):
#   <skill>/SKILL.md            — Claude Code skill body (optional)
#   <skill>/agents/*.md         — subagents (preferred location)
#   <skill>/*.md                — subagents (fallback; excludes SKILL.md/README.md/CHANGELOG.md/LICENSE.md)
#   <skill>/commands/*.md       — slash commands

set -euo pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
OPENCODE_DIR="${HOME}/.config/opencode"

link() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ -L "$dst" ]]; then
    rm "$dst"
  elif [[ -e "$dst" ]]; then
    local backup="${dst}.bak-$(date +%s)"
    echo "  backup: $dst -> $backup"
    mv "$dst" "$backup"
  fi
  ln -s "$src" "$dst"
  echo "  link:   $dst"
}

install_skill() {
  local skill_dir="$1"
  local skill_name
  skill_name="$(basename "$skill_dir")"

  echo ""
  echo "== $skill_name =="

  # Claude Code skill body
  if [[ -f "$skill_dir/SKILL.md" ]]; then
    link "$skill_dir/SKILL.md" "$CLAUDE_DIR/skills/$skill_name/SKILL.md"
  fi

  # Subagents: prefer ./agents/, fall back to top-level *.md
  local -a agent_files=()
  if [[ -d "$skill_dir/agents" ]]; then
    for f in "$skill_dir/agents"/*.md; do
      agent_files+=("$f")
    done
  else
    for f in "$skill_dir"/*.md; do
      case "$(basename "$f")" in
        SKILL.md|README.md|CHANGELOG.md|LICENSE.md) continue ;;
      esac
      agent_files+=("$f")
    done
  fi
  for f in "${agent_files[@]}"; do
    local name
    name="$(basename "$f")"
    link "$f" "$CLAUDE_DIR/agents/$name"
    link "$f" "$OPENCODE_DIR/agents/$name"
  done

  # Slash commands
  if [[ -d "$skill_dir/commands" ]]; then
    for f in "$skill_dir/commands"/*.md; do
      local name
      name="$(basename "$f")"
      link "$f" "$CLAUDE_DIR/commands/$name"
      link "$f" "$OPENCODE_DIR/command/$name"
    done
  fi
}

echo "Installing skills from $ROOT"

for d in "$ROOT"/*/; do
  name="$(basename "$d")"
  case "$name" in
    .*|node_modules) continue ;;
  esac
  # treat as skill iff it has SKILL.md, agents/, commands/, or any top-level *.md
  if [[ -f "$d/SKILL.md" || -d "$d/agents" || -d "$d/commands" ]] || compgen -G "$d/*.md" >/dev/null; then
    install_skill "$d"
  fi
done

cat <<'EOF'

Done.

Notes:
  - Claude Code ignores OpenCode-specific frontmatter ('mode', 'temperature',
    'permission'). Permission enforcement only applies in OpenCode — in Claude
    Code, subagents inherit the parent session's permission mode.
  - To uninstall, remove the symlinks under:
      ~/.claude/{skills,agents,commands}
      ~/.config/opencode/{agents,command}
EOF
