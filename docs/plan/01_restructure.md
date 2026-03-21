# 01. プロジェクト構造リファクタリング計画

## 目的
プロジェクトの成長に備え、フラットな `mahjong/` パッケージを機能別サブパッケージに再編する。
エージェント管理・外部データ取り込み・将来の機械学習を見据えた構造にする。

## 現在の構造

```
260320ＭＪ/
├── mahjong/          # 全14ファイルがフラット
│   ├── tile.py           (152行)
│   ├── wall.py           (92行)
│   ├── player.py         (160行)
│   ├── agari.py          (341行)
│   ├── agent.py          (323行) ← 基底+Random+Shanten全部入り
│   ├── game.py           (367行)
│   ├── game_naki.py      (203行)
│   ├── record.py         (175行)
│   ├── yaku.py           (470行)
│   ├── score.py          (257行)
│   ├── viewer.py         (95行)
│   ├── viewer_css.py     (217行)
│   └── viewer_js.py      (305行)
├── tests/            # 6ファイルがフラット
├── docs/
├── assets/
└── output/
```

## 新しい構造

```
260320ＭＪ/
│
├── mahjong/                      # 麻雀エンジン（純粋なルール実装）
│   ├── __init__.py               # パッケージ公開API
│   ├── engine/                   # コアデータ構造
│   │   ├── __init__.py
│   │   ├── tile.py               ← mahjong/tile.py
│   │   ├── wall.py               ← mahjong/wall.py
│   │   ├── player.py             ← mahjong/player.py
│   │   └── agari.py              ← mahjong/agari.py
│   ├── game/                     # ゲーム進行
│   │   ├── __init__.py
│   │   ├── round.py              ← mahjong/game.py (GameRound)
│   │   └── naki.py               ← mahjong/game_naki.py (NakiMixin)
│   ├── scoring/                  # 点数計算
│   │   ├── __init__.py
│   │   ├── yaku.py               ← mahjong/yaku.py
│   │   └── score.py              ← mahjong/score.py
│   └── record/                   # 棋譜記録
│       ├── __init__.py
│       └── record.py             ← mahjong/record.py
│
├── agents/                       # エージェント（エンジンとは独立）
│   ├── __init__.py
│   ├── base.py                   ← mahjong/agent.py の AgentBase部分
│   ├── registry.py               # 新規: エージェント登録・メタ情報管理
│   ├── random_agent.py           ← mahjong/agent.py の RandomAgent部分
│   ├── shanten_agent.py          ← mahjong/agent.py の ShantenAgent部分
│   └── external/                 # 将来: 外部AIラッパー
│       └── __init__.py
│
├── viewer/                       # ビューア・管理サイト
│   ├── __init__.py
│   ├── game_viewer/              # 棋譜再生ビューア
│   │   ├── __init__.py
│   │   ├── generator.py          ← mahjong/viewer.py
│   │   ├── styles.py             ← mahjong/viewer_css.py
│   │   └── scripts.py            ← mahjong/viewer_js.py
│   └── dashboard/                # 将来: エージェント管理UI
│       └── __init__.py
│
├── data/                         # 外部データ・研究
│   ├── parsers/                  # 将来: 天鳳/雀魂棋譜パーサー
│   │   └── __init__.py
│   └── research/                 # 調査メモ・論文ノート
│
├── learning/                     # 将来: 機械学習（Phase 3）
│   └── __init__.py
│
├── tests/                        # テスト（ソース構造ミラー）
│   ├── engine/
│   │   ├── test_tile.py          ← tests/test_basic.py（分割）
│   │   ├── test_wall.py          ← tests/test_basic.py（分割）
│   │   ├── test_player.py        ← tests/test_basic.py（分割）
│   │   └── test_agari.py         # 将来
│   ├── game/
│   │   ├── test_round.py         ← tests/test_game.py
│   │   └── test_naki.py          ← tests/test_naki.py
│   ├── scoring/
│   │   └── test_score.py         ← tests/test_score.py
│   ├── agents/
│   │   └── test_shanten.py       ← tests/test_shanten_agent.py
│   └── viewer/
│       └── test_viewer.py        ← tests/test_viewer.py
│
├── docs/
│   ├── plan/
│   └── implemented/
│
├── assets/tiles/                 # 牌SVG画像
└── output/                       # 生成物
```

