# 05. プロジェクト構造

## 概要
プロジェクトの成長に備え、フラットだった `mahjong/` パッケージを機能別サブパッケージに再編した。
エージェント管理・外部データ取り込み・将来の機械学習を見据えた構造。

## ディレクトリ構成

```
260320ＭＪ/
│
├── mahjong/                      # 麻雀エンジン（純粋なルール実装）
│   ├── __init__.py               # 互換性レイヤー（主要クラスの再エクスポート）
│   ├── engine/                   # コアデータ構造
│   │   ├── tile.py               # 牌の定義・ユーティリティ・ドラ変換
│   │   ├── wall.py               # 山（壁牌）・王牌・嶺上牌
│   │   ├── player.py             # プレイヤー状態・副露操作
│   │   └── agari.py              # 和了判定・シャンテン数・手牌分解
│   ├── game/                     # ゲーム進行
│   │   ├── round.py              # 1局のゲームループ（GameRound）
│   │   └── naki.py               # 鳴き処理（NakiMixin）
│   ├── scoring/                  # 点数計算
│   │   ├── yaku.py               # 役判定（20種以上+役満5種）
│   │   └── score.py              # 符計算・翻→点数変換・支払い計算
│   └── record/                   # 棋譜記録
│       └── record.py             # JSON/テキスト出力
│
├── agents/                       # AIエージェント（エンジンとは独立）
│   ├── __init__.py               # AgentBase, RandomAgent, ShantenAgent の再エクスポート
│   ├── base.py                   # AgentBase（全エージェントの基底クラス）
│   ├── random_agent.py           # ランダム打牌エージェント
│   ├── shanten_agent.py          # シャンテン数ベース戦略エージェント
│   └── external/                 # 将来: 外部AI（Mortal等）のラッパー
│
├── viewer/                       # ビューア・管理サイト
│   ├── game_viewer/              # 棋譜再生ビューア
│   │   ├── generator.py          # HTMLファイル生成
│   │   ├── styles.py             # CSS定義
│   │   └── scripts.py            # JavaScript定義
│   └── dashboard/                # 将来: エージェント管理・対戦結果・統計
│
├── data/                         # 外部データ・研究
│   ├── parsers/                  # 将来: 天鳳/雀魂の棋譜パーサー
│   └── research/                 # 調査メモ・論文ノート
│
├── learning/                     # 将来: 機械学習（Phase 3）
│
├── tests/                        # テスト（ソース構造をミラー）
│   ├── engine/test_basic.py      # 牌・山・プレイヤーのテスト
│   ├── game/test_round.py        # ゲームループのテスト
│   ├── game/test_naki.py         # 鳴きのテスト
│   ├── scoring/test_score.py     # 点数計算のテスト
│   ├── agents/test_shanten.py    # ShantenAgentのテスト
│   └── viewer/test_viewer.py     # ビューアのテスト
│
├── docs/
│   ├── plan/                     # 計画ドキュメント
│   └── implemented/              # 実装済みドキュメント
│
├── assets/tiles/                 # 牌SVG画像（FluffyStuff CC-BY）
└── output/                       # 生成物（HTML・JSON）
```

## 依存関係の方向

モジュール間の依存は一方向に厳守する。

```
engine（tile, wall, player, agari）
   ↓
scoring（yaku, score） ← engine に依存
   ↓
game（round, naki） ← engine, scoring に依存
   ↓
record ← engine に依存
   ↓
agents ← engine に依存（game には依存しない）
   ↓
viewer ← record, engine に依存
   ↓
learning ← agents, engine に依存（将来）
```

## インポートパス

### ソースコード内
新しいパスを使用する。

```python
from mahjong.engine.tile import tile_name, is_suit
from mahjong.engine.agari import is_agari, shanten_number
from mahjong.game.round import GameRound
from mahjong.scoring.score import calculate_score
from agents import ShantenAgent
from viewer.game_viewer.generator import generate_html
```

### 互換性レイヤー
`mahjong/__init__.py` で主要クラスを再エクスポートしており、
シンプルな用途では以下も動作する。

```python
from mahjong import GameRound, is_agari, calculate_score
```

## 設計方針

### エージェントの独立性
`agents/` はトップレベルパッケージとしてエンジンから独立。
- エンジンのインターフェース（`AgentBase`）のみに依存
- 新しいエージェントは `agents/` に1ファイル追加するだけ
- 将来の管理サイト（`viewer/dashboard/`）から一元管理可能
- 外部AI（Mortal等）は `agents/external/` にラッパーとして追加

### 外部データとの接続
`data/` はエンジンとは独立した調査・データ管理の拠点。
- `data/parsers/`: 天鳳・雀魂等の棋譜フォーマットのパーサー
- `data/research/`: 外部論文・手法の調査ノート
- `data/datasets/`: 変換済みデータ（.gitignore対象）

### ファイルサイズ制限
全ファイルは500行以下を維持する。超過した場合はモジュール分割する。
