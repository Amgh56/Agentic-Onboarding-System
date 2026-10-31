"""Compare saved results side by side:  python -m eval.compare results/rules-....json results/agent-....json"""

import json
import sys


def main():
    files = sys.argv[1:]
    if len(files) < 2:
        raise SystemExit("Usage: python -m eval.compare first.json second.json [...]")

    results = [json.loads(open(path).read()) for path in files]
    labels = [f"{r['variant']}/{r['prompt_sha']}" for r in results]
    names = sorted({c["name"] for r in results for c in r["cases"]})

    print(f"{'':<32}" + "".join(f"{label:<22}" for label in labels))
    for name in names:
        row = f"{name:<32}"
        for r in results:
            case = next((c for c in r["cases"] if c["name"] == name), None)
            row += f"{(str(case['passed_runs']) + '/' + str(case['runs_total'])) if case else '-':<22}"
        print(row)

    for key, title in [("runs_passed", "runs passed"), ("wrong_actions", "wrong actions"), ("tool_calls", "tool calls"), ("input_tokens", "input tokens"), ("output_tokens", "output tokens")]:
        print(f"{title:<32}" + "".join(f"{r['summary'][key]:<22}" for r in results))


if __name__ == "__main__":
    main()
