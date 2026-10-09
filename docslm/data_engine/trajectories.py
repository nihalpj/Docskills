"""Trajectory assembly — OpenAI tools message format with grounded reasoning.

Every assistant turn carries a Qwen3-style `<think>...</think>` block in its
content (before tool_calls or the final summary):
  - turn 1: route/rules/plan reasoning (from the plan, so it matches the code)
  - repair: measured failure → root cause → targeted patch plan
  - verification: why postcheck is called and what is expected
  - rejected DPO side: deliberately shallow reasoning (contrastive signal)

Loss convention: assistant messages only (system/user/tool masked); trainers
should use assistant-only loss (e.g. TRL SFTTrainer assistant_only_loss).
"""
import json

from . import TOOL_SCHEMAS
from . import reasoning as R

_call_seq = [0]


def _call_id() -> str:
    _call_seq[0] += 1
    return f"call_{_call_seq[0]:06d}"


def assistant_tool(name: str, args: dict, think: str | None = None) -> dict:
    content = think if think else None
    return {"role": "assistant", "content": content,
            "tool_calls": [{"id": _call_id(), "type": "function",
                            "function": {"name": name,
                                         "arguments": json.dumps(args, ensure_ascii=False)}}]}


def tool_result(call: dict, content: dict) -> dict:
    return {"role": "tool",
            "tool_call_id": call["tool_calls"][0]["id"],
            "name": call["tool_calls"][0]["function"]["name"],
            "content": json.dumps(content, ensure_ascii=False)}


def _final_text(spec, artifact: str, repair_turns: int) -> str:
    txt = f"Done: generated {artifact}"
    if repair_turns:
        txt += (f" (after {repair_turns} targeted repair turn"
                f"{'s' if repair_turns > 1 else ''})")
    txt += ". Execution succeeded and verification reports no violations. The file is ready."
    return txt


def _runner_tool(plan) -> str:
    return "run_node" if plan["runner"] == "node" else "run_python"


def _fail_signal(fail_out: dict) -> str:
    if fail_out["exec"] and fail_out["exec"]["exit"] != 0:
        err = fail_out["exec"]["stderr"]
        head = err[:160].replace("\n", " ")
        return f"script exited non-zero: {head}"
    sig = "; ".join(v[:120] for v in fail_out["violations"][:2])
    return f"verifier reported violations: {sig}"


def build_clean(spec, plan, context_system, verify_out) -> dict:
    """Trajectory without repair turns (reasoned turns)."""
    runner_tool = _runner_tool(plan)
    think1 = R.plan_reasoning(spec, plan, plan["runner"])
    messages = [
        {"role": "system", "content": context_system},
        {"role": "user", "content": plan["request"]},
    ]
    c1 = assistant_tool(runner_tool, {"code": plan["code"]}, think=think1)
    messages.append(c1)
    exec_res = verify_out["exec"]
    messages.append(tool_result(c1, {"exit": exec_res["exit"], "artifact": plan["artifact"],
                                     "seconds": exec_res["seconds"]}))
    if plan["expect"]["kind"] != "extract":
        c2 = assistant_tool("postcheck", {"path": plan["artifact"]},
                            think=R.verify_reasoning(spec, plan))
        messages.append(c2)
        messages.append(tool_result(c2, {"violations": verify_out["violations"]}))
    messages.append({"role": "assistant", "content": _final_text(spec, plan["artifact"], 0)})
    return _record(spec, messages, verify_out, mutation=None, repair_turns=0)


