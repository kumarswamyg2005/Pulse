# Issue tracker: Local Markdown

Specs and issues for this repo live as markdown files under `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec (PRD) is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first) — never a single combined tickets file
- Triage state is a `Status:` line near the top of each issue file
- Blocking edges are a `Blocked by:` line near the top
- Comments append to the bottom under a `## Comments` heading

Triage label vocabulary (defaults): `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.

Switch to GitHub Issues once the repo has a GitHub remote — re-run `/setup-matt-pocock-skills` to migrate the convention.
