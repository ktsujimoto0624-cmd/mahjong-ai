# 実装済み機能一覧

Phase 1（基盤構築）で実装された機能のドキュメント。

## ドキュメント

| # | ファイル | 内容 |
|---|---------|------|
| 01 | [01_engine_core.md](01_engine_core.md) | 牌・山・プレイヤー・和了判定・ゲームループ・鳴き処理 |
| 02 | [02_agents.md](02_agents.md) | AIエージェント（RandomAgent / ShantenAgent） |
| 03 | [03_scoring.md](03_scoring.md) | 点数計算（役判定20種以上・符計算・ドラ） |
| 04 | [04_record_viewer.md](04_record_viewer.md) | 棋譜記録（JSON/テキスト）・HTMLビューア |
| 05 | [05_project_structure.md](05_project_structure.md) | プロジェクト構造・依存関係・設計方針 |

## モジュール構成

```
mahjong/                          # 麻雀エンジン
├── engine/                       # コアデータ構造
│   ├── tile.py                   # 牌の定義・ユーティリティ
│   ├── wall.py                   # 山（壁牌）の管理
│   ├── player.py                 # プレイヤー状態
│   └── agari.py                  # 和了判定・シャンテン数・手牌分解
├── game/                         # ゲーム進行
│   ├── round.py                  # 1局のゲームループ
│   └── naki.py                   # 鳴き処理（Mixin）
├── scoring/                      # 点数計算
│   ├── yaku.py                   # 役判定
│   └── score.py                  # 符計算・点数計算
└── record/                       # 棋譜記録
    └── record.py                 # JSON/テキスト出力

agents/                           # AIエージェント（独立パッケージ）
├── base.py                       # 基底クラス
├── random_agent.py               # ランダム
├── shanten_agent.py              # シャンテン数ベース
└── external/                     # 将来: 外部AIラッパー

viewer/                           # ビューア・管理サイト
├── game_viewer/                  # 棋譜再生ビューア
│   ├── generator.py              # HTML生成
│   ├── styles.py                 # CSS
│   └── scripts.py                # JavaScript
└── dashboard/                    # 将来: エージェント管理UI

data/                             # 外部データ・研究
learning/                         # 将来: 機械学習
```

## Phase 1 完了状況

- [x] 牌・手牌・山・河のデータ構造（カウント方式）
- [x] 4人対戦のゲームループ（ツモ和了・流局）
- [x] 和了判定（基本形・七対子・国士無双）
- [x] シャンテン数計算
- [x] ランダムエージェント・シャンテンベースエージェント
- [x] エージェントID（名前・番号で識別可能）
- [x] 棋譜記録（JSON保存・テキスト出力）
- [x] HTMLビューア（SVG牌画像・ステップ再生・麻雀卓レイアウト）
- [x] GitHub Pages公開
- [x] ロン和了（他家の捨て牌での和了・頭ハネ）
- [x] リーチ宣言の処理（リーチ判定・リーチ後ツモ切り）
- [x] 鳴き（チー・ポン・大明槓・暗槓・加槓）
- [x] 点数計算（役判定・符計算・翻→点数変換）
- [x] ドラの点数反映

### 未実装（Phase 1 残り）
- [ ] 1局→半荘（東風戦・東南戦）の進行管理
