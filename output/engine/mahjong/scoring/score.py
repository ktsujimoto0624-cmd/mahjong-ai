"""
点数計算

役判定の結果（翻数）と符計算から最終的な点数を算出する。
"""

import math
from mahjong.engine.tile import (
    SANGENPAI, KAZEHAI, is_suit, is_honor,
    is_terminal, is_terminal_or_honor,
)
from mahjong.engine.agari import decompose_regular, _check_seven_pairs
from mahjong.scoring.yaku import judge_yaku


def calculate_score(win_info):
    """
    和了の点数を計算する。

    Args:
        win_info: 和了情報（yaku.judge_yaku と同じ）

    Returns:
        dict: {
            "yaku": [(役名, 翻数), ...],
            "han": 翻数,
            "fu": 符,
            "base_points": 基本点,
            "payments": 支払い情報,
            "is_yakuman": bool,
        }
    """
    yaku_list, han, decomp = judge_yaku(win_info)

    if not yaku_list:
        return None  # 役なし（和了不成立）

    is_yakuman = (han == -1)

    if is_yakuman:
        base_points = 8000  # 役満
        fu = 0
    else:
        fu = _calculate_fu(win_info, decomp, yaku_list)
        base_points = _han_fu_to_base(han, fu)

    payments = _calculate_payments(
        base_points, win_info["is_tsumo"],
        is_dealer=(win_info["seat_wind"] == 0),
    )

    return {
        "yaku": yaku_list,
        "han": 13 if is_yakuman else han,
        "fu": fu,
        "base_points": base_points,
        "payments": payments,
        "is_yakuman": is_yakuman,
    }


def _calculate_fu(win_info, decomp, yaku_list):
    """
    符を計算する。

    符の構成:
    - 副底: 30符（門前ロン）、20符（ツモ or 鳴き）
    - 面子: 刻子/槓子の種類に応じて加算
    - 雀頭: 役牌なら2符
    - 待ち: 嵌張/辺張/単騎は2符
    - ツモ: 2符（平和ツモは除く）
    """
    yaku_names = [name for name, _ in yaku_list]
    is_menzen = win_info["is_menzen"]
    is_tsumo = win_info["is_tsumo"]

    # 七対子は固定25符
    if "七対子" in yaku_names:
        return 25

    # 平和ツモは固定20符
    if "平和" in yaku_names and is_tsumo:
        return 20

    # 副底
    if is_menzen and not is_tsumo:
        fu = 30  # 門前ロン
    else:
        fu = 20  # ツモ or 鳴きロン

    if decomp is None:
        return _round_up_fu(fu)

    # 面子の符
    fu += _mentsu_fu(win_info, decomp)

    # 雀頭の符
    fu += _head_fu(win_info, decomp["head"])

    # 待ちの符
    fu += _machi_fu(win_info, decomp)

    # ツモ符（平和以外）
    if is_tsumo and "平和" not in yaku_names:
        fu += 2

    # 10の位に切り上げ
    fu = _round_up_fu(fu)

    # 鳴きロンの最低30符
    if not is_menzen and not is_tsumo and fu < 30:
        fu = 30

    return fu


def _mentsu_fu(win_info, decomp):
    """面子による符"""
    fu = 0
    wt = win_info["winning_tile"]
    is_tsumo = win_info["is_tsumo"]

    # 手牌の面子
    for mt, tile in decomp["mentsu"]:
        if mt == "koutsu":
            is_ankou = is_tsumo or tile != wt
            base = 4 if is_ankou else 2
            if is_terminal_or_honor(tile):
                base *= 2
            fu += base

    # 副露の面子
    for m in win_info["melds"]:
        mtype = m["type"]
        tile = m["tiles"][0]
        if mtype == "pon":
            base = 2  # 明刻
            if is_terminal_or_honor(tile):
                base *= 2
            fu += base
        elif mtype == "ankan":
            base = 16  # 暗槓
            if is_terminal_or_honor(tile):
                base *= 2
            fu += base
        elif mtype in ("daiminkan", "kakan"):
            base = 8  # 明槓
            if is_terminal_or_honor(tile):
                base *= 2
            fu += base

    return fu


def _head_fu(win_info, head):
    """雀頭による符"""
    fu = 0
    if head in SANGENPAI:
        fu += 2
    seat_wind_tile = KAZEHAI[win_info["seat_wind"]]
    round_wind_tile = KAZEHAI[win_info["round_wind"]]
    if head == seat_wind_tile:
        fu += 2
    if head == round_wind_tile:
        fu += 2
    return fu


def _machi_fu(win_info, decomp):
    """待ちの形による符"""
    wt = win_info["winning_tile"]
    head = decomp["head"]

    # 単騎待ち
    if wt == head:
        return 2

    for mt, start in decomp["mentsu"]:
        if mt != "shuntsu":
            continue
        if wt == start + 1:
            return 2  # 嵌張待ち
        if wt == start and (start % 9) == 6:
            return 2  # 辺張（789の7待ち）
        if wt == start + 2 and (start % 9) == 0:
            return 2  # 辺張（123の3待ち）

    return 0  # 両面待ち


def _round_up_fu(fu):
    """10の位に切り上げ"""
    return math.ceil(fu / 10) * 10


def _han_fu_to_base(han, fu):
    """翻と符から基本点を計算"""
    if han >= 13:
        return 8000  # 数え役満
    if han >= 11:
        return 6000  # 三倍満
    if han >= 8:
        return 4000  # 倍満
    if han >= 6:
        return 3000  # 跳満
    if han >= 5:
        return 2000  # 満貫

    # 基本点 = 符 × 2^(翻+2)
    base = fu * (2 ** (han + 2))
    if base >= 2000:
        return 2000

    return base


def _calculate_payments(base_points, is_tsumo, is_dealer):
    """
    支払い点数を計算する。

    Returns:
        dict with total, from_each_non_dealer, from_dealer, from_discarder
    """
    if is_tsumo:
        if is_dealer:
            each = _round_up_100(base_points * 2)
            return {
                "total": each * 3,
                "from_each_non_dealer": each,
                "from_dealer": 0,
                "from_discarder": 0,
            }
        else:
            from_dealer = _round_up_100(base_points * 2)
            from_non_dealer = _round_up_100(base_points)
            return {
                "total": from_dealer + from_non_dealer * 2,
                "from_each_non_dealer": from_non_dealer,
                "from_dealer": from_dealer,
                "from_discarder": 0,
            }
    else:
        if is_dealer:
            total = _round_up_100(base_points * 6)
        else:
            total = _round_up_100(base_points * 4)
        return {
            "total": total,
            "from_each_non_dealer": 0,
            "from_dealer": 0,
            "from_discarder": total,
        }


def _round_up_100(points):
    """100点単位に切り上げ"""
    return math.ceil(points / 100) * 100
