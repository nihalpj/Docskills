"""Build orchestrator: sample tasks -> generate plans -> mutate -> verify ->
assemble records -> write JSONL datasets + manifest. CLI:

  python3 -m data_engine.build --n-sft 480 --n-routing 1200 --n-pref 240
  python3 -m data_engine.build --smoke
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import random
import shutil
import time
from collections import Counter
from pathlib import Path

from . import ENGINE_VERSION, PLUGIN_REV, DEFAULT_SEED, DATASETS_DIR, REPO_ROOT
from . import taxonomy, corpus, mutations, verify, trajectories
from .generators import docx_gen, docx_py_gen, xlsx_gen, pptx_gen, pdf_gen
from .generators import docx_tools_gen, pdf_tools_gen, xlsx_tools_gen, pptx_tools_gen

GENERATORS = {
    ("docx", "create"): docx_gen.gen_create,
    ("docx", "edit"): docx_py_gen.gen_edit,
    ("docx", "format"): docx_py_gen.gen_format,
    ("docx", "read"): docx_py_gen.gen_read,
    ("docx", "toc_fix"): docx_tools_gen.gen_toc_fix,
    ("docx", "footer_fix"): docx_tools_gen.gen_footer_fix,
    ("docx", "comment"): docx_tools_gen.gen_comment,
    ("pdf", "report"): pdf_gen.gen_report,
    ("pdf", "merge"): pdf_tools_gen.gen_merge,
    ("pdf", "split"): pdf_tools_gen.gen_split,
    ("pdf", "rotate"): pdf_tools_gen.gen_rotate,
    ("pdf", "crop"): pdf_tools_gen.gen_crop,
    ("pdf", "extract_text"): pdf_tools_gen.gen_extract_text,
    ("pdf", "extract_table"): pdf_tools_gen.gen_extract_table,
    ("pdf", "extract_image"): pdf_tools_gen.gen_extract_image,
    ("pdf", "form_fill"): pdf_tools_gen.gen_form_fill,
    ("pdf", "meta_edit"): pdf_tools_gen.gen_meta_edit,
    ("pdf", "font_check"): pdf_tools_gen.gen_font_check,
    ("pdf", "toc_check"): pdf_tools_gen.gen_toc_check,
    ("pdf", "palette"): pdf_tools_gen.gen_palette,
    ("pdf", "qa"): pdf_tools_gen.gen_qa,
    ("xlsx", "create"): xlsx_gen.gen_create,
    ("xlsx", "edit"): xlsx_gen.gen_edit,
    ("xlsx", "analyze"): xlsx_gen.gen_analyze,
    ("xlsx", "inspect"): xlsx_tools_gen.gen_inspect,
    ("xlsx", "scan"): xlsx_tools_gen.gen_scan,
    ("xlsx", "audit"): xlsx_tools_gen.gen_audit,
    ("xlsx", "pivot"): xlsx_tools_gen.gen_pivot,
    ("pptx", "create"): pptx_gen.gen_create,
    ("pptx", "inspect_edit"): pptx_tools_gen.gen_inspect_edit,
}

AUTHORING = {"create", "edit", "format", "read", "analyze", "report"}

def _kind_tag(skill: str, route: str) -> str:
    if route in AUTHORING:
        if skill == "docx":
            return "node-docx" if route == "create" else "python-docx"
        if skill == "pdf":
            return "python-pdf"
        if skill == "pptx":
            return "node-pptx"
        return "python-xlsx"
    return f"{skill}-tools"   # python-docx-tools / python-pdf-tools / python-xlsx-tools / python-pptx-tools

REPAIR_PROB = 0.5


def _make_task(index: int, global_seed: int) -> taxonomy.TaskSpec:
    rng = random.Random(f"{global_seed}:sample:{index}")
    spec = taxonomy.sample_task(rng, index)
    spec.seed = random.Random(f"{global_seed}:content:{index}").randrange(2**31)
    return spec


def process_task(index: int, global_seed: int, artifacts_root: Path,
                 want_repair: bool) -> dict:
    """Returns {'status': 'ok'|'rejected', ...stats}. Deterministic per index."""
    spec = _make_task(index, global_seed)
    task_rng = random.Random(spec.seed)
    plan = GENERATORS[(spec.skill, spec.route)](spec, task_rng)
    pack = corpus.load_context_pack(spec.skill, spec.route, spec.scene)
    spec.context_files = pack["files"]
    spec.lineage = {"engine": ENGINE_VERSION, "plugin_rev": PLUGIN_REV,
                    "build_seed": global_seed, "task_seed": spec.seed}

    kind = _kind_tag(spec.skill, spec.route)
    mutation = mutations.pick_mutation(kind, spec.scene,
                                       random.Random(spec.seed ^ 0xA11CE))
    use_repair = want_repair and mutation is not None

    workdir = artifacts_root / spec.task_id
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    stats = {"skill": spec.skill, "route": spec.route, "scene": spec.scene,
             "lang": spec.lang, "difficulty": spec.difficulty}

    if use_repair:
        mutated_code = mutation.mutate(plan["code"])
        fail_out = verify.verify({**plan, "code": mutated_code}, workdir)
        if fail_out["pass"] or not fail_out["exec"]:
            stats.update(status="mutation_undetected", use="clean")
        else:
            fixed_code = mutation.fix(mutated_code)
            pass_out = verify.verify({**plan, "code": fixed_code}, workdir)
            if not pass_out["pass"]:
                stats.update(status="rejected", reason="fixed-still-fails",
                             violations=pass_out["violations"][:3])
                return {"spec": spec, "stats": stats}
            traj = trajectories.build_repair(
                spec, plan, pack["system"], mutated_code, fail_out,
                fixed_code, pass_out, mutation.name, mutation.error_class)
            pref = trajectories.build_preference(
                spec, plan, pack["system"], mutated_code, fail_out, fixed_code)
            stats.update(status="ok", use="repair", mutation=mutation.name,
                         error_class=mutation.error_class)
            return {"spec": spec, "stats": stats, "traj": traj, "pref": pref, "plan": plan}
    # clean path (also the fallback for undetected mutations)
    clean_out = verify.verify(plan, workdir)
    if not clean_out["pass"]:
        stats.update(status="rejected", reason="clean-fails",
                     violations=clean_out["violations"][:3])
        return {"spec": spec, "stats": stats}
    traj = trajectories.build_clean(spec, plan, pack["system"], clean_out)
    stats.update(status="ok", use="clean")
    return {"spec": spec, "stats": stats, "traj": traj, "plan": plan}


def build(n_sft: int, n_routing: int, n_pref: int, seed: int, out: Path,
          smoke: bool = False) -> dict:
    t0 = time.time()
    artifacts_root = out / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    # SFT + preference tasks
    results, stats_all = [], []
    # First pass sequential smoke to fail fast
    if smoke:
        probe = process_task(0, seed, artifacts_root, want_repair=True)
        if probe["stats"]["status"] != "ok":
            raise RuntimeError(f"smoke probe failed: {probe['stats']}")

    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(process_task, i, seed, artifacts_root, True): i
                   for i in range(n_sft)}
        for n, fut in enumerate(cf.as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            stats_all.append(r["stats"])
            if n % 25 == 0 or n == n_sft:
                ok = sum(1 for s in stats_all if s.get("status") == "ok")
                print(f"  [sft {n}/{n_sft}] ok={ok}", flush=True)

    ok_results = [r for r in results if r["stats"].get("status") == "ok"]
    repair_results = [r for r in ok_results if r["stats"].get("use") == "repair"]
    clean_results = [r for r in ok_results if r["stats"].get("use") == "clean"]

    sft_path, pref_path, routing_path = out / "sft_trajectories.jsonl", \
        out / "preference_pairs.jsonl", out / "routing.jsonl"

    with sft_path.open("w", encoding="utf-8") as f:
        for r in ok_results:
            f.write(json.dumps(r["traj"], ensure_ascii=False) + "\n")
    pref_written = repair_results[:n_pref]
    with pref_path.open("w", encoding="utf-8") as f:
        for r in pref_written:
            f.write(json.dumps(r["pref"], ensure_ascii=False) + "\n")

    # routing set — cheap, no execution
    n_written = 0
    with routing_path.open("w", encoding="utf-8") as f:
        i = 900000
        while n_written < n_routing:
            i += 1
            spec = _make_task(i, seed + 1)
            rng = random.Random(spec.seed)
            try:
                plan = GENERATORS[(spec.skill, spec.route)](spec, rng)
            except KeyError:
                continue
            f.write(json.dumps(trajectories.build_routing(spec, plan["request"]),
                               ensure_ascii=False) + "\n")
            n_written += 1

    manifest = _manifest(stats_all, ok_results, repair_results, clean_results,
                         n_written, len(pref_written), seed, out, t0, smoke)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    return manifest


def _manifest(stats_all, ok_results, repair_results, clean_results, n_routing,
              n_pref_written, seed, out: Path, t0: float, smoke: bool) -> dict:
    def count_by(key, items):
        return dict(Counter(s.get(key) for s in items))

    def sha256_file(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]

    strat = Counter()
    for r in ok_results:
        st = r["stats"]
        strat[f"{st['skill']}/{st['route']}/{st['lang']}/L{st['difficulty']}"] += 1
    files = {}
    for name in ("sft_trajectories.jsonl", "preference_pairs.jsonl", "routing.jsonl"):
        p = out / name
        if p.exists():
            files[name] = {"sha256_16": sha256_file(p), "bytes": p.stat().st_size}
    status_counts = Counter(s.get("status") for s in stats_all)
    return {
        "engine_version": ENGINE_VERSION, "plugin_rev": PLUGIN_REV,
        "build_seed": seed, "smoke": smoke,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_seconds": round(time.time() - t0, 1),
        "counts": {
            "attempted": len(stats_all), "sft_ok": len(ok_results),
            "sft_repair": len(repair_results), "sft_clean": len(clean_results),
            "preference_pairs": n_pref_written,
            "routing": n_routing,
            "rejected": dict(status_counts),
        },
        "strata": dict(sorted(strat.items())),
        "mutations": dict(Counter(r["stats"].get("mutation") for r in repair_results)),
        "error_classes": dict(Counter(r["stats"].get("error_class") for r in repair_results)),
        "files": files,
        "notes": "All records execution-verified against document-skills postcheck "
                 "and structural checkers; rejected attempts are excluded.",
    }


def main():
    ap = argparse.ArgumentParser(description="DocSLM data engine build")
    ap.add_argument("--n-sft", type=int, default=480)
    ap.add_argument("--n-routing", type=int, default=1200)
    ap.add_argument("--n-pref", type=int, default=240)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out", type=Path, default=DATASETS_DIR)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        args.n_sft, args.n_routing, args.n_pref = 8, 12, 4
    print(f"building: sft={args.n_sft} routing={args.n_routing} pref={args.n_pref} "
          f"seed={args.seed} out={args.out}", flush=True)
    manifest = build(args.n_sft, args.n_routing, args.n_pref, args.seed,
                     args.out, args.smoke)
    print(json.dumps(manifest["counts"], indent=2))
    print(f"done in {manifest['wall_seconds']}s — datasets in {args.out}")


if __name__ == "__main__":
    main()
