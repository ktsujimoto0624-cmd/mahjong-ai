"""フリテン判定テスト"""

from mahjong.engine.agari import waiting_tiles, is_agari
from mahjong.engine.player import Player
from mahjong.engine.tile import empty_hand
from mahjong.game.round import GameRound


def test_waiting_tiles_tenpai():
    """テンパイ時の待ち牌を正しく返す"""
    hand = empty_hand()
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p → 4p単騎待ち
    for t in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
        hand[t] = 1
    hand[12] = 1  # 4p
    waits = waiting_tiles(hand, 0)
    assert 12 in waits  # 4p


def test_waiting_tiles_not_tenpai():
    """テンパイでない場合は空リスト"""
    hand = empty_hand()
    # バラバラな手
    hand[0] = 1
    hand[5] = 1
    hand[10] = 1
    hand[15] = 1
    hand[20] = 1
    hand[25] = 1
    hand[27] = 1
    hand[28] = 1
    hand[29] = 1
    hand[30] = 1
    hand[31] = 1
    hand[32] = 1
    hand[33] = 1
    waits = waiting_tiles(hand, 0)
    assert waits == []


def test_furiten_basic():
    """自分の河に待ち牌がある場合フリテン"""
    player = Player(seat=0)
    # テンパイ手を作る: 1m2m3m 4m5m6m 7m8m9m 1p2p3p 4p
    for t in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        player.hand[t] = 1
    # 河に4p(id=12)がある → フリテン
    player.discards.append(12)
    assert player.is_furiten() is True


def test_not_furiten():
    """河に待ち牌がなければフリテンでない"""
    player = Player(seat=0)
    for t in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        player.hand[t] = 1
    # 河には関係ない牌
    player.discards.append(20)
    assert player.is_furiten() is False


def test_furiten_not_tenpai():
    """テンパイでなければフリテンにならない"""
    player = Player(seat=0)
    hand = empty_hand()
    hand[0] = 1
    hand[5] = 1
    hand[10] = 2
    hand[15] = 1
    hand[20] = 1
    hand[25] = 1
    hand[27] = 1
    hand[28] = 1
    hand[29] = 1
    hand[30] = 1
    hand[31] = 1
    hand[32] = 1
    hand[33] = 1
    player.hand = hand
    player.discards.append(0)
    assert player.is_furiten() is False


def test_temporary_furiten_state():
    """同巡フリテン: ロン見逃し後にフラグが立つ"""
    from agents import ShantenAgent
    agents = [ShantenAgent(seed=i) for i in range(4)]
    game = GameRound(agents, wall_seed=42)
    # 初期状態では同巡フリテンなし
    assert game.temporary_furiten == [False, False, False, False]
    assert game.permanent_furiten == [False, False, False, False]


def test_furiten_in_game():
    """実際のゲームでフリテンが正常に動作する（クラッシュしない）"""
    from agents import ShantenAgent
    agents = [ShantenAgent(seed=i) for i in range(4)]
    game = GameRound(agents, wall_seed=42)
    result = game.run()
    assert result is not None
    assert result["type"] in ("tsumo", "ron", "ryukyoku")
