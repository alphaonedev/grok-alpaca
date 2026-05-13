# NHI Prompts

The [`prompts/`](../prompts/) directory contains 18 ready-to-paste prompts for Claude Code CLI. Each one builds one feature with clear acceptance criteria. They're meant to be run in order against a fresh checkout.

See [`prompts/README.md`](../prompts/README.md) for the index.

## When to add a new prompt

You're extending the project. A new feature touches more than one file or requires a non-trivial decision. The natural shape is "one prompt, one feature."

## Writing prompts that work cold

Claude Code starts each session without memory of prior runs. A prompt that works cold has:

1. **Role + goal** in 1–2 sentences at the top.
2. **Tasks** as a numbered list, naming exact file paths.
3. **Constraints** the model must respect (read-only? localhost? no extra deps?).
4. **Acceptance** — concrete commands or checks that prove the work is done.

What does NOT belong:
- References to "as we discussed" or "like last time"
- TODOs for things the prompt should actually do itself
- Multi-feature scopes — split them

## Example

The smallest good prompt looks like:

```markdown
# Prompt N — <one-line title>

## Goal
<2-3 sentences on what's being built and why>

## Tasks
1. <file path>: <what to add>
2. <file path>: <what to change>
3. Tests: <where and what to assert>

## Constraints
- <constraint>
- <constraint>

## Acceptance
- `<command>` exits 0
- `<curl / browser action>` shows <expected>
```

## Tips

- Prefer **acceptance criteria you can run from the shell** over "make sure it looks right."
- When extending: invoke the right Anthropic skill in the goal section (e.g., "Use the `frontend-design` skill for the layout").
- After each prompt completes, commit. Easier to revert one prompt's work than untangle two.
