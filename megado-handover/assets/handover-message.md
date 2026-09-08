# Copy-paste delivery message template

Implement [project objective] using Megado.

Clone both repositories into unused directories on this machine:

```sh
git clone --branch [project branch] [project repository URL] [project directory]
git clone [skills repository URL] poms-skills
git -C poms-skills checkout --detach [inspected skills SHA]
```

If a directory already exists, inspect it and preserve its work; do not overwrite it.
Read `poms-skills/megado/SKILL.md` ([pinned public skill URL]) and follow it.
You can use it directly without installing it globally.

Then read `[project directory]/[plan directory]/START-HERE.md`.
That directory contains the North Star, plan, tasklist, acceptance criteria,
run configuration, review contract, and current status. The project code is
included in the same branch.

You are authorized to [exact scope and finish]. [Delivery: activate run.yaml
from planning_only to delivery as documented; do not request approval already
granted. Planning-only: update planning documents only.]

Use the configured role slots: [summarize all seven bindings from run.yaml].
Review ceilings: [stages and remaining caps, including corrections/restarts].
Oracle ceiling: [separate remaining cap]. These are ceilings, not quotas.
Preserve [historical counts] and follow the artifact-based review contract.

First check repository state and establish [prerequisites]. Report missing
models or capabilities explicitly. Current implementation/evidence state:
[actual state, including missing evidence].

Preserve [accepted simplifications and non-goals]. [Explicit excluded actions].
Complete [authorized work and validation], then provide [finish artifacts,
evidence, and unresolved blockers].

Prepared baseline commits:

- [Project]: [exact source SHA and relationship to handover branch]
- poms-skills: [exact inspected SHA]
