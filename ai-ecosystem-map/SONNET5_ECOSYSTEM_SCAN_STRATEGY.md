# SONNET5_ECOSYSTEM_SCAN_STRATEGY.md — the per-session execution ritual

This is the execution script every scan session follows. It is sized to a
single Sonnet 5 context window. One session = one SCAN_TREE candidate = one
commit. Bootstrap prompt for a fresh session:

> Work in /home/user/lastmanupinc-hub/ai-ecosystem-map. Read begin.yaml and
> continue the loop.

## Doctrine (do not reinterpret)

**Peer-independence** (owner verbatim, 2026-08-16): "We are checking to see if
what we built in house is aligned with these as peers. Not our ability to use
them, our ability to never need them. A score of 0% peer is not only
acceptable but it's expected. Initial discovery is more important that we are
honest than blindly optimistic. So we can build on truth."

- Using a vendor tool = **dependence** → record in `vendor_in_use`. It NEVER
  raises a grade.
- Default is `absent` (with recorded search_expressions). When in doubt,
  grade DOWN and say why in the evidence note.
- Grade ladder: a grep hit line alone is `scaffold` at best. A working
  implementation you actually opened and read is `partial` or `bench`.
  `peer` requires demonstrated end-to-end equivalence: real code PLUS tests,
  a verifier, or a wired production call site — all cited by path.

## The ritual (numbered; do them in order)

1. **Bootstrap.** Read `begin.yaml` → `continuation.yaml#automated_loop_state`
   → take `next_candidate_id` → read that candidate's block in
   `SCAN_TREE.yaml`. Do not ask permission; the loop is the permission.
