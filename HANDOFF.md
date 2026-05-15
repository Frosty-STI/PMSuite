# HANDOFF — PMSuite Gantt Builder

This document is the resume point for any fresh agent or developer picking up where we left off. It is intentionally short — depth lives in the cross-referenced docs.

## Where we are right now

- **Walking skeleton committed and pushed** (commit `10a294d`, branch `main`, repo `https://github.com/Frosty-STI/PMSuite`).
- **11 tests pass** (`pytest -q` ~1 sec). The end-to-end pipeline (load JSON → validate → schedule → build Excel) is real and working.
- **8 location enum** wired with USA-perspective work-weeks. Holiday-library seed map prepared but holidays themselves are empty in the demo projects.
- **One commit upstream of `Initial commit`.** The repo's user-facing artifact at this moment is the walking skeleton.

## What's locked (no need to re-litigate)

All 26 design decisions from the grilling session are captured in [MASTERECAP.md](MASTERECAP.md). See [DESIGN.md](DESIGN.md) for the architecture-level rationale, [JSONFILE.md](JSONFILE.md) for the JSON schema, [API.md](API.md) for the Python API contract, [EXCELBUILDER.md](EXCELBUILDER.md) for the Excel output spec, and [STREAMLIT.md](STREAMLIT.md) for the UI spec.

Latest commits this session: parent completion cascade preserves children's earlier `actual_completion_date` (does NOT overwrite — Q8d / common-sense reading confirmed by user).

## What's stubbed (the work ahead)

Walking skeleton ships the pipeline shape; these are real holes the customer demo needs filled:

1. **Backward-pass CPM + total float** — `gantt_builder/critical_path.py` returns empty critical set.
2. **SS / FF / SF dependency types + lag** — currently fall back to FS semantics silently (concerning for handoff).
3. **Delay propagation engine + auto-catchup-on-load + `delay_log` audit trail** — the "living document" headline feature is not yet built.
4. **Parent completion cascade + completion freeze** — design decided, code not yet written.
5. **Full Excel rendering** (Option E segmented colors, today line, weekend/holiday shading per row's location, parent summary bars).
6. **Streamlit editing surface** — task add/edit/delete, dependency picker with explanation expander, dirty-state badge with browser beforeunload warning, New Project form.
7. **Holiday editor page** with re-seed-from-library diff.
8. **Expand `examples/npde_demo.json`** to ~30-50 tasks modeling a generic NPDE program drawn from public-web semiconductor flows. Public-domain only — never TI internal data. Seed real 2026-2027 holidays.
9. **Remaining test files:** `test_validation.py`, `test_scheduler.py`, `test_delays.py`, `test_completion.py`, `test_dependencies.py`, `test_critical_path.py`, `test_locations.py`, `test_holidays.py`, `test_excel_builder.py`, `test_excel_visual.py`, `test_performance.py`.

## The user's current targeting

- **Demo audience: external customers / cross-team handoff.** Both function and visual polish required.
- **Public web NPDE data only.** Never TI internal data in this public repo.
- **Per-feature commits.** Each item from "stubbed" list = one commit, pushed.
- **License: MIT** (default, override if enterprise constraint surfaces).
- **Real holidays** seeded for 2026-2027 in the demo project.
- **Color palette: locked** per [DESIGN.md §14.4](DESIGN.md).

## Two paths the user is choosing between

These were on the table when this handoff was written:

**Path A — Go-mode (autonomous).** I work through all 9 steps with ~4 visual/data checkpoints from the user (~30 min total user time). Wall clock: 5-12 hours of agent execution time.

**Path B — Pair-programming-mode.** User watches in real-time, tighter feedback loop, slower but tighter alignment.

User has not yet selected. **First question to ask on resume: which path?**

## What a fresh agent should do on resume

1. **Greet briefly and confirm Path A vs Path B.**
2. **Read [MASTERECAP.md](MASTERECAP.md)** before touching code — every design call is captured there.
3. **Run `pytest -q` from `C:\Users\Frosty\PMsuite`** to confirm the test suite still passes.
4. **Start at Step 1: Backward-pass CPM + total float.** Plan: implement `_backward_pass()` in `gantt_builder/critical_path.py`, populate `total_float` dict, mark `critical_task_ids` where float == 0, exclude completed tasks. Add `test_critical_path.py` with at least 3 cases (linear chain, parallel diamond, completed-task exclusion). Commit + push.

## Suggested skills for next session

- **No `grill-me` needed** — the grilling session is closed, decisions locked.
- **No `handoff` needed mid-stream** — this doc is the persistent record.
- Plain `Edit` / `Write` / `Bash` / `Read` / `Glob` / `Grep` tool use is the entire next-session toolkit.
- If a true new ambiguity surfaces, ask the user directly rather than spawn an agent.

## Where things live

```
C:\Users\Frosty\PMsuite\          # local clone, ~/.git pushed to GitHub
├── DESIGN.md                     # architecture-level design rationale
├── MASTERECAP.md                 # all 26 grilling decisions in one place
├── API.md                        # Python API contract
├── JSONFILE.md                   # JSON schema reference
├── EXCELBUILDER.md               # Excel output spec
├── STREAMLIT.md                  # UI spec
├── HANDOFF.md                    # this file
├── README.md                     # user-facing intro
├── gantt_builder/                # the Python package (walking skeleton)
├── ui/streamlit_app.py           # walking-skeleton Streamlit shell
├── tests/                        # 11 passing tests
├── examples/                     # small_demo.json (working) + npde_demo.json (stub)
└── output/                       # gitignored, generated Excel goes here
```

User auto-memory at `C:\Users\Frosty\.claude\projects\C--Users-Frosty\memory\`:
- `user_domain_semiconductor_npde.md` — domain context (NPDE, e-day vs working-day, global sites).
- `MEMORY.md` — index.

## Tone the user expects

- Crisp, decisive. They've been answering "your suggestion" or specific overrides — they know what they want.
- One question at a time when ambiguity arises.
- Don't ask permission for things already authorized ("push to github freely", per-feature commits, MIT license).
- Don't pad responses. The user has been engaged for many hours; respect their attention.

## Final notes

- User is running Python 3.12.1 on Windows 11. Package installed via `pip install --user -e "C:\Users\Frosty\PMsuite[dev]"`.
- `streamlit.exe` is at `C:\Users\Frosty\AppData\Roaming\Python\Python312\Scripts\` — not on PATH; user must use `python -m streamlit run ui\streamlit_app.py` or add to PATH.
- `gh` CLI was installed during the session but isn't on PATH; not blocking — plain `git push` works with the existing remote.
- Git identity was set inline for the walking-skeleton commit using `user.name="Frosty-STI"` and `user.email="s1lv3rstreak@gmail.com"`. Future commits should use the same identity until the user configures it permanently.
- Latest model: Opus 4.7 (`claude-opus-4-7`). Switched mid-session per user `/model` toggles.
