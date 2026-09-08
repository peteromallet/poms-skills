# Example: Hivemind delivery handover

User-provided example. These bindings, budgets, authorization, and baseline commits belong to this example; derive actual handovers from their own run configuration.

Implement the Hivemind knowledge-model plan using Megado.

Clone both repositories onto this machine:

```sh
git clone --branch hivemind https://github.com/banodoco/hivemind.git
git clone https://github.com/peteromallet/poms-skills.git
```

Read `poms-skills/megado/SKILL.md` and follow it. You can use it directly without installing it globally.

Then read `hivemind/docs/plans/knowledge-model-plan-20260908/START-HERE.md`.

That directory contains the North Star, plan, tasklist, acceptance criteria, run configuration, review contract, and current status. The project code is included in the same branch.

You are authorized to implement T1–T10 and run the configured tests and reviews. Activate run.yaml from planning_only to delivery as documented. Do not request another approval to begin.

Use the configured role slots:

- Coordinator: Luna medium
- Normal worker: Luna high
- XHARD worker/reviewer and oracle: Sol high
- Normal reviewer: Luna medium
- Final holistic reviewer: Astra medium

Review ceilings: 2 foundation reviews, 3 final reviews, and 3 separate oracle calls. These are ceilings, not quotas. Preserve counters and follow the artifact-based review contract.

First check repository state and establish the disposable database, pgvector, and Deno prerequisites. No implementation has been completed or certified yet.

Preserve the agreed simplifications: no media subsystem, compatibility shims, search redesign, or extra process. Production deployment, production database cutover, and live corpus writes remain outside scope.

Complete the implementation and validation, then provide the resulting changes, evidence, and any unresolved blockers.

Prepared baseline commits:

- Hivemind: `98adbb7c1196706dab7094693ab87c446d59419c`
- poms-skills: `99ba29dd9358d2e52cfe10a113c33624af4ebb44`
