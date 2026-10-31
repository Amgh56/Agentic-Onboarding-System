"""Run the evaluation:

    python -m eval.run                      # the 4 development cases, 3 runs each, with the full agent
    python -m eval.run --variant agent      # the agent without the verifier
    python -m eval.run --variant rules      # the fixed checklist baseline (no model, free)
    python -m eval.run --final              # also the held-out case, for the final result
    python -m eval.run --system-prompt-file my_prompt.txt   # try a changed agent prompt

Results are saved in eval/results/ and compared with: python -m eval.compare a.json b.json
"""

import argparse
import hashlib
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

from app.core import llm
from app.features.agent import prompts
from eval import cases as case_list
from eval.variants import VARIANTS
from eval.world import World, play

RESULTS_DIR = Path(__file__).parent / "results"


def prompt_sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def evaluate(case, world: World) -> dict:
    checks = []
    for check in case.checks:
        try:
            happened = bool(check.test(world))
        except Exception:
            happened = False
        ok = (not happened) if check.forbidden else happened
        checks.append({"label": check.label, "ok": ok, "forbidden": check.forbidden})
    return {
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "wrong_actions": sum(1 for c in checks if c["forbidden"] and not c["ok"]),
        "escalated": world.escalated,
        "tool_calls": world.tool_calls,
    }


def run_case(case, variant_name: str) -> dict:
    before = dict(llm.usage)
    started = time.time()
    try:
        outcome = evaluate(case, play(case, VARIANTS[variant_name]()))
    except Exception:
        outcome = {"passed": False, "checks": [], "wrong_actions": 0, "escalated": False, "tool_calls": 0, "error": traceback.format_exc()}
    outcome["tokens"] = {key: llm.usage[key] - before[key] for key in before}
    outcome["seconds"] = round(time.time() - started, 1)
    return outcome


def summarize(case_results: list[dict], cases_by_name: dict) -> dict:
    runs = [(cases_by_name[c["name"]], r) for c in case_results for r in c["runs"]]
    return {
        "runs_passed": sum(1 for _, r in runs if r["passed"]),
        "runs_total": len(runs),
        "cases_passed": sum(1 for c in case_results if c["passed_runs"] == c["runs_total"]),
        "cases_total": len(case_results),
        "wrong_actions": sum(r["wrong_actions"] for _, r in runs),
        "correct_escalations": sum(1 for case, r in runs if case.expects_escalation and r["escalated"]),
        "missed_escalations": sum(1 for case, r in runs if case.expects_escalation and not r["escalated"]),
        "false_escalations": sum(1 for case, r in runs if not case.expects_escalation and r["escalated"]),
        "tool_calls": sum(r["tool_calls"] for _, r in runs),
        "input_tokens": sum(r["tokens"]["input_tokens"] for _, r in runs),
        "output_tokens": sum(r["tokens"]["output_tokens"] for _, r in runs),
        "model_calls": sum(r["tokens"]["calls"] for _, r in runs),
    }


def run_all(variant: str, runs: int = 3, names: list[str] | None = None, final: bool = False,
            out_dir=None, prompt_file: str | None = None, echo=lambda text: None) -> dict:
    selected = [c for c in case_list.ALL if (c.name in names if names else c.split == "dev" or final)]
    if any(c.split == "held_out" for c in selected) and not final:
        raise ValueError("The held-out case only runs with --final")
    if prompt_file:
        prompts.SYSTEM_PROMPT = Path(prompt_file).read_text()

    case_results = []
    for case in selected:
        results = []
        for number in range(1, runs + 1):
            result = run_case(case, variant)
            results.append(result)
            echo(f"  {case.name} run {number}/{runs}: {'PASS' if result['passed'] else 'FAIL'} "
                 f"({result['tool_calls']} tool calls, {result['tokens']['input_tokens'] + result['tokens']['output_tokens']} tokens, {result['seconds']}s)")
        case_results.append({
            "name": case.name, "split": case.split, "runs": results,
            "passed_runs": sum(1 for r in results if r["passed"]), "runs_total": runs,
        })

    out = {
        "variant": variant,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "runs_per_case": runs,
        "final": final,
        "prompt_file": prompt_file,
        "prompt_sha": prompt_sha(prompts.SYSTEM_PROMPT),
        "models": {"strong": llm.settings.model_strong, "fast": llm.settings.model_fast},
        "cases": case_results,
        "summary": summarize(case_results, {c.name: c for c in selected}),
    }
    folder = Path(out_dir) if out_dir else RESULTS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{variant}-{datetime.now():%Y%m%d-%H%M%S}.json"
    out["file"] = str(path)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out


def report(results: dict) -> str:
    s = results["summary"]
    lines = [f"\nVariant: {results['variant']}   prompt: {results['prompt_sha']}   models: {results['models']['strong']} / {results['models']['fast']}", ""]
    for case in results["cases"]:
        lines.append(f"  {case['name']:<30} {case['passed_runs']}/{case['runs_total']} passed ({case['split']})")
        for number, run in enumerate(case["runs"], start=1):
            for check in run["checks"]:
                if not check["ok"]:
                    kind = "did the wrong thing" if check["forbidden"] else "missing"
                    lines.append(f"      run {number}: {kind}: {check['label']}")
            if run.get("error"):
                lines.append(f"      run {number}: crashed: {run['error'].strip().splitlines()[-1]}")
    lines += [
        "",
        f"  Cases passed in every run : {s['cases_passed']}/{s['cases_total']}",
        f"  Runs passed               : {s['runs_passed']}/{s['runs_total']}",
        f"  Wrong actions             : {s['wrong_actions']}",
        f"  Escalations               : {s['correct_escalations']} correct, {s['missed_escalations']} missed, {s['false_escalations']} not needed",
        f"  Tool calls                : {s['tool_calls']}",
        f"  Model calls / tokens      : {s['model_calls']} calls, {s['input_tokens']} in, {s['output_tokens']} out",
        f"\n  Saved: {results['file']}",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run the onboarding evaluation.")
    parser.add_argument("--variant", choices=sorted(VARIANTS), default="full")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--cases", nargs="*", help="only these cases, by name")
    parser.add_argument("--final", action="store_true", help="include the held-out case")
    parser.add_argument("--system-prompt-file", help="replace the agent's system prompt with this file")
    args = parser.parse_args()

    names = args.cases or None
    print(f"Running variant '{args.variant}', {args.runs} run(s) per case" + (" (uses the OpenAI API)" if args.variant != "rules" else ""))
    results = run_all(args.variant, args.runs, names, args.final, prompt_file=args.system_prompt_file, echo=print)
    print(report(results))


if __name__ == "__main__":
    main()
