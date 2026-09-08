# Poms skills

Reusable skills for Codex-compatible agent work, including Hivemind and Megado.
Each skill is self-contained under its own directory and is usable from a
checkout without installing Python dependencies unless that skill says
otherwise.

## Install Megado on another machine

Clone the repository into a user-owned data directory:

```sh
git clone https://github.com/peteromallet/poms-skills.git ~/.local/share/poms-skills
```

Expose the Megado skill to Codex only when that path is not already occupied:

```sh
mkdir -p ~/.codex/skills
if [ -e ~/.codex/skills/megado ] || [ -L ~/.codex/skills/megado ]; then
  echo "~/.codex/skills/megado already exists; inspect it before changing it"
else
  ln -s ~/.local/share/poms-skills/megado ~/.codex/skills/megado
fi
```

The Megado skill includes its references, review-packet template, run template,
and helper scripts in the same checkout. A run should read `megado/SKILL.md`
and the referenced files from that checkout before planning or execution.

To update a checkout later:

```sh
git -C ~/.local/share/poms-skills pull --ff-only
```

The Hivemind skill is under `hivemind/`. It uses the public corpus read path
and documents its own runtime credentials and write-path requirements.

## Layout

- `megado/` — planning, delegation, review, execution, and handoff guidance
- `megado-handover/` — portable remote-machine handovers and delivery messages
- `hivemind/` — Hivemind search skill and dependency-free CLI
- other directories — reusable task-specific skills

Symlinked directories from the local workstation are intentionally not included;
they remain external source checkouts and are not part of this repository.
