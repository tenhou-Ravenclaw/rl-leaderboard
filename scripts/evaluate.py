#!/usr/bin/env python3
"""Evaluate a submitted model on BipedalWalker-v3 for 10 episodes."""

import argparse
import importlib.util
import json
import os
import sys
import time
import zipfile
import tempfile
from datetime import datetime, timezone

import gymnasium as gym
import numpy as np

ENV_CONFIG = {
    "BipedalWalker-v3": {
        "n_episodes": 10,
        "seed": 42,
        "max_steps": 2000,
    }
}

COMPLETION_REWARD_THRESHOLD = 300.0


def load_agent(model_zip_path: str, tmp_dir: str):
    with zipfile.ZipFile(model_zip_path, "r") as zf:
        zf.extractall(tmp_dir)

    agent_path = os.path.join(tmp_dir, "agent.py")
    if not os.path.exists(agent_path):
        raise FileNotFoundError(f"agent.py not found in {model_zip_path}")

    spec = importlib.util.spec_from_file_location("agent", agent_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.Agent(model_dir=tmp_dir)


def evaluate(model_zip_path: str, env_name: str = "BipedalWalker-v3") -> dict:
    cfg = ENV_CONFIG[env_name]
    env = gym.make(env_name)

    rewards = []
    episode_lengths = []
    distances = []
    runtimes = []
    completed = 0

    agent_tmp = tempfile.mkdtemp()
    agent = load_agent(model_zip_path, agent_tmp)

    for ep in range(cfg["n_episodes"]):
        obs, _ = env.reset(seed=cfg["seed"] + ep)
        total_reward = 0.0
        steps = 0
        start = time.time()

        for _ in range(cfg["max_steps"]):
            action = agent.act(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            if terminated or truncated:
                break

        elapsed = time.time() - start
        rewards.append(total_reward)
        episode_lengths.append(steps)
        runtimes.append(elapsed)

        # BipedalWalker: hull x position is available via info or obs[0] cumulative
        # Use total_reward as proxy; actual distance requires env internals
        distances.append(float(info.get("x_pos", 0.0)) if "x_pos" in info else 0.0)

        if total_reward >= COMPLETION_REWARD_THRESHOLD:
            completed += 1

    env.close()

    return {
        "env": env_name,
        "episodes": cfg["n_episodes"],
        "mean_reward": float(np.mean(rewards)),
        "max_reward": float(np.max(rewards)),
        "min_reward": float(np.min(rewards)),
        "std_reward": float(np.std(rewards)),
        "completion_rate": completed / cfg["n_episodes"],
        "mean_episode_length": float(np.mean(episode_lengths)),
        "mean_distance": float(np.mean(distances)),
        "mean_runtime_sec": float(np.mean(runtimes)),
    }


def parse_model_path(model_zip_path: str):
    """Extract user and model name from models/<user>/<model>/model.zip."""
    parts = model_zip_path.replace("\\", "/").split("/")
    try:
        idx = parts.index("models")
        return parts[idx + 1], parts[idx + 2]
    except (ValueError, IndexError):
        return "unknown", os.path.basename(os.path.dirname(model_zip_path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="Path to model.zip")
    parser.add_argument("--output", default=None, help="Path to write JSON result")
    parser.add_argument("--env", default="BipedalWalker-v3")
    args = parser.parse_args()

    user, model_name = parse_model_path(args.model_path)
    print(f"Evaluating: user={user}, model={model_name}, env={args.env}")

    metrics = evaluate(args.model_path, args.env)
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "model": model_name,
        **metrics,
    }

    print(json.dumps(result, indent=2))

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Result written to {args.output}")

    # Also append to history
    history_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "history.json"
    )
    if os.path.exists(history_path):
        with open(history_path) as f:
            history = json.load(f)
        history.append(result)
        with open(history_path, "w") as f:
            json.dump(history, f, indent=2)
        print(f"Appended to {history_path}")


if __name__ == "__main__":
    main()
