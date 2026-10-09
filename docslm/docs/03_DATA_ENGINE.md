# Data Engine — DocSLM-0.8B

The data engine turns the document-skills plugin itself into a training-data factory. Every example is grounded in **real execution** against the plugin's actual scripts — nothing is kept that has not run, passed postcheck, and (for creation tasks) been accepted by the judge.

---

## 1. Pipeline overview

```mermaid
flowchart LR
    Tax["task taxonomy<br/>& sampler"] --> Seeds["seed task specs"]
    Seeds --> Teacher["teacher rollouts<br/>frontier model + skill corpus<br/>in the real sandbox"]
    Teacher --> Exec{"executed<br/>clean?"}
    Exec -- yes --> PC{"postcheck /<br/>compile / recalc?"}
    Exec -- no -->|"failure trace"| Miner
    PC -- yes --> JUDGE{"judge accepts?"}
    PC -- no -->|"violation trace"| Miner
    JUDGE -- yes --> Keep["accepted trajectory"]
    JUDGE -- no -->|"judge issues"| Miner
    Keep --> Dedup["dedup + decontaminate<br/>vs DocBench"]
    Dedup --> DS[("SFT + DPO datasets")]
    Miner["repair miner<br/>failure → successful repair pairs"] --> DS

    style Keep fill:#c8e6c9
    style DS fill:#cfd8dc
```

The **repair miner** is the differentiator: failures from teacher rollouts are not discarded — a second teacher attempt is given the diagnostics and asked for a *targeted patch*. Successful `failure → patch → pass` sequences become the model's self-repair curriculum (PRD FR-6/FR-7). Failures are also *deliberately injected* (see §5).

---

## 2. Task taxonomy and sampler

Tasks are sampled from a stratified matrix so the model sees the whole product surface, not just easy DOCX creation.

**Dimensions**

| Dimension | Values | v1 weights |
|---|---|---|
| Skill | docx, xlsx, pptx, pdf | 35 / 25 / 20 / 20 % |
| Route | create, edit, format, comment, read; pdf briefs: report / creative / academic / process | create 45%, edit 20%, process/read 20%, format+comment 15% |
| Scene | report, contract, resume, exam, academic, official-doc, copywriting; xlsx: finance, analyze, … | uniform over applicable |
| Language | en-US (English-only corpus) | 100 % |
| Difficulty | L1 single-artifact simple · L2 multi-section + tables/charts · L3 multi-artifact or multi-repair | 40 / 40 / 20 % |
| Input modality | outline-only, attachment-edit, data-file (CSV/JSON → doc), mixed | per route |

**Seed sources** (for realistic content, never verbatim copyrighted docs):

- Synthetic entity generators: company/department/person name pools, finance time-series, project trackers — so tables and charts have plausible data.
- CC-licensed corpora (Wikipedia, Common Crawl derived, gov open data) for long-form content blocks.
- Templatized document skeletons per scene (a contract has parties/clauses/consideration; an exam has questions/rubrics) with randomized fill.

**Volume plan**

| Dataset | Examples | Avg turns | Notes |
|---|---|---|---|
| SFT trajectories | 60k accepted | 4–9 | includes ≥ 25% containing a repair turn |
| Routing-only (cheap) | 20k | 1 | skill/route/scene classification, first token supervision |
| Preference pairs | 12k | — | chosen = accepted, rejected = near-miss (exec or judge fail) |
| Judge-lite (image, verdict) | 30k pages | — | page PNG + judge JSON; balanced pass/fail |
| DocBench (held out) | 1,200 tasks | — | frozen, decontaminated, never trained on |

---

## 3. Trajectory format

Multi-turn, OpenAI tools format — byte-identical to what the production server will replay (ADR-3). One JSONL record:

