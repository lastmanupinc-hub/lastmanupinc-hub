# CLAUDE.md — AI Ecosystem Capability Map

> **Rulebook.** Read in this order at session start:
> 1. `CLAUDE.md` (this file) — invariants + banned patterns
> 2. `begin.yaml` — bootstrap + loop entry (`autonomous_loop_bootstrap`)
> 3. `continuation.yaml` — live ledger; `automated_loop_state` is the resume pointer
> 4. `ECOSYSTEM_TARGETS.yaml` — IMMUTABLE target taxonomy (89 slots) + scoring doctrine
> 5. `AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml` — **canonical grade truth**
> 6. `SCAN_TREE.yaml` — batch backlog · `SONNET5_ECOSYSTEM_SCAN_STRATEGY.md` — the ritual

## What this is

A cross-repo capability audit: the 31 lastmanupinc-hub repos (cloned at
`/home/user`) graded against the 89 vendor targets of "The Modern AI
Ecosystem — Tools" infographic, under the **peer-independence doctrine**:
we measure the ability to *never need* each vendor, not the ability to use
it. Honest 0% is expected; the numbers are conservative floors that only
rise with file evidence.

Output: `AI_ECOSYSTEM_CAPABILITY_MATRIX.yaml` (ledger) +
`derived/capability_map.html` (regenerable radial picture, also published as
a Claude artifact).

**Intended permanent home:** dedicated repo `lastmanupinc-hub/ai-ecosystem-map`.
Hosted here (profile repo, `ai-ecosystem-map/` subdir) because the session
token could not create repos (2026-08-16). Migration = copy this directory;
nothing outside it is load-bearing.

## Commands

```
python3 tools/rollup.py --write        # recompute percentages → derived/rollup.json + matrix parity block
python3 tools/rollup.py --check        # verify matrix parity block matches (CI-style)
python3 tools/gov_lint.py              # honesty linter — must exit 0 before every commit
python3 tools/build_capability_map.py  # regenerate derived/capability_map.html (deterministic)
```

## Invariants (do not violate)

- **READ-ONLY SCANNING.** Never commit to, edit, or open PRs on a scanned
  repo. Only this directory mutates. Verify `git status` clean in scanned
  repos before ending a session.
- **The matrix is canonical.** No file may claim a grade it contradicts.
- **vendor_in_use never raises a grade.** Dependence ≠ peerhood.
- Never grade above `absent` without a real file path in `peer_evidence`.
- Never grade `absent` without recorded `search_expressions`.
- `partial` requires `missing_for_peer`.
- `parity_100_criteria` numbers are written only by `tools/rollup.py`.
- Grades are restated, never overwritten — every change lands in the matrix
  `change_log` with `rows_touched`.
- `ECOSYSTEM_TARGETS.yaml` is immutable reference data (taxonomy + doctrine).
- Set `continuation.yaml#automated_loop_state.next_candidate_id` before
  ending ANY session.
- One candidate per session, one commit per candidate
  (`CAND-SCAN-NN: scan <repos> — <n> rows touched`).

## Banned

- Grading up from a grep hit alone (hit = `scaffold` ceiling until read)
- Citing vendor usage as peer evidence
- Hand-editing `parity_100_criteria` or `derived/`
- Scanning depth theater: claiming repos_scanned without running the batteries
- Touching `/home/user/<scanned-repo>` working trees
