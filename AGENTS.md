When doing a change always do a code review after the task is complete.

# Code Review

Focus on:

- Code quality and best practices
- Potential bugs and edge cases
- Performance implications
- Security considerations

Provide constructive feedback without making direct changes.

# Agents

We have the following agents:

@code-simplifier - simplifies and refines code for clarity, consistency, and maintainability
@review - for reviewing code before we create a PR
@pr-check - checks PR comments/ code suggestions, auto-fixes what makes sense, responds to the rest
@security - for security audits, vulnerability scanning, and secret detection

# Git Flow Management

See the `git` skill (auto-loads when relevant). Core rules: never push to `master`/`main`, never auto-merge PRs, branch-based development, plan before non-trivial action.

# Documentation & Alignment

See the `documentation-alignment` skill (auto-loads when relevant). Covers ubiquitous language, ADRs for non-obvious decisions, and aligning on data relationships, state transitions, and deletion behavior before writing code.
