# Working Rules

**Git safety.** Keep every step revertible. Commit a snapshot before any edit or
deletion, and commit again once a change is working. Never leave the tree in a
state I cannot roll back to.

**Search before designing.** Before proposing a solution, search for how it is
already done—GitHub repositories, issues, and documentation—and state the
industry-standard approach. Propose only after that search.

**Prefer the long-term fix.** When a durable solution and a minimal
stop-the-bleeding patch both work, take the durable one and state its cost. Use
a patch only when explicitly requested.

**Use Matt Pocock skills.** Whenever a mattpocock-skills skill applies to the
task (`tdd`, `diagnosing-bugs`, `grill-with-docs`, `to-spec`, `implement`, or
`code-review`), invoke it rather than working freehand.

## Agent skills

### Issue tracker

Issues are tracked as local Markdown files under `.scratch/`. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the default Matt Pocock triage-label vocabulary. See
`docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain documentation layout. See
`docs/agents/domain.md`.
