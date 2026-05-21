#!/usr/bin/env bash
# Installs every agent and skill in this repo into Claude Code (~/.claude)
# and OpenCode (~/.config/opencode). Idempotent: re-running replaces
# symlinks; existing real files are backed up to
# <path>.bak-<timestamp>-<pid> before being replaced. Dangling symlinks
# pointing back into this repo are cleaned up at the start of each run
# so removed items disappear.
#
# Repo layout:
#   agents/<name>/*.md           - subagents (one or more .md files per folder)
#   agents/<name>/commands/*.md  - slash commands scoped to that agent
#   skills/<name>/SKILL.md       - skill body (required)
#   skills/<name>/...            - any sibling files (templates, scripts, refs)
#                                  are included because the skill folder is
#                                  symlinked as a whole
#   skills/<name>/commands/*.md  - slash commands scoped to that skill
#
# Install targets:
#   Subagents:     ~/.claude/agents/<name>.md
#                  ~/.config/opencode/agents/<name>.md
#   Skills:        ~/.claude/skills/<name>            (folder symlink)
#                  ~/.config/opencode/skills/<name>   (folder symlink)
#   Commands:      ~/.claude/commands/<name>.md
#                  ~/.config/opencode/commands/<name>.md
#   AGENTS.md:     ~/.claude/AGENTS.md
#                  ~/.config/opencode/AGENTS.md

set -euo pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
OPENCODE_DIR="${HOME}/.config/opencode"

# Generate a backup path that doesn't already exist. Combines second-resolution
# timestamp with PID and a tilde-suffix fallback to avoid collisions when the
# script runs multiple times within the same second.
backup_path() {
  local dst="$1"
  local backup="${dst}.bak-$(date +%s)-$$"
  while [[ -e "$backup" ]]; do
    backup="${backup}~"
  done
  printf '%s\n' "$backup"
}

# Symlink a single file. Replaces an existing symlink; backs up a real file.
link_file() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ -L "$dst" ]]; then
    rm "$dst"
  elif [[ -e "$dst" ]]; then
    local backup
    backup="$(backup_path "$dst")"
    echo "  backup: $dst -> $backup"
    mv "$dst" "$backup"
  fi
  ln -s "$src" "$dst"
  echo "  link:   $dst"
}

# Symlink a whole directory. Replaces an existing symlink; backs up a real dir.
link_dir() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ -L "$dst" ]]; then
    rm "$dst"
  elif [[ -e "$dst" ]]; then
    local backup
    backup="$(backup_path "$dst")"
    echo "  backup: $dst -> $backup"
    mv "$dst" "$backup"
  fi
  ln -s "$src" "$dst"
  echo "  link:   $dst/"
}

# Remove symlinks under $1 whose target points into $ROOT but no longer exists.
# Keeps the install idempotent even after items are renamed or deleted.
prune_dangling() {
  local dir="$1"
  [[ -d "$dir" ]] || return 0
  while IFS= read -r -d '' link_path; do
    local target
    target="$(readlink "$link_path")"
    if [[ "$target" == "$ROOT"/* && ! -e "$link_path" ]]; then
      echo "  prune:  $link_path (target $target gone)"
      rm "$link_path"
    fi
  done < <(find "$dir" -type l -print0 2>/dev/null)
}

# Remove empty subdirectories one level deep inside $1. Used after pruning so
# orphaned skill folders (e.g. ~/.claude/skills/old-skill/) don't accumulate.
sweep_empty() {
  local dir="$1"
  [[ -d "$dir" ]] || return 0
  find "$dir" -mindepth 1 -maxdepth 1 -type d -empty -delete 2>/dev/null || true
}

install_agent() {
  local agent_dir="$1"
  local agent_name
  agent_name="$(basename "$agent_dir")"

  echo ""
  echo "== agent: $agent_name =="

  local found=0
  for f in "$agent_dir"/*.md; do
    found=1
    local name
    name="$(basename "$f")"
    link_file "$f" "$CLAUDE_DIR/agents/$name"
    link_file "$f" "$OPENCODE_DIR/agents/$name"
  done
  if [[ $found -eq 0 ]]; then
    echo "  skip:   no .md files in $agent_dir"
  fi

  if [[ -d "$agent_dir/commands" ]]; then
    for f in "$agent_dir/commands"/*.md; do
      local name
      name="$(basename "$f")"
      link_file "$f" "$CLAUDE_DIR/commands/$name"
      link_file "$f" "$OPENCODE_DIR/commands/$name"
    done
  fi
}

install_skill() {
  local skill_dir="$1"
  local skill_name
  skill_name="$(basename "$skill_dir")"
  # Strip any trailing slash that the glob "$ROOT/skills"/*/ leaves behind so
  # `ln -s` doesn't dereference the source.
  skill_dir="${skill_dir%/}"

  echo ""
  echo "== skill: $skill_name =="

  if [[ ! -f "$skill_dir/SKILL.md" ]]; then
    echo "  skip:   no SKILL.md found"
    return 0
  fi

  # Symlink the whole skill folder so any sibling files (templates, scripts,
  # references) come along automatically.
  link_dir "$skill_dir" "$CLAUDE_DIR/skills/$skill_name"
  link_dir "$skill_dir" "$OPENCODE_DIR/skills/$skill_name"

  # Commands inside skills are installed to the platform-wide commands dirs,
  # not to the skill folder. They're already reachable via the folder symlink,
  # but OpenCode/Claude Code only discover commands from the dedicated paths.
  if [[ -d "$skill_dir/commands" ]]; then
    for f in "$skill_dir/commands"/*.md; do
      local name
      name="$(basename "$f")"
      link_file "$f" "$CLAUDE_DIR/commands/$name"
      link_file "$f" "$OPENCODE_DIR/commands/$name"
    done
  fi
}

echo "Installing from $ROOT"

echo ""
echo "Pruning dangling symlinks pointing into this repo..."
prune_dangling "$CLAUDE_DIR/agents"
prune_dangling "$CLAUDE_DIR/skills"
prune_dangling "$CLAUDE_DIR/commands"
prune_dangling "$CLAUDE_DIR/AGENTS.md"
prune_dangling "$OPENCODE_DIR/agents"
prune_dangling "$OPENCODE_DIR/skills"
prune_dangling "$OPENCODE_DIR/commands"
prune_dangling "$OPENCODE_DIR/AGENTS.md"

# Sweep up any now-empty skill folders left behind by prior installs that
# symlinked SKILL.md rather than the whole folder.
sweep_empty "$CLAUDE_DIR/skills"
sweep_empty "$OPENCODE_DIR/skills"

for d in "$ROOT/agents"/*/; do
  install_agent "$d"
done

for d in "$ROOT/skills"/*/; do
  install_skill "$d"
done

if [[ -f "$ROOT/AGENTS.md" ]]; then
  echo ""
  echo "== AGENTS.md =="
  link_file "$ROOT/AGENTS.md" "$CLAUDE_DIR/AGENTS.md"
  link_file "$ROOT/AGENTS.md" "$OPENCODE_DIR/AGENTS.md"
fi

cat <<'EOF'

Done.

Notes:
  - Claude Code ignores OpenCode-specific frontmatter ('mode', 'temperature',
    'permission'). Permission enforcement only applies in OpenCode - in Claude
    Code, subagents inherit the parent session's permission mode.
  - To uninstall, remove the symlinks under:
      ~/.claude/{agents,skills,commands} and ~/.claude/AGENTS.md
      ~/.config/opencode/{agents,skills,commands} and ~/.config/opencode/AGENTS.md
EOF
