#!/usr/bin/env python3
"""Generate leaderboard/README.md from results/history.json."""

import argparse
import json
import os
from datetime import datetime


def best_per_user_model(history: list) -> list:
    """Return the best result per (user, model) pair by mean_reward."""
    best = {}
    for entry in history:
        key = (entry["user"], entry["model"])
        if key not in best or entry["mean_reward"] > best[key]["mean_reward"]:
            best[key] = entry
    return sorted(best.values(), key=lambda x: x["mean_reward"], reverse=True)


def format_leaderboard(rows: list) -> str:
    lines = [
        "# RL Leaderboard",
        "",
        f"> 最終更新: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Current Rankings",
        "",
        "| Rank | User | Model | Mean Reward | Max Reward | Completion Rate | Env |",
        "|------|------|-------|-------------|------------|-----------------|-----|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['user']} | {r['model']} "
            f"| {r['mean_reward']:.1f} | {r['max_reward']:.1f} "
            f"| {r['completion_rate']*100:.0f}% | {r['env']} |"
        )

    lines += [
        "",
        "## Experiment History",
        "",
        "| User | Model | Mean Reward | Std | Date |",
        "|------|-------|-------------|-----|------|",
    ]
    for r in sorted(history_global, key=lambda x: x["timestamp"], reverse=True):
        date = r["timestamp"][:10]
        lines.append(
            f"| {r['user']} | {r['model']} | {r['mean_reward']:.1f} "
            f"| {r['std_reward']:.1f} | {date} |"
        )

    lines += ["", "---", "_自動生成 by [rl-leaderboard](../../)_", ""]
    return "\n".join(lines)


history_global = []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", default="results/history.json")
    parser.add_argument("--output", default="leaderboard/README.md")
    args = parser.parse_args()

    with open(args.history) as f:
        history = json.load(f)

    global history_global
    history_global = history

    rows = best_per_user_model(history)
    content = format_leaderboard(rows)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(content)

    print(f"Leaderboard written to {args.output} ({len(rows)} entries)")


if __name__ == "__main__":
    main()
