# Datasets — DocSLM Training Data (Batch 2026.10-r3, seed 2026, uniform coverage + reasoning)

Production dataset produced by the [data engine](../data_engine/) per [Data Engine spec](03_DATA_ENGINE.md). **Every record is grounded in real execution AND carries a reasoning trace**: generated scripts ran in the sandbox against the document-skills plugin v0.1.4 — including the plugin's own CLIs (`pdf.py`, `xlsx.py`, `postcheck.py`, `add_toc_placeholders.py`, `fix_footer_fields.py`, `document.py`, `pdf_qa.py`) — and every assistant turn is prefixed with a Qwen3-style `<think>` block derived from the plan and the measured failure signals. Nothing unverified was emitted.

## 1. What shipped (`datasets/`)

| File | Records | Size | Contents |
|---|---|---|---|
| `sft_trajectories.jsonl` | 930 | ~9 MB | Full tool-loop trajectories with reasoning on every assistant turn; 573 contain a real executed repair turn |
| `preference_pairs.jsonl` | 240 | ~1.8 MB | chosen (full plan reasoning + verified code) vs rejected (deliberately shallow reasoning + measured-failing code) |
| `routing.jsonl` | 1,240 | ~1 MB | Brief routing rationale in `<think>`, then the golden `{skill, route, scene}` JSON |
| `manifest.json` / `validation_report.json` | — | — | Strata, hashes, capability coverage, reasoning contract report |
| `artifacts/` | 930 workdirs | 33 MB | Full audit trail: every script + artifact |

**Build fingerprint:** seed `2026` · engine `1.2.0` · plugin `document-skills@0.1.4` · validation **PASSED** (0 problems).

## 2. Reasoning contract (new in r3)

Every assistant tool-call turn must carry a `<think>...</think>` block; the validator enforces presence, depth (≥120 chars), and groundedness (must mention the route, tooling path, plan, failure analysis, or postcheck). Four turn types:

| Turn | Reasoning content |
|---|---|
| Turn-1 (plan) | route/scene/difficulty, applicable formatting rules (line 312, ShadingType.CLEAR, table margins…) or the plugin CLI contract (JSON `status:'success'`, exit-1-on-error, `--output` flags), step plan, repair budget |
| Repair | quotes the **measured** failure signal (exit + stderr head, or verifier violations), names the root-cause class, states the minimal targeted patch and the never-regenerate policy |
| Verification | why postcheck/the structural check is authoritative, expected outcome, escalation path |
| DPO rejected side | deliberately shallow "just run it" rationale — a contrastive signal so preference optimization also teaches reasoning quality |

Reasoning is generated from the plan/mutation metadata (supervised CoT), so it is always consistent with what the code actually does — no hallucinated rationale. The routing head reasons briefly before emitting its JSON label.

Example — a repair turn after a real `SyntaxError`:

```json
{"role": "assistant", "content": "<think>\nFailure analysis (repair turn 1/2).\nMeasured signal: script exited non-zero:   File \"gen.py\", line 51     doc.build(story              ^ SyntaxError: '(' was never closed\nRoot cause: a typo broke the code before it could run.\nPatch plan: minimal, targeted change only — close the unclosed doc.build(story) call. Keep the rest of the working script unchanged; do not regenerate the whole artifact.\nThen re-run and postcheck again; if it still fails, escalate.\n</think>",
 "tool_calls": [{"id": "call_000002", "type": "function",
                 "function": {"name": "run_python",
                              "arguments": "{\"code\": \"# targeted patch: fix pdf_syntax (syntax)\\n…\"}"}}]}
```

**Trainer guidance:** keep `assistant_only_loss=True` (think blocks live in assistant turns, so CoT is trained while system/user/tool text stays masked). At inference, run the model with thinking enabled (Qwen3.5 `enable_thinking`); the loop parser may strip `<think>` blocks from displayed output but must feed them back into context as usual.

## 3. Uniform function coverage (the "identical performance" contract)

