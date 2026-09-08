# hivemind — Banodoco knowledge corpus skill + CLI

Read-only search over the Banodoco Discord archive (generative video/image
tooling community): raw messages, external resources (articles/workflows/
YouTube), and curated distillations. Two layers:

- **`SKILL.md`** — the agent-facing skill: full REST API reference, query
  patterns, channel map, caveats.
- **`hivemind`** — a dependency-free CLI wrapper for quick human/agent use.

## Requirements

- Python 3.9+ (stdlib only — no pip installs)
- `~/.local/bin` on `PATH` (or any bin dir of your choice)

## Install

```bash
# from this directory (the skill repo)
ln -s "$PWD/hivemind" ~/.local/bin/hivemind
# or copy if you don't want a symlink:
# cp hivemind ~/.local/bin/hivemind && chmod +x ~/.local/bin/hivemind
```

Verify:

```bash
hivemind --help
hivemind recent --channel wan_chatter --limit 3
```

## Commands

```
hivemind "QUERY"            distillations-first corpus search
hivemind search "QUERY"     [--resources] [--kind K] [--since D] [--until D]
hivemind probe "TERM"       counts per channel group  [--channel C] [--since/--until] [--json]
hivemind trend "TERM"       monthly counts, newest first  [--months N] [--channel C] [--json]
hivemind authors NAME...    per-author message counts (case-sensitive!)  [--json]
hivemind top-authors        rank authors by message count  [--limit N]
hivemind recent             recent messages; no --channel = ALL channels
      [--channel C] [--author A] [--term T ...] [--since/--until] [--limit N]
      [--full] [--count] [--order asc|desc] [--no-order] [--before-id ID]
      [--after-id ID] [--links] [--json]
hivemind around ID          conversation window around a message  [--window M]
hivemind day --channel C --date YYYY-MM-DD   full chronological day
hivemind profile AUTHOR     first/last/total/busiest month  [--channel C]
hivemind reactions ID       who reacted (emoji breakdown)
hivemind media ID           all media for a message (refreshed via the
                            refresh-media-urls edge function)  [--json]
hivemind top-reacted        most-reacted messages (bucket-bisected; slow)  [--limit N]
hivemind get ID|URL         one message + permalink (accepts full discord.com URLs)
hivemind cites KIND ID      distillations citing an item  [--resolve] [--json]
```

## Notes

- **Read-only** by default. The only POST the CLI makes is
  `hivemind media ID`, which calls the public `refresh-media-urls` edge
  function to re-issue expiring Discord CDN attachment URLs.
- The API key is the Supabase anon publishable key, embedded in the script —
  safe to commit and share.
- Author names are case-sensitive (`ExampleAuthor` ≠ `exampleauthor`); threads and reply
  references do not exist in the export (flattened); unscoped ordered scans on
  big channels can hit statement timeouts — see `SKILL.md` for the recovery
  playbook.
- Endpoint reference: `https://ujlwuvkrxlvoswwkerdf.supabase.co/rest/v1` —
  full query docs in `SKILL.md`.

## Contribute back

The corpus has a write path (submit resources/distillations via the
`contribute` edge function) — see `SKILL.md` → "Contribute API".