## インポートパス変更マップ

| 旧パス | 新パス |
|--------|--------|
| `mahjong.tile` | `mahjong.engine.tile` |
| `mahjong.wall` | `mahjong.engine.wall` |
| `mahjong.player` | `mahjong.engine.player` |
| `mahjong.agari` | `mahjong.engine.agari` |
| `mahjong.game` | `mahjong.game.round` |
| `mahjong.game_naki` | `mahjong.game.naki` |
| `mahjong.yaku` | `mahjong.scoring.yaku` |
| `mahjong.score` | `mahjong.scoring.score` |
| `mahjong.record` | `mahjong.record.record` |
| `mahjong.agent` (AgentBase) | `agents.base` |
| `mahjong.agent` (RandomAgent) | `agents.random_agent` |
| `mahjong.agent` (ShantenAgent) | `agents.shanten_agent` |
| `mahjong.viewer` | `viewer.game_viewer.generator` |
| `mahjong.viewer_css` | `viewer.game_viewer.styles` |
| `mahjong.viewer_js` | `viewer.game_viewer.scripts` |

### 互換性レイヤー
`mahjong/__init__.py` で主要クラス・関数を再エクスポートし、
外部からの `from mahjong import GameRound` 等は引き続き使えるようにする。

## 実装フェーズ

### Phase A: ディレクトリ作成・ファイル移動（破壊的変更なし）
1. 新ディレクトリ構造を作成（`__init__.py` 含む）
2. 既存ファイルを新しい場所にコピー
3. 各ファイルの `from mahjong.xxx` を新パスに書き換え
4. `mahjong/__init__.py` に互換エクスポートを追加
5. テストが全て通ることを確認

### Phase B: テスト再配置
1. `tests/` 配下にサブディレクトリ作成
2. テストファイルを移動・リネーム
3. テストのインポートパスを更新
4. 全テスト通過を確認

### Phase C: agents/ 分離
1. `agent.py` を `agents/base.py`, `agents/random_agent.py`, `agents/shanten_agent.py` に分割
2. `agents/registry.py` を新規作成（エージェント登録の仕組み）
3. `mahjong/game/round.py` からのエージェント参照を更新
4. テスト通過確認

### Phase D: viewer/ 分離
1. `viewer.py`, `viewer_css.py`, `viewer_js.py` を `viewer/game_viewer/` に移動
2. ファイルリネーム（generator.py, styles.py, scripts.py）
3. HTML生成パスの調整
4. テスト通過確認

### Phase E: 旧ファイル削除・クリーンアップ
1. 旧 `mahjong/` のフラットファイルを削除
2. 不要になった互換レイヤーがあれば削除
3. ドキュメント更新（`docs/implemented/`, `docs/plan/`）
4. 最終テスト・コミット

## リスク管理

| リスク | 対策 |
|--------|------|
| インポートパス変更でテストが壊れる | 各Phase後に必ず全テスト実行 |
| 循環インポート | engine → game → scoring の一方向依存を厳守 |
| 旧パスを使う外部スクリプト | `mahjong/__init__.py` で再エクスポート |
| Git履歴が途切れる | `git mv` を使ってファイル移動を追跡 |

## 依存関係の方向（厳守）

```
engine（tile, wall, player, agari）
   ↓
scoring（yaku, score） ← engine に依存
   ↓
game（round, naki） ← engine, scoring に依存
   ↓
record ← engine に依存
   ↓
agents ← engine, scoring に依存（game には依存しない）
   ↓
viewer ← record, engine に依存
   ↓
learning ← agents, engine に依存（将来）
```

## 完了条件
- [ ] 全27テストが通過する
- [ ] 全ファイルが500行以下
- [ ] `wc -l` で行数が変わっていない（ロジック変更なし）
- [ ] `git status` で旧ファイルが残っていない
- [ ] ドキュメントが新構造を反映している
