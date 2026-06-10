#!/usr/bin/env python3
"""Write a GitHub Actions job summary from the latest evaluation result."""

import json
import os
import sys


def main():
    result_path = sys.argv[1] if len(sys.argv) > 1 else "results/latest.json"
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    with open(result_path) as f:
        r = json.load(f)

    lines = [
        f"## Evaluation Result — {r['user']} / {r['model']}",
        "",
        f"**Environment**: {r['env']}  ",
        f"**Episodes**: {r['episodes']}  ",
        f"**Timestamp**: {r['timestamp']}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Mean Reward | {r['mean_reward']:.2f} |",
        f"| Max Reward | {r['max_reward']:.2f} |",
        f"| Min Reward | {r['min_reward']:.2f} |",
        f"| Std Reward | {r['std_reward']:.2f} |",
        f"| Completion Rate | {r['completion_rate']*100:.0f}% |",
        f"| Mean Episode Length | {r['mean_episode_length']:.0f} steps |",
        f"| Mean Runtime | {r['mean_runtime_sec']:.2f} sec |",
        "",
    ]
    report = "\n".join(lines)
    print(report)

    if summary_path:
        with open(summary_path, "a") as f:
            f.write(report)


if __name__ == "__main__":
    main()
