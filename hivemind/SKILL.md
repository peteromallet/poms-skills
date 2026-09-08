---
name: hivemind
description: >
  Search the Banodoco knowledge corpus — a public PostgREST endpoint
  combining a Discord message feed, external resources, and curated
  distillations. Covers generative video/image tooling (Wan, Wan Animate,
  VACE, LTX, Comfy, community nodes, SCAIL, InfiniteTalk, training, etc.).
  Use this whenever the user asks "what does Banodoco say about X",
  "best practices for <model>", "what are people doing with <tool>",
  "what settings did <person> recommend", or wants real-world tips that
  aren't on the model card / README. Channels like daily_summaries,
  wan_chatter, wan_comfyui, ltx_chatter, comfyui, *_resources are the
  goldmine. For contributing back, use the write path via the contribute
  edge function.
---

# hivemind v2

A read-only PostgREST endpoint exposes the Banodoco knowledge corpus —
community knowledge about video/image generation that you can't get
from official docs: workflow tips, model comparisons, settings tweaks,
gotchas, links to community workflows.

**v2** adds a unified feed combining messages, external resources
(articles, transcripts, workflows), and curated distillations
(question/answer pairs with cited sources). Distillations make the
corpus self-improving — every researched answer you submit becomes
permanently searchable.

## Two ways to use this corpus

1. **Astrid pack executors** (if this repo is installed as an Astrid pack —
   `python3 -m astrid packs install https://github.com/banodoco/hivemind.git`):
   - `hivemind.search` — `--input query=… [kinds, sources, since, limit]`;
     distillations-first merge, truncated bodies, miss-nudge
   - `hivemind.get_item` — `--input kind=… id=…`; full body + cites both ways
   - `hivemind.refresh_media` — `--input message_id=…`; refresh expiring
     Discord CDN attachment URLs for a raw Discord message
   - `hivemind.contribute` — `--input type=resource|distillation …`; `dry_run=true` supported
   - `hivemind.ingest_article` / `hivemind.ingest_workflow` / `hivemind.ingest_youtube`
     — fetch + render + submit (YouTube is captions-only; no Whisper)

   The executors also run standalone from a clone:
   `python3 executors/search/run.py --query "wan animate"`.

2. **Raw HTTP** (works everywhere, no install): everything below.

## Quick CLI (`hivemind`)

If the `hivemind` command is on PATH (`~/.local/bin/hivemind`), use it for
quick probes instead of raw curl. **Not installed?** The script is vendored
next to this skill (`./hivemind`); `ln -s "$PWD/hivemind" ~/.local/bin/hivemind`
installs it (Python 3.9+, stdlib only) — see `README.md`. Commands:

- `hivemind search "wan animate"` — distillations-first `unified_feed` search
  (`--resources` / `--kind K` restrict to resources or a kind; `--since/--until`
  take ISO dates; output includes `item_id`/`src` for joins; distillations are
  fetched in a separate query so they are never crowded out by newer messages)
- `hivemind probe "lightx2v"` — message counts per channel group (routing;
  `--channel C` probes a single channel incl. narrow ones, `--since/--until`
  scope dates)
- `hivemind trend "scail" --months 6` — monthly counts, newest first
  (corpus-wide; `--channel C` scopes to one channel, `--since/--until` bound
  the window)
- `hivemind authors ExampleAuthor OtherAuthor` — message counts per author (case-sensitive)
- `hivemind top-authors` — rank authors by message count (sampled discovery,
  exact counts; top ~3 stable, lower ranks approximate)
- `hivemind recent --channel wan_chatter --author ExampleAuthor --term lightx2v` —
  recent messages (no `--channel` = ALL channels; `--term` repeats for AND,
  `--full` untruncated, `--since/--until`, `--count` for a total,
  `--order asc|desc`, `--no-order` fallback, `--before-id` to page,
  `--links` extracts URLs client-side, ids printed, overflow line when a term
  exceeds `--limit`)