```json
{
  "id": "traj_014283",
  "spec": {"skill": "docx", "route": "create", "scene": "contract",
           "lang": "en-US", "difficulty": 2, "sampler_seed": 8842},
  "context_pack": {"route_file": "routes/create.md@0.1.4",
                   "scene_file": "scenes/contract.md@0.1.4",
                   "cover_recipe": "R3"},
  "messages": [
    {"role": "system", "content": "<packed prompt skeleton, English-only>"},
    {"role": "user", "content": "Draft a software development services agreement covering scope, fees, IP, confidentiality and liability; generate contract.docx."},
    {"role": "assistant", "tool_calls": [{"function": {"name": "run_node",
      "arguments": {"code": "const {Document…} = require(\"docx\"); …"}}}]},
    {"role": "tool", "name": "run_node", "content": "{\"exit\": 0, \"artifact\": \"contract.docx\"}"},
    {"role": "assistant", "tool_calls": [{"function": {"name": "postcheck",
      "arguments": {"path": "contract.docx"}}}]},
    {"role": "tool", "name": "postcheck", "content": "{\"violations\": [\"line-spacing 1.0 on p.3\"]}"},
    {"role": "assistant", "tool_calls": [{"function": {"name": "run_node",
      "arguments": {"code": "/* targeted patch: set line 312 on section 3 */ …"}}}]},
    {"role": "tool", "name": "postcheck", "content": "{\"violations\": []}"},
    {"role": "assistant", "content": "Agreement completed: …"}
  ],
  "verification": {"exec": "pass", "postcheck": "pass", "judge": {"verdict": "pass",
                   "pages": 4}, "repair_turns": 1},
  "lineage": {"teacher": "…", "sandbox_image": "docslm-sbx@sha256:…", "plugin_rev": "0.1.4"}
}
```

Loss is computed on assistant tokens only (system/user/tool tokens masked). The `verification` and `lineage` blocks are training metadata — never part of the model context.

---

## 4. Teacher rollout protocol

1. **Context assembly exactly as production** (Architecture §3 skeleton). The teacher sees what DocSLM will see — no privileged hints — so learned behaviors transfer.
2. **Sandbox = production image.** `docslm-sbx` container: plugin 0.1.4 scripts, docx-js, openpyxl, pptxgenjs, reportlab, pikepdf, tectonic, soffice-headless for rendering; no network.
3. **Loop guards identical to runtime** (12 turns, 2 repairs). Trajectories that only succeed by breaking guardrails are rejected — the student could not reproduce them either.
4. **Best-of-n with diversity:** 4 rollouts per seed; keep up to 2 distinct accepted trajectories (different valid approaches are valuable).
5. **Repair-turn injection:** for 30% of accepted create-trajectories, continue the episode by applying a mutation from §5 and letting the teacher repair it.

Teacher cost control: seeds are cheap to generate; rollouts are the cost. Budget ≈ 240k rollouts → ~90k accepted → dedup → 60k SFT. Track acceptance rate per stratum; under-sampled strata get re-quota'd weekly.

---

## 5. Failure injection (repair curriculum)

Deliberate mutations of *accepted* artifacts/scripts to mine `diagnosis → patch → pass` pairs:

| Mutation class | Example | Teaches |
|---|---|---|
| API error | wrong docx-js enum, removed import | reading stack traces, correct API usage |
| Format violation | line spacing 1.0, missing table margins, `ShadingType` wrong | postcheck-driven patching |
| Unit errors | cm given as twips raw number | unit discipline (567/1440/20 tables) |
| Cover violation | free-form cover instead of recipe R_k | recipe compliance (FR-5) |
| Unit errors | cm value passed where twips expected | unit discipline (567/1440/20 tables) |
| Corrupt artifact | bad ZIP, unclosed XML tag | recovery vs regenerate decision |
| Chart/range errors | `#REF!`, wrong series range | xlsx recalc repair |
| Compile errors | LaTeX missing `ctex`, float too wide | academic-brief repair |

Each mutation is applied to a *known-good* state, so the correct patch is verifiable: the post-mutation diff that restores PASS is stored as the supervision target.

---

## 6. Quality, licensing, hygiene

- **Hard filter:** no example enters SFT without `exec=pass` AND `postcheck=pass` AND (create routes) `judge=pass`. Near-misses go to preference pairs instead.
- **Dedup:** MinHash over normalized code ASTs (JS) / AST dump (Python); near-duplicate content via 8-gram Jaccard.
- **Decontamination:** every DocBench task spec (entity pools, skeletons, seeds) is hash-blocklisted from the sampler; quarterly re-check.
- **Licensing:** inputs are synthetic or CC/open-data; teacher outputs are executions over these inputs (no verbatim copyrighted documents); plugin skill files are used under their license internally for context assembly, and *retrieved at runtime* rather than memorized into weights — the released model contains no skill text.
- **Balance audit per release:** route × scene × language × difficulty quotas verified in the manifest; any cell < 50% of quota blocks the dataset version.

## 7. Manifests and versioning

Every dataset is a versioned directory + `manifest.json` (row counts per stratum, filter stats, sandbox image digest, plugin rev, sampler seed range, hash of every file). Training runs pin a manifest hash (PRD reproducibility), and every released checkpoint can answer: *exactly which data, from which factory run, trained me.*