def build_repair(spec, plan, context_system, mutated_code, fail_out,
                 fixed_code, pass_out, mutation_name, error_class) -> dict:
    """failure → diagnosis reasoning → targeted patch → pass."""
    runner_tool = _runner_tool(plan)
    think1 = R.plan_reasoning(spec, plan, plan["runner"])
    messages = [
        {"role": "system", "content": context_system},
        {"role": "user", "content": plan["request"]},
    ]
    c1 = assistant_tool(runner_tool, {"code": mutated_code}, think=think1)
    messages.append(c1)
    exec_res = fail_out["exec"]
    tool_content = {"exit": exec_res["exit"], "artifact": plan["artifact"] if fail_out["artifact"] else None,
                    "seconds": exec_res["seconds"]}
    if exec_res["exit"] != 0:
        err = exec_res["stderr"]
        tool_content["stderr"] = err[:400] + ("\n...\n" + err[-200:] if len(err) > 600 else "")
    if fail_out["violations"]:
        tool_content["violations"] = fail_out["violations"]
    messages.append(tool_result(c1, tool_content))

    think2 = R.repair_reasoning(spec, plan, mutation_name, error_class,
                                _fail_signal(fail_out), turn=1)
    patched = ("// targeted patch: fix " + mutation_name + " (" + error_class + ")\n"
               if plan["runner"] == "node"
               else "# targeted patch: fix " + mutation_name + " (" + error_class + ")\n")
    c2 = assistant_tool(runner_tool, {"code": patched + fixed_code}, think=think2)
    messages.append(c2)
    exec2 = pass_out["exec"]
    messages.append(tool_result(c2, {"exit": exec2["exit"], "artifact": plan["artifact"],
                                     "seconds": exec2["seconds"]}))
    if plan["expect"]["kind"] != "extract":
        c3 = assistant_tool("postcheck", {"path": plan["artifact"]},
                            think=R.verify_reasoning(spec, plan))
        messages.append(c3)
        messages.append(tool_result(c3, {"violations": pass_out["violations"]}))
    messages.append({"role": "assistant", "content": _final_text(spec, plan["artifact"], 1)})
    return _record(spec, messages, pass_out, mutation=mutation_name, repair_turns=1)


def build_preference(spec, plan, context_system, rejected_code, fail_out, chosen_code) -> dict:
    """chosen = full plan reasoning + verified code; rejected = shallow reasoning + code
    with the measured failure."""
    tool = "run_node" if plan["runner"] == "node" else "run_python"

    def _assistant(call_id: str, think: str, code: str) -> dict:
        return {"role": "assistant", "content": think,
                "tool_calls": [{"id": call_id, "type": "function",
                                "function": {"name": tool,
                                             "arguments": json.dumps({"code": code}, ensure_ascii=False)}}]}

    return {
        "id": f"pref_{spec.task_id}",
        "spec": spec.to_dict(),
        "prompt": [{"role": "system", "content": context_system},
                   {"role": "user", "content": plan["request"]}],
        "chosen": _assistant("call_chosen",
                             R.plan_reasoning(spec, plan, plan["runner"]), chosen_code),
        "rejected": _assistant("call_rejected", R.shallow_reasoning(spec), rejected_code),
        "meta": {"rejected_failure": {"violations": fail_out["violations"],
                                      "exit": fail_out["exec"]["exit"] if fail_out["exec"] else None},
                 "rejected_mutation": True,
                 "reasoning_contrast": True},
    }


def build_routing(spec, request: str) -> dict:
    label = {"skill": spec.skill, "route": spec.route, "scene": spec.scene}
    head = request[:60]
    return {
        "id": f"route_{spec.task_id}",
        "messages": [
            {"role": "system", "content":
                "You are the document-skills task router. Classify each user request "
                "and reply with a single JSON object: {\"skill\": docx|xlsx|pptx|pdf, "
                "\"route\": ..., \"scene\": ...}. Reason briefly inside <think> tags, "
                "then output the JSON object."},
            {"role": "user", "content": request},
            {"role": "assistant",
             "content": R.routing_reasoning(label, head) + "\n" + json.dumps(label, ensure_ascii=False)},
        ],
        "label": label,
    }


def _record(spec, messages, verify_out, mutation, repair_turns) -> dict:
    return {
        "id": f"traj_{spec.task_id}",
        "spec": spec.to_dict(),
        "context_pack": {"files": spec.context_files},
        "tools": TOOL_SCHEMAS,
        "messages": messages,
        "verification": {
            "exec": "pass" if verify_out["pass"] else "fail",
            "violations": verify_out["violations"],
            "repair_turns": repair_turns,
            "mutation": mutation,
        },
        "lineage": spec.lineage,
    }
