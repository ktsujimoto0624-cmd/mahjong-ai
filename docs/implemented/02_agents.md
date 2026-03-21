# 02. AIエージェント

## 概要
AIの意思決定インターフェースと、2種類のエージェント実装。

## エージェント基底クラス (`agent.py: AgentBase`)

全エージェントが実装すべきインターフェース。

### 打牌系
| メソッド | 説明 | デフォルト |
|----------|------|-----------|
| `choose_discard(player, game_state)` | 何を捨てるか | 未実装（必須） |
| `choose_discard_riichi(player, game_state)` | リーチ宣言時の打牌 | `choose_discard` と同じ |

### リーチ・和了系
| メソッド | 説明 | デフォルト |
|----------|------|-----------|
| `choose_riichi(player, game_state)` | リーチするか | 常にリーチ |
| `choose_ron(player, tile, from_seat, game_state)` | ロンするか | 常にロン |

### 鳴き系
| メソッド | 説明 | デフォルト |
|----------|------|-----------|
| `choose_pon(player, tile, from_seat, game_state)` | ポンするか | しない |
| `choose_chi(player, tile, from_seat, game_state)` | チーするか（手牌2枚のリストを返す） | しない |
| `choose_kan(player, tile, from_seat, game_state)` | 大明槓するか | しない |
| `choose_ankan(player, game_state)` | 暗槓するか（牌IDを返す） | しない |
| `choose_kakan(player, game_state)` | 加槓するか（牌IDを返す） | しない |

### game_state の内容
```python
{
    "turn": 巡目,
    "current_player": 現在のプレイヤー席番号,
    "discards": [4人分の捨て牌リスト],
    "remaining_tiles": 山の残り枚数,
    "dora_indicators": ドラ表示牌リスト,
    "riichi": [4人分のリーチ状態],
    "melds": [4人分の副露リスト],
}
```

## RandomAgent

手牌からランダムに1枚捨てる。動作確認用。鳴きはしない。

## ShantenAgent

シャンテン数ベースの戦略エージェント。

### 打牌戦略
1. 各牌を仮に捨てて、シャンテン数が最小になる牌を選ぶ
2. 同じシャンテン数なら、受入枚数（有効牌の種類数）が多い方を選ぶ
3. それでも同じならランダム

### 鳴き戦略
- **ポン**: 鳴いた後にシャンテン数が下がるなら鳴く
- **チー**: 鳴いた後にシャンテン数が下がる組み合わせがあれば鳴く（最善の組を選択）
- **暗槓**: 4枚揃っていたら暗槓する（リーチ中は除く）
- **加槓**: ポンした牌の4枚目があれば加槓する（リーチ中は除く）

### リーチ戦略
- テンパイかつ門前なら常にリーチ
- リーチ時は受入枚数が最大になる打牌を選ぶ
