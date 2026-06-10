# RL Leaderboard - CLAUDE.md

## プロジェクト概要

強化学習モデルを GitHub に Push するだけで自動評価・ランキング化されるプラットフォーム。
評価環境は BipedalWalker-v3 (Gymnasium) で統一し、GitHub Actions 上で実行することで公平性を担保する。

---

## アーキテクチャ

```
rl-leaderboard/
├── .github/workflows/
│   └── evaluate.yml        # Push トリガーの評価ワークフロー
├── models/
│   └── <user>/<model_name>/
│       └── model.zip        # 提出モデル（解凍後に agent.py が必要）
├── results/
│   ├── history.json         # 全提出の評価履歴
│   └── latest.json          # 最新の評価結果
├── leaderboard/
│   └── README.md            # 自動生成されるランキング表
├── scripts/
│   ├── evaluate.py          # モデル評価ロジック（10 episode）
│   ├── update_leaderboard.py # history.json → leaderboard/README.md 生成
│   └── generate_report.py   # GitHub Actions サマリー生成
└── requirements.txt
```

---

## モデル提出の仕組み

### ディレクトリ規約

```
models/<GitHub_username>/<model_name>/model.zip
```

例: `models/fujita/SAC_v3/model.zip`

### model.zip の内容

解凍後に以下が必須:

```
agent.py    # act(observation) -> action を持つクラス Agent
```

`agent.py` の最低限のインターフェース:

```python
class Agent:
    def __init__(self, model_dir: str):
        # model_dir にある重みファイルをロード
        pass

    def act(self, observation) -> any:
        # observation を受け取り action を返す
        pass
```

---

## 評価ロジック（scripts/evaluate.py）

- 環境: `gymnasium` の `BipedalWalker-v3`
- エピソード数: 10
- シード: 固定（再現性確保）

### 収集指標

| カテゴリ | 指標 |
|---|---|
| Reward | 平均・最大・最小・標準偏差 |
| Stability | 完走率・平均エピソード長 |
| Mobility | 平均到達距離 |
| Runtime | 平均完走時間 |

### 順位付けの主指標

`mean_reward`（平均報酬）で降順ソート。

---

## GitHub Actions ワークフロー（.github/workflows/evaluate.yml）

### トリガー

`models/` 配下のファイル変更を含む Push

### ステップ

1. 変更された model.zip を検出
2. `scripts/evaluate.py` を実行
3. `results/history.json` に結果を追記
4. `scripts/update_leaderboard.py` でランキング再生成
5. `leaderboard/README.md` と `results/` を自動コミット

---

## データスキーマ

### results/history.json

```json
[
  {
    "timestamp": "2026-06-10T12:00:00Z",
    "user": "fujita",
    "model": "SAC_v3",
    "env": "BipedalWalker-v3",
    "episodes": 10,
    "mean_reward": 312.5,
    "max_reward": 340.2,
    "min_reward": 280.1,
    "std_reward": 18.3,
    "completion_rate": 0.9,
    "mean_episode_length": 1580,
    "mean_distance": 42.3,
    "mean_runtime_sec": 8.2
  }
]
```

---

## ローカル評価手順

```bash
pip install -r requirements.txt
python scripts/evaluate.py --model-path models/fujita/SAC_v3/model.zip --output results/local_test.json
```

---

## ランキング生成

```bash
python scripts/update_leaderboard.py --history results/history.json --output leaderboard/README.md
```

---

## 将来拡張の方針

- **V2**: Web Dashboard（React + Vercel）でランキング・グラフ表示
- **V3**: CartPole / MountainCar / LunarLander 等の複数環境対応
- **V4**: Kaggle 形式のチーム内コンペ機能

新しい評価環境を追加する場合は `scripts/evaluate.py` の `ENV_CONFIG` に追記する設計にすること。

---

## 注意事項

- 評価は GitHub Actions 上でのみ実施し、ローカル評価結果はランキングに反映しない
- `results/history.json` は追記のみ許可（削除・上書き禁止）
- モデル提出後は Pull Request 経由で main ブランチにマージすること