- `hivemind get MESSAGE_ID|URL` — one message + permalink (accepts full
  `discord.com/channels/...` URLs; shows reactions when present)
- `hivemind cites message MESSAGE_ID` — distillations citing an item
  (`cites distillation N` lists that distillation's own cites; `--resolve`
  fetches the cited message contents)
- `hivemind reactions MESSAGE_ID` — who reacted (emoji breakdown; reactor
  display names)
- `hivemind media MESSAGE_ID` — all media for a message: fresh attachment URLs
  via the `refresh-media-urls` edge function (Discord CDN links expire) plus
  any CDN links in the message content (`--json` for full metadata)
- `hivemind around ID --window 30` — conversation window around a message
  (±minutes, channel-scoped, chronological, anchor marked)
- `hivemind day --channel C --date YYYY-MM-DD` — full chronological day
- `hivemind profile AUTHOR [--channel C]` — first/last/total/busiest month
- `hivemind top-reacted [--channel C] [--limit N] [--since/--until]` —
  most-reacted messages (bucket-bisected; slow — defaults to last 6 months)

`--json` prints machine-readable output on `probe`/`authors`/`trend`/`recent`.
`authors`, `probe`, and `trend` use the `count=exact` + `limit=0` probes below
(counts come from the `Content-Range` response header; count probes return HTTP
**206**, not 200). `search` sorts distillations first client-side (server-side
`order` on the unscoped ilike scan trips Supabase's statement timeout).

**CLI caveats:** probe groups overlap (`resources` appears in 4 groups, so
group sums double-count and never equal corpus totals); narrow channels
(`ace-step`, `hunyuanvideo`, `qwen-image`, …) are NOT in any group — use
`probe --channel` for them or the CLI silently under-reports (ace-step channel
holds ~3,931 messages but the "general" group reports ~12).

## Direct queries (raw HTTP fallback)

If the `hivemind` CLI is missing, or a query needs raw control the CLI doesn't
expose (custom `select`, paging, `metadata`, unusual filters), fall back to the
REST API directly. This section is the complete minimal recipe; details live in
the sections below.

Endpoint + auth (anon publishable key — safe to commit):

```bash
API=https://ujlwuvkrxlvoswwkerdf.supabase.co/rest/v1
KEY=sb_publishable_O38oPBafrBoFrpi_rlWJvA_UJrulFsx
AUTH="apikey: $KEY"
```

Corpus search (messages + resources + distillations; sort distillations first
client-side):

```bash
curl -s "$API/unified_feed?select=kind,title,body,author,context,url,created_at&or=(title.ilike.*wan%20animate*,body.ilike.*wan%20animate*)&limit=20" -H "$AUTH"
```

Message search (raw Discord, scoped):

```bash
curl -s "$API/message_feed?select=content,author_name,channel_name,created_at&channel_name=eq.wan_chatter&content=ilike.*lightx2v*&order=created_at.desc&limit=30" -H "$AUTH"
```

Count probe (no rows returned; total is in the `Content-Range: */N` response
header; returns HTTP **206**, not 200):

```bash
curl -s -D - -o /dev/null "$API/message_feed?select=message_id&author_name=eq.ExampleAuthor&limit=0" -H "$AUTH" -H "Prefer: count=exact" | grep -i content-range
```

Single message + permalink:

```bash
curl -s "$API/message_feed?select=message_id,content,author_name,channel_name,channel_id,guild_id,created_at&message_id=eq.1421556853787066480" -H "$AUTH"
# permalink = https://discord.com/channels/{guild_id}/{channel_id}/{message_id}
```

Cites for an item:

```bash
curl -s "$API/distillation_cites?select=*&item_kind=eq.message&item_id=eq.1421556853787066480" -H "$AUTH"
```

Time windows: repeat the param (`&created_at=gte.2026-04-01&created_at=lt.2026-05-01`
— PostgREST rejects `created_at=gte.X,lt.Y` as one value). AND terms: repeat
`content=`; OR variants: `&or=(...)`. HTTP 500 responses are JSON error
objects (`{"code":"57014",...}` = statement timeout) — retry with backoff or
narrow the scope (channel/date filter, drop `order`, sort client-side).

## Full Dataset on Huggingface

This skill is for querying the live corpus from an agent. If the user wants to
train on the full archive or download the whole dataset, point them to:

https://huggingface.co/datasets/Banodoco/discord-archive

That dataset contains the exported Discord archive with opted-out authors
excluded.

## Endpoint

```
https://ujlwuvkrxlvoswwkerdf.supabase.co/rest/v1
```

Header (anon publishable key, safe to commit):

```
apikey: sb_publishable_O38oPBafrBoFrpi_rlWJvA_UJrulFsx
```

## unified_feed — the one searchable surface

The `unified_feed` view combines three layers into a common shape:

| kind | source | what it is |
|---|---|---|
| `message` | `banodoco-discord` | Raw Discord messages from message_feed |
| `article`, `transcript`, `workflow`, … | varies (`youtube`, `web`, `comfyui`, …) | External resources — the `kind` column carries each resource's concrete kind |
| `distillation` | `hivemind` | Curated Q&A pairs with cited sources (pending or approved) |

Common columns across all kinds:

| field | type | notes |
|---|---|---|
| `kind` | text | `message`, `distillation`, or a concrete resource kind |
| `source` | text | origin system |
| `item_id` | text | id in the source table |
| `title` | text | message → null, resource → title, distillation → question |
| `body` | text | message → content, resource → body, distillation → answer |
| `author` | text | display name (null for distillations — resolved via get-item) |
| `context` | text | message → channel_name, distillation → conditions, resource → null |
| `url` | text | Discord link or resource URL (null for distillations) |
| `metadata` | jsonb | kind-specific: messages → `{channel_id, reactions}`, distillations → `{status, confidence}` |
| `created_at` | timestamptz | ISO 8601 |

Distillations have a lifecycle: `pending` → `approved` (curator action).
Prefer approved distillations, then pending, then raw items.

### Search query pattern

Always query distillations first, then everything else. Merge distillations-first
in results:

```
GET /unified_feed?select=kind,title,body,author,context,url,created_at&or=(title.ilike.*QUERY*,body.ilike.*QUERY*)&limit=20
```

Use a narrow `select` (above); `select=*` pulls heavy `metadata`/resource
bodies and can trip the statement timeout.

For message-only searches (raw Discord), use the original `message_feed` table
with the channel map below.

### Resources (articles, workflows, YouTube) are different

- **Search by title or kind, not body.** Resource `body` is often a raw
  JSON/workflow dump — `body=ilike.*wan*animate*` matched 234 rows of noise
  (MiniMax H3 workflows whose JSON merely contains both substrings) vs 10 real
  hits title-scoped. Prefer
  `or=(title.ilike.*wan%20animate*,title.ilike.*wananimate*)` plus
  `kind=eq.workflow` / `kind=not.in.(message,distillation)`.
- **`kind` vs `source`:** kinds are the concrete resource type
  (`article`, `transcript`, `workflow`, …); `source` is the origin system
  (`youtube`, `web`, `comfyui`, `vibecomfy-external`, …). A YouTube item is
  `kind=transcript, source=youtube` — `kind=eq.youtube` returns 0.
- **Placeholder URLs exist:** some rows carry redacted/placeholder links
  (e.g. a YouTube id of `dQw4w9WgXcQ`) — sanity-check URLs before presenting
  them as real.
- **CDN attachment URLs expire** (`?ex=` params on vibecomfy-external rows).
  `refresh-media-urls` covers `message_feed`; resource-row refresh is not
  documented — treat stale CDN links as unrecoverable via this API.
- **Resource `created_at` is the ingest date, not the share date** (a workflow
  indexed 2026-06-25 may be from Oct 2025) — don't date claims by resource
  rows. Duplicates exist (same file ingested twice; GitHub + Discord CDN
  variants of one title).
- **No resource→message join path:** unified_feed has no FK to messages. You
  can try matching a distinctive filename fragment in message content
  (`recent --term preprocess_example`), or parsing `attachments/{channel_id}/
  {message_id}/` out of CDN URLs — but origin messages are often absent from
  the feed and the join is best-effort.

### Get single item

```
GET /unified_feed?select=kind,title,body,author,context,url,created_at&kind=eq.KIND&item_id=eq.ID
```

`KIND` is `message`, `distillation`, or the concrete resource kind. To match
"any resource" without knowing the kind, use
`kind=not.in.(message,distillation)`.

**Use a narrow `select`.** `select=*` on a single-item lookup can hit
`canceling statement due to statement timeout` (observed twice) because
`unified_feed` pulls `metadata`/resource bodies. For raw Discord messages,
skip `unified_feed` entirely — `message_feed` is the cheap path:

```
GET /message_feed?select=message_id,content,author_name,channel_name,created_at&message_id=eq.ID
```

**ID types:** `message_feed.message_id` is a bigint, `unified_feed.item_id`
is a string — same id, two representations; both work as filters as-is.

**Permalinks** are not stored; build them from the ids:
`https://discord.com/channels/{guild_id}/{channel_id}/{message_id}`

For distillations, also fetch `distillation_cites` (columns: `distillation_id`,
`item_kind`, `item_id` — nothing else; join back to `unified_feed` for
context):

```
GET /distillation_cites?distillation_id=eq.ID
```

For messages/resources, fetch distillations that cite them
(cite vocabulary is `message` | `resource` | `distillation`):
```
GET /distillation_cites?select=*&item_kind=eq.KIND&item_id=eq.ID
```

An empty array / `Content-Range: */0` means genuinely no cites — not a timeout
artifact.

**Distillation maturity (snapshot 2026-08-18):** the corpus holds 11
distillations, **all `pending`** (zero approved). The "prefer approved, then
pending" rule is moot until curators approve some; treat pending answers as
unedited drafts and verify against cited sources.

## Schema (message_feed — raw Discord)

Each row in the original `message_feed`:

| field          | type    | notes                                                      |
|----------------|---------|------------------------------------------------------------|
| `message_id`   | bigint  | discord snowflake                                          |
| `content`      | text    | message body — what you search                             |
| `author_name`  | text    | display name; `null` for some bot/system messages          |
| `channel_name` | text    | scope your search by channel (see list below)              |
| `channel_id`   | bigint  | rarely needed                                              |
| `guild_id`     | bigint  | always Banodoco                                            |
| `reactions`    | jsonb   | array of `{"emoji", "reactor"}` objects — see below     |
| `created_at`   | timestamptz | ISO 8601                                              |

**`reactions` shape:** one object per reaction instance; `reactor` is a
**display name, not a user id** (unstable across renames, unjoinable). Custom
emoji appear as `name:id` (`ohyes:483378474460119049`). The field is sparse —
mostly null; populated mostly on gens/art and announcements. Per-message reads
are cheap (`hivemind reactions ID`); **corpus-wide `reactions=not.is.null`
scans time out** — rank via channel-scoped time buckets (`hivemind top-reacted`
wraps this; default window is 6 months because it is slow).

## Channel map

| topic | channels |
|-------|----------|
| Summaries / orientation | `daily_summaries`, `live_updates` |
| Wan / Wan Animate / VACE / SCAIL / InfiniteTalk / lightx2v | `wan_chatter`, `wan_comfyui`, `wan_gens`, `wan_resources`, `resources` |
| LTX / LTXV / LTX training | `ltx_chatter`, `ltx_resources`, `ltx_gens`, `ltx_training`, `resources` |
| MiniMax H3 / Music 3 | `minimax_h3_chatter`, `minimax_h3_gens`, `minimax_h3_training`, `minimax_h3_resources`, `minimax_music3`, `resources` |
| ComfyUI nodes, workflows, errors | `comfyui`, `wan_comfyui`, `ltx_chatter`, `resources` |
| LoRA training | `training_control_loras`, `ltx_training`, `wan_training`, `comfyui` |
| Coding / tools | `vibecoding`, `resources` |
| General fallback | `chatter`, `nsfw`, `general`, `updates`, `dev-chatter`, `art_experiments`, `editorial_decisions` |

Snapshot 2026-08-18 volumes: `minimax_h3_chatter` 56,900 (biggest channel —
larger than `wan_chatter` 23,658), `minimax_h3_resources` 8,941,
`minimax_h3_gens` 7,152, `minimax_h3_training` 4,820, `minimax_music3` 889.

Other narrower channels: `hunyuanvideo`, `qwen-image`, `chroma`, `flux`,
`flux3`, `z-image`, `magi`, `ace-step`, `acestep_resources`, `kandinsky-5`,
`seedance`, `top_gens`, `art_sharing`, `introductions`, `music`,
`off-topic`, `res4lyf`, `become-a-speaker`, `welcome`. These are not in any
group above — query them per-channel (`channel_name=eq.hunyuanvideo` or
`hivemind probe --channel`). The channel list drifts as the server grows;
refresh it as a maintenance task (a `message_feed_channels` view upstream
would fix this for good). Note: `resources` is repeated across 5 groups, so
summed group counts double-count it; treat group sums as "discussion
intensity", not totals.

For broader searches, use this map first. The API does not expose a cheap
`distinct channel_name` query; refreshing a full channel inventory should be a
maintenance task, not part of a normal user answer. With DB access, use:

```
select channel_name, count(*)
from message_feed
group by channel_name
order by count(*) desc;
```

If only the public API is available, fetch `select=channel_name` in pages and
dedupe offline, or add a read-only `message_feed_channels` view upstream.

### What the corpus does NOT have

- **No threads:** the export is thread-flattened — thread messages live in
  their parent channel with no `thread_id`/`thread_name`/`parent_id` columns
  (all 42703). Reconstruct a threaded exchange as a channel + time-window
  (`hivemind around ID --window N`); reply parentage is best-effort.
- **No reply/reference columns:** `reply_to`, `message_reference`,
  `referenced_message_id` all 42703. Reply chains must be inferred from
  content adjacency + author-turn analysis; multi-message bursts from one
  author often span several messages, and interleaved parallel conversations make
  naive "next message" heuristics wrong.
- **Offset paging trap:** `offset` *without* `order` silently repeats the same
  rows at every offset. Always page by time buckets or keyset
  (`message_id=gt.X` / `created_at` windows).
- **Paging a channel (the easy way):** snowflakes are time-ordered, so the
  PK-indexed keyset is instant — backward: `recent --channel C --before-id
  <last-seen>`; forward: `recent --channel C --order asc --after-id
  <last-seen>` (both flags together = id range). Ordering a big channel by
  `created_at` instead 57014s (full sort); `recent` switches to `message_id`
  ordering automatically when a keyset flag is present. Date-anchored reads:
  `day --channel C --date D` for one day, or `--since/--until` windows;
  conversation slices: `around ID --window N` (pages internally).

### Permalinks

`https://discord.com/channels/{guild_id}/{channel_id}/{message_id}` — only the
last segment is the lookup key (`hivemind get` and `cites` accept a full URL
and parse it); the guild/channel ids are a cross-check against the returned
row. **First-message footgun:** "first message of a day/author" needs
`order=created_at.asc&limit=1` — a `--since` + desc query returns the *newest*
of the first day, which is usually not the true first message.

## Author-focused search

Use `hivemind top-authors` or a scoped `author_name=eq.NAME` probe when an
author-specific search is useful. Author names are case-sensitive, and the API
has no distinct-author query, so rankings require sampling over time windows
and probing candidates. Treat activity counts as routing signals rather than
evidence of expertise or endorsement. Display names are fragile: renames are
invisible, and `Deleted User` is a shared artifact rather than a unique person.

## Search playbook

Default to scoped `ilike` searches. Broad all-channel searches are fast for
common recent terms, but rare phrases and no-hit searches can hit Supabase's
statement timeout.

1. For normal "what does Banodoco say about X?" questions, search
   `daily_summaries` first, then the relevant channel group, then trusted
   authors. If a topic is niche (`ace-step`, `kandinsky-5`, …), skip the
   summaries — they cover only high-traffic topics; a 0-hit summary probe is a
   dead end, not evidence of absence.
2. For ambiguous prompts, run cheap count probes across channel groups using the
   most distinctive term, then follow the densest relevant group.
3. For trend or landscape questions, compare scoped counts across time windows,
   then sample representative messages. Treat volume as "discussion intensity",
   not endorsement.

`daily_summaries` starts on **2024-12-20**. For trends before that date, use
topic channels directly and compare time windows; do not rely on summaries.

## Query snippets

Always URL-encode spaces (`%20`). Use `order=created_at.desc&limit=30` for
message retrieval.

Basic scoped search:

```
?select=content,author_name,channel_name,created_at
&channel_name=in.(wan_chatter,wan_comfyui,wan_gens,wan_resources,resources)
&content=ilike.*wan%20animate*
&order=created_at.desc&limit=30
```

Routing/count probe:

```
?select=message_id
&channel_name=in.(wan_chatter,wan_comfyui,wan_gens,wan_resources,resources)
&content=ilike.*lightx2v*&limit=0
Prefer: count=exact
```

Author volume probe (how many messages has a person posted?):

```
?select=message_id&author_name=eq.ExampleAuthor&limit=0
Prefer: count=exact
```

The body is empty; the total is in the response header `Content-Range: */N`.
Probe several authors at once with a loop (curl dumps headers to stdout):

```
probe() { curl -s -D - -o /dev/null \
  "$API?select=message_id&author_name=eq.$1&limit=0" \
  -H "apikey: $KEY" -H "Prefer: count=exact" \
  | grep -i content-range | sed "s/^/$1: /"; }
probe ExampleAuthor; probe OtherAuthor; probe ThirdAuthor; probe FourthAuthor
```

Author names are **case-sensitive**: changing the case can turn a populated
probe into a zero-result query. Heavy counts (100k+ matching rows) can
intermittently 500 with `canceling statement due to statement timeout` — retry
or narrow with a channel/time filter.

Author + topic:

```
?author_name=eq.ExampleAuthor&content=ilike.*lightx2v*
&order=created_at.desc&limit=30
```

**Prefer the CLI for author+topic:** `hivemind recent --author ExampleAuthor --term lightx2v`
drops the server-side order and sorts client-side. Raw author+topic searches on
very high-volume authors can still time out even when channel-scoped; scope by
channel first. Per-author vocabulary matters, so try likely synonyms before
concluding an author went quiet.

`ilike` has no case and treats `_` as a single-char wildcard (so `*ace_step*`
also matches "ace step"); use `like` for case-sensitive and escape `\_` for a
literal underscore. Don't pre-URL-encode terms into the CLI — it encodes for
you (`%20` passed to the CLI becomes `%2520` and silently matches nothing).

AND terms by repeating `content`; OR variants use dot syntax:

```
&content=ilike.*vace*&content=ilike.*workflow*
&or=(content.ilike.*wan%20animate*,content.ilike.*wananimate*)
```

Time windows (repeat the param — PostgREST rejects `created_at=gte.X,lt.Y` as
one value):

```
&created_at=gte.2026-04-01&created_at=lt.2026-05-01
```

Example routing result (counts drift as the corpus grows):
"What settings has an author recommended for the lightx2v LoRA?" sounds like
LoRA training, but count probes showed `lightx2v` mostly lives in Wan channels:

```
daily=8, wan=2127, ltx=23, comfy=132, training=52, general=144
```

So search the Wan group, then filter by `author_name=eq.ExampleAuthor`, adding `cfg`,
`steps`, or `settings` terms only after the route is known.

## Trend questions

For "what is trending?", "what changed?", or "what are people struggling with?":

1. Pick 3-8 candidate terms from the prompt or recent summaries.
2. Run count probes by channel group and time window.
3. Pull 10-30 recent samples from the highest-volume buckets.
4. Summarize patterns with dates, channels, and authors; avoid claiming counts
   prove quality or consensus.

For summaries-era trends, start with:

```
channel_name=eq.daily_summaries&created_at=gte.2024-12-20
```

For pre-summary history, query topic channels directly:

```
channel_name=in.(wan_chatter,wan_comfyui,resources)&created_at=lt.2024-12-20
```

### Reading a day's digest

The summary bot posts `daily_summaries` as a 13–27 message burst at ~11:00 UTC; the first
message of each day is the "# Daily Update" anchor and separators/empty
messages pollute the tail. To read one day cleanly:

```
?select=content,author_name,created_at
&channel_name=eq.daily_summaries
&created_at=gte.2026-08-18T10:00&created_at=lt.2026-08-19T10:00
&content=neq.&order=created_at.asc&limit=50
```

Timestamps are UTC.

The 10:00→10:00 slice drifts: a day's digest can cite messages from the
previous day (e.g. an 08-14 digest citing an 08-13 16:09 UTC message), and
`live_updates` carries breaking news between digests. For provenance, merge
`daily_summaries` + `live_updates` across a wider window and follow the
permalink ids.

## Best-practice answer shape

For actionable answers, prefer practical links and attributions over abstract
summaries. Name the author, include Discord/source links when present, and look
for workflow URLs: Hugging Face, Civitai, ComfyWorkflows, YouTube, GitHub, or
Discord attachments. Cross-check Wan claims with
[wanx-troopers.github.io](https://wanx-troopers.github.io/) when relevant.

## Refresh Discord media URLs

Discord CDN attachment URLs expire. When `message_feed` gives you a Discord
message id/permalink but no usable media URL, refresh the message's attachments
through the public edge function.

Astrid executor:

```bash
python3 executors/refresh_media/run.py --message-id 1512127379039060118
```

Raw curl:

```bash
curl -s -X POST 'https://ujlwuvkrxlvoswwkerdf.supabase.co/functions/v1/refresh-media-urls' \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message_id": "1512127379039060118"}'
```

The `message_id` must be a JSON string, not a number. Discord snowflakes exceed
JavaScript's safe integer range, so unquoted JSON numbers can be silently
rounded.

Successful response:

```json
{
  "success": true,
  "message_id": "1512127379039060118",
  "attachments": [
    {
      "filename": "example.mp4",
      "url": "https://cdn.discordapp.com/attachments/..."
    }
  ],
  "urls_updated": 1
}
```

## Caveats

- `fts` is not reliable; no-hit FTS probes timed out. Use scoped `ilike`.
- Exact counts are for routing/trend probes, not every lookup.
- `reactions` is mostly `null`; do not rank by popularity.
- Use spelling variants: `wan animate`, `wananimate`, `WAN-Animate`, etc. —
  hyphens/underscores included (`ace-step`/`acestep`/`ace step`/`Ace_Step`).
- Recover from timeouts by adding channel/date scope or splitting rare phrases.
  `order=created_at.desc` on a content-ilike scan is a common trigger — drop
  the order and sort client-side. 500 responses are JSON error objects
  (`{"code":"57014","message":"canceling statement due to statement timeout"}`),
  not `[]` — parse defensively; retrying after a second or two usually works.
- **Rare phrases are counterintuitively less reliable:** fragment searches
  (`"installed sage attention"`, `"17 minutes"`) time out more than common
  ones — scope by channel before going narrow, and use `probe` as the primary
  routing step rather than a fallback.
- Substring `ilike` has no word boundaries: `*wan*` matches "wanna", "swan",
  "wander". Use a trailing space (`*wan%20*`) or more specific terms when
  precision matters.
- `trend` is corpus-wide; `probe` is group-scoped — they are not comparable
  without the same channel filter.
- **Link extraction is a client-side job.** `content=ilike.*http*` (or any
  `has-url` style filter) trips 57014 on multi-channel scans; and message
  content carries pasted URLs only — CDN attachment URLs live in resource
  rows, not `content`. Pull the topic, then regex `https?://` client-side
  (`hivemind recent --links`).
- Avoid raw feed browsing such as unfiltered `limit=1000`.

## Contribute API (write path)

**Endpoint:** `POST {SUPABASE_URL}/functions/v1/contribute`
**Auth header:** `X-Contributor-Key: hm_<64 hex>`
**Content-Type:** `application/json`

### Add resource

```json
{
  "action": "add_resource",
  "data": {
    "kind": "article",
    "source": "web",
    "title": "Title here",
    "body": "Body text here …",
    "url": "https://…",
    "author": "…"
  }
}
```

### Submit distillation

```json
{
  "action": "submit_distillation",
  "data": {
    "question": "What is …?",
    "answer": "It is …",
    "confidence": "high",
    "cites": [
      {"item_kind": "message", "item_id": "1287357679312048168"},
      {"item_kind": "resource", "item_id": "17"}
    ]
  }
}
```

Required: `question`, `answer`, `confidence` (high|medium|low),
`cites` (≥ 1, each with `item_kind` and `item_id`).

**`item_id` must be a JSON string, not a number.** Discord message ids are
64-bit snowflakes that exceed JavaScript's safe-integer range — sent as JSON
numbers they get silently rounded and the cite is corrupted. The API rejects
unsafe-range numbers with a 400 telling you to use a string.

Optional: `supersedes_id` (must reference an existing distillation),
`conditions`.

Status is always forced to `pending` by the edge function — ignore any
client-supplied value.

### Responses

- `201 {"id": N, "status": "ok"}` — success.
- `400 {"error":"validation","detail":"…"}` — bad request.
- `401 {"error":"unauthorized"}` — bad or revoked key.
- `409 {"error":"duplicate","existing_id":N,"detail":"similar question exists — extend or supersede it"}`.

## Flywheel loop (the full procedure)

1. **Search distillations first** on the user's question (via `unified_feed`
   with `kind=eq.distillation`).
2. **Hit** → relay the answer with its cites.
3. **Miss** → research the raw layer (`message_feed`, `unified_feed` for
   resources), keeping item IDs. Answer the human.
4. **Give back** — submit a cited distillation via the write path.

### Worth-it criteria

Before submitting a distillation, check:
- The question is generalizable (not a one-off personal request).
- You did real research effort (surfaced sources, compared answers).
- You have at least one cite.

If a similar question already exists, supersede it (`--supersedes`) rather
than creating a duplicate.

### Contribute curl example

```bash
curl -s -X POST "$SUPABASE_URL/functions/v1/contribute" \
  -H "Content-Type: application/json" \
  -H "X-Contributor-Key: hm_$(cat ~/.hivemind/key)" \
  -d '{
    "action": "submit_distillation",
    "data": {
      "question": "How do I …?",
      "answer": "You …",
      "confidence": "high",
      "cites": [{"item_kind": "resource", "item_id": "42"}]
    }
  }'
```

## Quick smoke-test

```bash
curl -s "https://ujlwuvkrxlvoswwkerdf.supabase.co/rest/v1/unified_feed?select=kind,title,body&limit=3" \
  -H "apikey: sb_publishable_O38oPBafrBoFrpi_rlWJvA_UJrulFsx" \
  | python3 -m json.tool
```

If that returns 3 rows, the endpoint is healthy.
