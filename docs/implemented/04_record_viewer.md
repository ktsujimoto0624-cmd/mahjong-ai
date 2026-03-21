# 04. 棋譜記録・HTMLビューア

## 概要
1局の全アクションを記録し、ブラウザで視覚的にステップ再生できる。

## 棋譜記録 (`record.py`)

### 記録されるアクション

| type | 内容 | フィールド |
|------|------|-----------|
| `draw` | ツモ | seat, tile |
| `discard` | 打牌 | seat, tile, riichi |
| `riichi` | リーチ宣言 | seat |
| `meld` | 鳴き | seat, meld_type, tiles, from_seat, taken_tile |

### meld_type の種類
- `chi` — チー（順子、下家のみ）
- `pon` — ポン
- `daiminkan` — 大明槓
- `ankan` — 暗槓
- `kakan` — 加槓

### 出力形式
- **JSON**: `save_json(filepath)` / `load_json(filepath)`
- **テキスト**: `to_text()` — 人間が読める棋譜

### 結果情報
```python
{
    "type": "tsumo" | "ron" | "ryukyoku",
    "winner": 席番号 | None,
    "turn": 巡目,
    "winning_tile": 和了牌ID,
    "score": {                    # 点数計算結果
        "yaku": [(役名, 翻数), ...],
        "han": 翻数,
        "fu": 符,
        "payments": { "total": 点数, ... },
    },
}
```

## HTMLビューア (`viewer.py`, `viewer_css.py`, `viewer_js.py`)

### レイアウト
実際の麻雀卓を上から見た配置。

```
        ── 西家(seat2) 手牌 ──
       |                       |
 北家  |    西河  中央  南河    | 南家
(seat3)|    北河  情報  東河    |(seat1)
 手牌  |                       | 手牌
       |                       |
        ── 東家(seat0) 手牌 ──
```

- **seat 0** = 東家（下、自分視点）
- **seat 1** = 南家（右、牌を-90°回転）
- **seat 2** = 西家（上、牌を180°回転）
- **seat 3** = 北家（左、牌を90°回転）

### 操作
| 操作 | ボタン / キー |
|------|--------------|
| 1手進む | 「進む >」/ → |
| 1手戻る | 「< 戻る」/ ← |
| 最初へ | 「\|<」/ Home |
| 最後へ | 「>\|」/ End |
| 自動再生 | 「自動再生」/ Space |

### 表示機能
- **ツモ牌ハイライト**: 黄色のグロー効果
- **最終捨て牌ハイライト**: 赤のグロー効果
- **リーチ宣言牌**: 横向き表示
- **リーチマーク**: プレイヤー名の横に赤字「リーチ」
- **副露表示**: 手牌エリアの右側に表示、鳴いた牌は緑背景
- **アクティブプレイヤー**: 黄色ボーダー
- **和了者**: 赤ボーダー
- **結果バナー**: 和了/流局の詳細情報

### ファイル構成
ビューアは500行制限のため3ファイルに分割。

| ファイル | 行数 | 内容 |
|----------|------|------|
| `viewer.py` | ~95 | HTMLテンプレート・generate_html() |
| `viewer_css.py` | ~217 | 全CSSスタイル |
| `viewer_js.py` | ~305 | 状態管理・描画・操作 |

### 牌画像
FluffyStuff/riichi-mahjong-tiles (SVG, CC-BY) を使用。
`assets/tiles/` に配置、HTMLからは相対パスで参照。

### GitHub Pages
`output/sample_record.html` を GitHub Pages で公開。
https://ktsujimoto0624-cmd.github.io/mahjong-ai/sample_record.html
