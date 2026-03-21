"""点数計算のテスト"""

from mahjong.tile import empty_hand, dora_from_indicator
from mahjong.yaku import judge_yaku
from mahjong.score import calculate_score


def _make_win_info(hand, winning_tile, **kwargs):
    """テスト用の win_info を構築"""
    defaults = {
        "hand": hand,
        "melds": [],
        "winning_tile": winning_tile,
        "is_tsumo": False,
        "is_riichi": False,
        "seat_wind": 1,   # 南家（子）
        "round_wind": 0,  # 東場
        "is_menzen": True,
    }
    defaults.update(kwargs)
    return defaults


def test_riichi_tsumo():
    """リーチ+門前清自摸和"""
    hand = empty_hand()
    # 1m2m3m 4m5m6m 7m8m9m 1p2p3p + 5p5p (雀頭)  = 14枚
    for t in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
        hand[t] = 1
    hand[9] = 1   # 1p
    hand[10] = 1  # 2p
    hand[11] = 1  # 3p
    hand[13] = 2  # 5p×2 (雀頭)
    wi = _make_win_info(hand, 11, is_tsumo=True, is_riichi=True)
    score = calculate_score(wi)
    assert score is not None
    names = [n for n, _ in score["yaku"]]
    assert "リーチ" in names
    assert "門前清自摸和" in names


def test_pinfu():
    """平和"""
    hand = empty_hand()
    # 1m2m3m 4p5p6p 7s8s9s 2m3m4m + 5m5m(雀頭)
    hand[0] = 1  # 1m
    hand[1] = 2  # 2m×2
    hand[2] = 2  # 3m×2
    hand[3] = 1  # 4m
    hand[4] = 1  # 5m (雀頭)×2→下で調整
    hand[4] = 2  # 5m×2 雀頭
    hand[12] = 1  # 4p
    hand[13] = 1  # 5p
    hand[14] = 1  # 6p
    hand[24] = 1  # 7s
    hand[25] = 1  # 8s
    hand[26] = 1  # 9s
    # 両面待ちで1mロン
    wi = _make_win_info(hand, 0, is_riichi=True)
    score = calculate_score(wi)
    assert score is not None
    names = [n for n, _ in score["yaku"]]
    assert "リーチ" in names


def test_tanyao():
    """断么九"""
    hand = empty_hand()
    # 2m3m4m 5m6m7m 3p4p5p 6s7s8s + 5p5p
    hand[1] = 1  # 2m
    hand[2] = 1  # 3m
    hand[3] = 1  # 4m
    hand[4] = 1  # 5m
    hand[5] = 1  # 6m
    hand[6] = 1  # 7m
    hand[11] = 1  # 3p
    hand[12] = 1  # 4p
    hand[13] = 3  # 5p (1+2=雀頭)
    hand[23] = 1  # 6s
    hand[24] = 1  # 7s
    hand[25] = 1  # 8s
    wi = _make_win_info(hand, 1, is_riichi=True)
    score = calculate_score(wi)
    assert score is not None
    names = [n for n, _ in score["yaku"]]
    assert "断么九" in names


def test_yakuhai():
    """役牌（白）"""
    hand = empty_hand()
    # 1m2m3m 4p5p6p 7s8s9s + 白白白 + 2m2m(雀頭)
    hand[0] = 1  # 1m
    hand[1] = 3  # 2m (1+2=雀頭)
    hand[2] = 1  # 3m
    hand[12] = 1  # 4p
    hand[13] = 1  # 5p
    hand[14] = 1  # 6p
    hand[24] = 1  # 7s
    hand[25] = 1  # 8s
    hand[26] = 1  # 9s
    hand[31] = 3  # 白×3
    wi = _make_win_info(hand, 31, is_riichi=False)
    score = calculate_score(wi)
    assert score is not None
    names = [n for n, _ in score["yaku"]]
    assert "役牌 白" in names


def test_chitoitsu():
    """七対子"""
    hand = empty_hand()
    # 7種×2枚
    for t in [0, 4, 9, 13, 18, 22, 27]:
        hand[t] = 2
    wi = _make_win_info(hand, 0, is_riichi=True)
    score = calculate_score(wi)
    assert score is not None
    names = [n for n, _ in score["yaku"]]
    assert "七対子" in names
    assert score["fu"] == 25


def test_toitoi():
    """対々和（ポン×2 + 手牌暗刻×2 + 雀頭）"""
    hand = empty_hand()
    hand[0] = 3  # 1m×3
    hand[9] = 3  # 1p×3
    hand[27] = 2  # 東×2 (雀頭)
    melds = [
        {"type": "pon", "tiles": [18, 18, 18], "from": 0},
        {"type": "pon", "tiles": [31, 31, 31], "from": 2},
    ]
    wi = _make_win_info(
        hand, 0, melds=melds, is_menzen=False, is_riichi=False,
    )
    score = calculate_score(wi)
    assert score is not None
    names = [n for n, _ in score["yaku"]]
    assert "対々和" in names
    assert "役牌 白" in names


def test_kokushi():
    """国士無双（役満）"""
    hand = empty_hand()
    kokushi = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
    for t in kokushi:
        hand[t] = 1
    hand[0] = 2  # 1m が雀頭
    wi = _make_win_info(hand, 33, is_riichi=False)
    score = calculate_score(wi)
    assert score is not None
    assert score["is_yakuman"]
    names = [n for n, _ in score["yaku"]]
    assert "国士無双" in names


def test_dora_from_indicator():
    """ドラ表示牌→ドラ牌の変換"""
    assert dora_from_indicator(0) == 1    # 1m → 2m
    assert dora_from_indicator(8) == 0    # 9m → 1m
    assert dora_from_indicator(27) == 28  # 東 → 南
    assert dora_from_indicator(30) == 27  # 北 → 東
    assert dora_from_indicator(31) == 32  # 白 → 發
    assert dora_from_indicator(33) == 31  # 中 → 白


def test_fu_calculation():
    """符計算の基本"""
    hand = empty_hand()
    # 1m1m1m 2p3p4p 5s6s7s 東東東 + 白白(雀頭)
    hand[0] = 3   # 1m×3 (暗刻)
    hand[10] = 1  # 2p
    hand[11] = 1  # 3p
    hand[12] = 1  # 4p
    hand[22] = 1  # 5s
    hand[23] = 1  # 6s
    hand[24] = 1  # 7s
    hand[27] = 3  # 東×3 (暗刻)
    hand[31] = 2  # 白×2 (雀頭)
    wi = _make_win_info(hand, 10, is_tsumo=False, is_riichi=True)
    score = calculate_score(wi)
    assert score is not None
    # 副底30 + 1m暗刻(8=4*2 端牌) + 東暗刻(8=4*2 字牌) + 白雀頭(2) = 48 → 50符
    assert score["fu"] == 50


def test_game_scoring():
    """ゲーム統合: 100局エラーなし"""
    from mahjong.game import GameRound
    from mahjong.agent import ShantenAgent

    scored = 0
    for seed in range(100):
        agents = [ShantenAgent(seed=seed + i) for i in range(4)]
        game = GameRound(agents, wall_seed=seed)
        result = game.run()
        if result.get("score") is not None:
            scored += 1
            assert result["score"]["payments"]["total"] > 0

    assert scored > 0
