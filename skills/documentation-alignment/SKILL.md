---
name: documentation-alignment
description: Documentation and alignment discipline for software projects. Load when planning a new feature, discussing domain terminology, modeling data relationships, making non-obvious design choices, or whenever shared understanding is at risk. Covers ubiquitous language, Architectural Decision Records (ADRs), and aligning on data and behavior before writing code.
---

# Documentation & Alignment

Shared understanding is cheaper than rewrites. Use these practices when scoping work or making decisions that future-you (or a teammate) will need to reconstruct.

## Ubiquitous language

- Maintain a shared glossary between the codebase, developers, and domain experts. A `CONTEXT.md` file at the repo root is a good default location.
- When the user introduces a term that is fuzzy or overloaded, challenge it. Ask: "Does X mean the entity, the event, or the role?" Sharpen it to one concrete definition before writing code.
- Once a term is agreed, use it consistently in code (types, function names, table names) and in documentation. Avoid silent synonyms.

## Architectural Decision Records (ADRs)

Write an ADR when a decision:

- Is hard to reverse (e.g., choice of database, auth provider, public API shape).
- Involves a significant trade-off where a future reader would otherwise ask "why?".
- Would be surprising or non-obvious without context.

Minimum ADR contents: title, status (proposed / accepted / superseded), context (the forces at play), decision (what was chosen), and consequences (what becomes easier and what becomes harder).

Skip an ADR for trivial, easily-reversed choices. The point is to capture rationale that lives outside the code, not to bureaucratize every commit.

## Align before you build

Before writing code for any non-trivial change, get explicit agreement on:

- **Data relationships.** 1:1, 1:N, or N:N? What is the canonical owner? Are joins through an association table?
- **State transitions.** What states exist? Which transitions are legal? What triggers each one? Are any transitions terminal?
- **Edge cases.** Empty states, null inputs, concurrent updates, partial failures, idempotency requirements.
- **Deletion behavior.** Soft delete or hard delete? CASCADE, RESTRICT, or SET NULL on foreign keys? What happens to dependent records?
- **Authorization.** Who can do this? On what resources? Is the check at the API layer, the database layer, or both?

When any of these are ambiguous, stop and ask the user. Do not guess and proceed.

## Update docs as you go

When a decision changes during implementation, update the relevant doc (glossary, ADR, README, schema notes) in the same PR. Stale documentation is worse than no documentation.