Tasks are assigned by **deterministic round-robin over the 30 capabilities** — not random weights — so every function group gets exactly the same volume. The validator enforces this as a hard gate:

- **30/30 capabilities × 31 trajectories each** (min = max = 31)
- **Difficulty exactly uniform: 310 / 310 / 310** for L1/L2/L3
- Scenes uniform within each capability; language en-US only

**Capability matrix (30):**

| Skill | Capabilities |
|---|---|
| docx (7) | create · edit · format · read · **toc_fix** (`add_toc_placeholders.py`) · **footer_fix** (`fix_footer_fields.py`) · **comment** (`document.py` comment API) |
| pdf (14) | report · **merge** · **split** · **rotate** · **crop** · **extract_text** · **extract_table** · **extract_image** · **form_fill** · **meta_edit** · **font_check** · **toc_check** · **palette** · **qa** (`pdf_qa.py`) |
| xlsx (7) | create · edit · analyze · **inspect** · **scan** · **audit** · **pivot** (`xlsx.py` CLI) |
| pptx (2) | create · **inspect_edit** (python-pptx) |

Bold = plugin-tool capabilities added in r2: the model trains on driving the plugin's real CLIs (e.g. `pdf.py form.fill -o out.pdf -d '{...}'`, `xlsx.py pivot --source Data!A1:B5 ...`), with scripts referencing the neutral sandbox mount `/skills/` (mapped to the plugin dir at exec time, so records contain no machine paths).
## 4. Verification guarantees

Per-capability verification uses the **authoritative tool for that function**: postcheck.py (docx artifacts), the plugin CLI's own JSON status + content sentinels (pdf/xlsx tool tasks), openpyxl reload (xlsx artifacts), python-pptx/zip checks (pptx), pypdf page/text checks (pdf artifacts). Tool scripts tolerate pdf.py's stdout deprecation warnings by extracting the trailing JSON object.

**Repair curriculum** — 573 repair trajectories across 13 mutation classes (each kept only when the mutated script measurably FAILS and the fixed script PASSES): `py_syntax` 404, `ref_unknown_sheet` 30, `cli_flag_typo` 29 (new: corrupts `--output`→`--outpu` in pdf CLI calls), `missing_import_py` 24, `attr_typo` 20, `openpyxl_import` 20, `undefined_method` 15, `pdf_syntax` 9, `missing_import` 10, `undefined_helper` 4, `shading_solid` 5, `trailing_blank_page` 2, `heading_level_skip` 1.

## 5. Rebuild & scale out

```bash
cd docslm
python3 -m data_engine.build --n-sft 930 --n-routing 1240 --n-pref 240 --seed 2026
python3 -m data_engine.validate     # enforces capability coverage + quotas; exit 1 on failure
python3 -m data_engine.build --smoke   # 8-record quick check
```

Scaling keeps exact uniformity: any n divisible by 30 yields n/30 per capability (the validator allows ±3 spread otherwise).

## 6. Honest limitations

1. **Five plugin functions are not covered because their engines cannot run in this sandbox**: `xlsx.py recalc` (needs LibreOffice — absent), `pdf.py convert.latex` (Tectonic — absent), `convert.html` + creative/poster briefs (Playwright/Chromium — absent), `convert.office` (LibreOffice). Installing those engines is the only remaining gap; the factory needs no changes once they exist. `xlsx.py chart` is not a registered subcommand in plugin v0.1.4 (unreachable).
2. **Template-derived authoring code.** The 7 authoring capabilities (create/edit/format/report) use parameterized templates with randomized content; production-scale diversity needs teacher-model rollouts through this same verifier (Data Engine §4). Tool-route scripts are the plugin's real CLI invocations.
3. **No judge-lite image data** (page-PNG verdict pairs) — separate dataset, needs rendering.
4. **Single repair turn** per repair trajectory.
5. Minor duplicate turn-1 scripts across capabilities (validator reports 2) — harmless; mix seeds for training.
