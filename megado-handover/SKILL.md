---
name: megado-handover
description: Prepare a portable Megado project handover for another machine or agent, including selected artifacts, dependency provenance, publication checks, and a copy-paste delivery message.
---

# Megado handover

Use this skill when a user asks to move a Megado plan and project to another
machine or agent. It publishes evidence and instructions directly to a Git branch; it does not execute
the product plan. Read the canonical Megado skill first: normally
`../megado/SKILL.md` in this checkout, otherwise the source path supplied by
the user. Read its referenced run and review documents directly as needed.

## Establish the handover contract

Record the authoritative project path, selected worktree or ref, run directory,
recipient, desired receiving mode (`planning_only` or `delivery`), destination
remote, base branch, and publication visibility. For this workflow, default
publication visibility is public unless the latest explicit user instruction
changes it; still record the destination. Treat that instruction as authority.
Preserve prior decisions, role assignments, budgets,
states, and historical counters; apply only a later explicit override. Do not
invent model defaults or duplicate them outside `run.yaml`.

Inspect `git status`, `HEAD`, branches, remotes, worktrees, and the selected
run. Establish whether origin is stale relative to the latest committed
project. Select and record the exact source SHA. If dirty files are included,
name them and why; preserve intentionally included source while excluding
unrelated dirt, secrets, and private notes. Never silently turn an uncommitted
working tree into the authoritative source.

## Publish ordinary files in Git

Use the repository branch as the handover. Do not create ZIP files, tarballs,
archive bundles, or a separate distribution package unless the user explicitly
requests one. Commit the necessary source and ordinary Markdown/configuration
files, push the branch to GitHub, and provide a short continuation instruction
linking to the committed handover message.

Select the necessary current planning documents outside ignored `.otto` storage:
START-HERE and the linked plan, criteria, objective, goal, status, `run.yaml`,
authorization, scope, decision, acceptance, and provenance records. Reuse
tracked project docs and include an ignored or untracked file only when it is
the intentional authoritative source. Follow links until the recipient can
start without the original absolute paths. Do not wholesale-copy logs,
archives, raw receipts, or machine-local caches. Label planning records as
planning evidence; they are not proof that product implementation or tests ran.
Keep historical exploration and counters distinct from the current state.

Document Megado dependencies with fetchable URLs the recipient can access and
exact commits or tags. The handover must state the SHA actually inspected,
provide a no-overwrite install command, and provide a direct-read fallback.
Check that native agent capability and every required model are available;
report a
missing capability or model explicitly, with no silent substitution.

## Audit and publish safely

Audit every intended published file and reachable history for credentials,
private operational details, unnecessary personal data, watchlists, and
internal paths. A publishable key in intended configuration is not proof of
authentication. Remove an item from the publication set or sanitize it with
authority; do not rewrite history automatically. Publish only to the
authorized destination and visibility.

When publication is authorized, create or use a branch from the recorded
source, stage only explicit selected paths, commit, push normally with no
force, and verify the remote ref resolves to the local commit. Preserve other
worktrees and unrelated changes. Report omitted files and any unresolved risk.

The preparer publishes only the authorized handover branch and its artifacts.
When the user's delivery authorization includes a PR finish, the receiving
agent creates the implementation branch and PR after implementation and the
required validation, then returns its URL with outcome evidence and unresolved
risks. Record the target remote and base branch. Never infer permission to
merge, deploy, or cut over from a handover; generic planning-only or handover
authorization does not grant a PR.

## Validate the recipient path

Use a fresh checkout or an equivalent clean path to verify clone/ref commands,
portable links, dependency installation or direct-read fallback, `run.yaml`
parsing, role/model references, prerequisites, and review-packet inputs that
actually exist. Do not manufacture product tests or claim a model packet from a
plan record; a missing packet can be created from the real candidate later.
For `planning_only`, deliver the artifact and message without executing the
product plan. For `delivery`, the recipient changes the accepted mode in the
single authoritative `run.yaml` while preserving roles, stages, budgets,
counters, and boundaries, then executes only what the authorization covers.
Unknown prerequisites are reported for resolution; they are not approval
gates invented by this skill.

Perform a bounded independent portability check when worthwhile or requested,
proportionate to the handover. Do not add mandatory two-panel audits, extra
review gates, or hide the actual product review count. Always deliver both the
durable artifact and the copy-paste message in `assets/handover-message.md`.
The message must name
the exact project and skills SHAs, current phase/state, authority, objective,
boundaries, stages and budgets from `run.yaml`, prerequisites, start commands,
and the selected finish instruction.

## Write a self-contained continuation message

Assume the receiving agent knows nothing about this conversation or Megado.
Follow [the Hivemind example](examples/hivemind-delivery.md) and adapt
[the message template](assets/handover-message.md) to the actual project.
Include both repository URLs and clone commands, an explicit link/path to
`poms-skills/megado/SKILL.md`, and say it can be read directly without global
installation. Include the plan entrypoint, authority, role bindings, remaining
review/oracle ceilings, prerequisites, non-goals, finish instruction, and exact
prepared baseline commits. Summaries of bindings and caps must match the
run's authoritative `run.yaml`; never import the example's project settings.
Return the self-contained message to the user, not merely a link to it.
