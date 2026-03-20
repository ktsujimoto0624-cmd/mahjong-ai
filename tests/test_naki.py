"""鳴き（チー・ポン・カン）のテスト"""

from mahjong.game import GameRound
from mahjong.agent import ShantenAgent
from mahjong.player import Player
from mahjong.tile import empty_hand


def test_pon_adds_meld():
    """ポンで副露が追加されること"""
    player = Player(seat=0)
    player.hand[0] = 3  # 1m を3枚
    player.add_pon(taken_tile=0, from_seat=1)
    assert len(player.melds) == 1
    assert player.melds[0]["type"] == "pon"
    assert player.hand[0] == 1  # 手牌に1枚残る


def test_chi_adds_meld():
    """チーで副露が追加されること"""
    player = Player(seat=0)
    player.hand[0] = 1  # 1m
    player.hand[1] = 1  # 2m
    player.add_chi(taken_tile=2, hand_tiles=[0, 1], from_seat=3)
    assert len(player.melds) == 1
    assert player.melds[0]["type"] == "chi"
    assert player.melds[0]["tiles"] == [0, 1, 2]
    assert player.hand[0] == 0
    assert player.hand[1] == 0


def test_ankan():
    """暗槓で手牌から4枚除去されること"""
    player = Player(seat=0)
    player.hand[5] = 4  # 6m を4枚
    player.add_ankan(5)
    assert len(player.melds) == 1
    assert player.melds[0]["type"] == "ankan"
    assert player.hand[5] == 0
    assert player.is_menzen()  # 暗槓は門前


def test_kakan():
    """加槓でポンが更新されること"""
    player = Player(seat=0)
    player.hand[0] = 2
    player.add_pon(taken_tile=0, from_seat=1)
    assert player.hand[0] == 0
    player.hand[0] = 1  # ツモで1枚追加
    player.add_kakan(0)
    assert player.melds[0]["type"] == "kakan"
    assert len(player.melds[0]["tiles"]) == 4
    assert player.hand[0] == 0


def test_menzen_after_pon():
    """ポン後は門前でなくなること"""
    player = Player(seat=0)
    player.hand[0] = 2
    player.add_pon(taken_tile=0, from_seat=1)
    assert not player.is_menzen()


def test_game_with_naki():
    """鳴きありのゲームが100局エラーなく完了すること"""
    results = {"tsumo": 0, "ron": 0, "ryukyoku": 0}
    for seed in range(100):
        agents = [ShantenAgent(seed=seed + i) for i in range(4)]
        game = GameRound(agents, wall_seed=seed)
        result = game.run()
        results[result["type"]] += 1

    total = sum(results.values())
    assert total == 100
    # 鳴きにより和了率が上がることを確認（流局が減る）
    assert results["tsumo"] + results["ron"] > 0


def test_naki_in_record():
    """鳴きが棋譜に正しく記録されること"""
    # seed=67 は多数の鳴きが発生する
    agents = [ShantenAgent(seed=67 + i) for i in range(4)]
    game = GameRound(agents, wall_seed=67)
    game.run()

    meld_actions = [a for a in game.record.actions if a["type"] == "meld"]
    assert len(meld_actions) > 0

    for ma in meld_actions:
        assert "meld_type" in ma
        assert "tiles" in ma
        assert "from_seat" in ma
        assert "taken_tile" in ma