2. **Load targets.** Read `ECOSYSTEM_TARGETS.yaml` in full (compact by
   design). From the matrix, read only rows whose grade is below `peer`
   (settled rows are the consolidation session's business, not yours).
3. **Per repo in the batch — orientation (cheap).** `ls` the top level; read
   README / CLAUDE.md / ARCHITECTURE.md headers only (≤120 lines each).
   Write a one-sentence repo purpose into the evidence shard.
4. **Per repo — the 11 category batteries.** Run from the repo root with
   `grep -rniE --binary-files=without-match` and exclusions
   `--exclude-dir={.git,node_modules,third_party,archive,_archive,dist,build,vendor}`
   (plus `*.min.*`, lockfiles). One battery per category:

   | Category | Battery (core regex) |
   |---|---|
   | LLM | `language.?model|inference|tokenizer|logits|sampling|completion|transformer` |
   | Agentic AI | `multi.?agent|orchestrat|agent.?loop|task.?graph|planner|delegat|handoff|swarm` |
   | RAG | `retriev|chunk|rerank|knowledge.?base|corpus|citation|grounding` |
   | Embedding | `embedding|cosine|vector_dim|semantic.?search|nearest.?neighbor|similarity` |
   | MCP | `mcp|jsonrpc|tools/call|tool_registry|server.?manifest|\.well-known` |
   | AI Security | `guardrail|prompt.?injection|pii|redact|content.?safety|refusal|sanitiz|admission.?gate` |
   | Observability | `trace|telemetry|eval.?harness|scorecard|prompt.?log|observab|audit.?log` |
   | Memory | `memory|session.?state|persist|ledger|recall|knowledge.?graph` |
   | AI Agent | `agent.?framework|tool_use|function.?call|agent.?runtime|autonomous` |
   | Automation | `workflow|scheduler|cron|pipeline|orchestration|trigger|dag|queue|retry` |
   | Vector DB | `vector.?store|hnsw|ann.?index|ivf|knn|pgvector|faiss|similarity.?index` |

   Plus ONE **dependence battery** per repo (feeds `vendor_in_use` only,
   never grades):
   `anthropic|openai|gemini|mistral|cohere|huggingface|ollama|vllm|langchain|langgraph|llamaindex|crewai|autogen|haystack|dspy|pinecone|weaviate|qdrant|milvus|chroma|pgvector|elasticsearch|redis|neo4j|mem0|zep|letta|n8n|zapier|temporal|airflow|prefect|kestra|pipedream|langsmith|langfuse|promptfoo|helicone|presidio|guardrails`

   Record the LITERAL expressions you ran (they become `search_expressions`
   for absent rows).
5. **Verify before grading.** Open at most ~15 files per repo, ≤200 lines per
   read, only files with battery hits. Apply the grade ladder from Doctrine.
   The `not_peer_evidence` list on each target slot is binding.
6. **Write the evidence shard** `evidence/<repo>.scan.yaml`:
   ```yaml
   repo: <name>
   scanned: <date>
   session: <candidate id>
   purpose: "<one sentence>"
   findings:
     <category>:
       - {files: ["path:line"], note: "<what it actually is>", suggests_grade: <grade>, slots: [<slot ids>]}
   empty_batteries:
     <category>: ["<literal grep expression>"]
   vendor_hits:
     - {vendor: <name>, files: ["path"], note: "<dependence context>"}
   ```
7. **Update matrix rows.** Append the batch's repos to `repos_scanned` on ALL
   89 rows. Upgrade a grade only where new file evidence beats the current
   grade; fill `missing_for_peer` for partials; add `search_expressions` for
   rows going/staying absent. Append one matrix `change_log` entry
   `{date, title, changes[], rows_touched[]}` (newest first).
8. **Regenerate derived state.** In order, all must succeed:
   ```
   python3 tools/rollup.py --write
   python3 tools/gov_lint.py
   python3 tools/build_capability_map.py
   ```
9. **Update continuation.yaml.** Set `last_completed_candidate_id` (with a
   narrative `#` comment), set the new `next_candidate_id`, append to
   `completed_candidate_ids`, prepend a `change_log` entry. Mark the
   SCAN_TREE candidate `status: done` with `{date, session_id}`.
10. **Snapshot.** Verify `git status` is clean in every scanned repo
    (READ-ONLY invariant). Then in the host repo: single commit
    `CAND-SCAN-NN: scan <repos> — <n> rows touched`, push with
    `git push -u origin claude/ai-integration-capability-map-k1y70t`.

## Context-budget guardrails (Sonnet 5)

- Grep for counts + top-10 paths first (`-l | head`), then targeted
  `-n -C2` on chosen files. Never read whole big files.
- Never `Read` a file >2000 lines without offset/limit; never read
  generated/binary/data files.
- If a battery returns >200 hits, narrow by directory before opening anything.
- Hard cap: if the reading budget runs out mid-batch, SPLIT the candidate in
  SCAN_TREE (e.g. CAND-SCAN-04b), record the split in both change_logs, and
  finish cleanly rather than grade thin.
- Huge-repo rule (AXIS-ENGINE class): grep-only depth is acceptable; grade
  conservatively from what you verified, note the depth limit in the shard.

## Known gotcha: `re.sub` replacement-string corruption (recurred CAND-SCAN-01→04)

If your matrix-update script reads an existing string field (e.g. an old
`search_expressions` entry containing a literal backslash, like a regex
fragment) and passes that text as the **replacement** argument to
`re.sub(pattern, replacement, body)`, Python's `re` module interprets
backslash sequences in `replacement` as backreferences (`\1`, `\g<name>`,
`\\`) — so `\\.` (two backslash chars + dot, the correct YAML double-quoted
encoding of a literal `\.`) silently collapses to `\.` (one backslash) on
every single pass. Run the same script pattern across a few sessions and the
escaping degrades until PyYAML fails to parse it. This bit four sessions in a
row before being traced to its root cause.

**Fix:** never build a replacement string by concatenating previously-read
file content and pass it as `re.sub`'s second argument directly. Either (a)
use a lambda replacement — `re.sub(pattern, lambda m: new_text, body)` —
which is never escape-interpreted, or (b) avoid the whole class by not
putting literal backslashes in matrix prose at all (prefer rephrasing a
regex-looking fragment in words, as this file's own batteries table does).
`gov_lint.py` cannot catch this by construction (the corrupted-but-still-legal
single-backslash form is what breaks the parse, so a broken file fails
loudly at the next `yamlite.load` — check for that failure mode specifically
if a session's rollup/lint step throws a raw `yaml.scanner.ScannerError`
instead of a clean gov_lint failure).

## Known gotcha #2: Python `\"` silently becomes a bare `"` (recurred CAND-SCAN-05)

Same failure family, different Python foot-gun: if a matrix-generation
script builds a YAML double-quoted scalar's *content* inside a Python
`'''triple-quoted'''` (or any non-raw) string literal and writes `\"` meaning
"a literal double-quote character inside this text", Python's string-literal
parser consumes the backslash and the output already contains a bare `"` —
there is no backslash left for YAML to see as an escape. The result is a
YAML double-quoted scalar that closes early at that quote, and the parser
then hits the leftover trailing text as a syntax error (a `ParserError:
expected <block end>, but found <scalar>` a line or two later, NOT
pointing directly at the bad quote).

**Fix:** never build YAML double-quoted-scalar content that contains a
literal `"` character via a Python string escape — use single quotes (`'`)
for any nested quoting inside prose you're generating (as the matrix's own
authoring convention already does elsewhere), or build the YAML with a
real YAML/JSON serializer instead of string formatting. `tools/yamlite.py`'s
`load()` now wraps parse failures with a pointer back to this section —
read that message first before treating a broken matrix as a mystery.

## Consolidation session (CAND-CONSOLIDATE-12)

No new scanning. Re-open the cited files for ≥12 sampled non-absent rows —
ALL `peer`/`peer_plus` rows are mandatory in the sample — and demote anything
the evidence doesn't support. Then final `rollup.py --write` + `gov_lint.py` +
`build_capability_map.py`, republish the artifact, mark exit_criteria met,
set `scan_phase.active: false`, and record the closing change_log entry.
