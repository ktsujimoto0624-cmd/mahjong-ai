"""
役判定

和了した手牌に含まれる役を判定し、翻数を返す。
WinInfo（和了情報）を受け取り、成立する役のリストを返す。
"""

from mahjong.tile import (
    NUM_TILE_TYPES, HONOR_START, SANGENPAI, KAZEHAI,
    TON, NAN, SHA, PEI, HAKU, HATSU, CHUN,
    is_suit, is_honor, is_terminal, is_terminal_or_honor,
)
from mahjong.agari import decompose_regular, _check_seven_pairs, _check_kokushi


def judge_yaku(win_info):
    """
    和了情報から成立する役を判定する。

    Args:
        win_info: dict with keys:
            hand: カウント配列（和了牌含む14枚状態）
            melds: 副露リスト [{"type": str, "tiles": [...], "from": int|None}]
            winning_tile: 和了牌ID
            is_tsumo: ツモ和了か
            is_riichi: リーチしていたか
            seat_wind: 自風 (0=東,1=南,2=西,3=北)
            round_wind: 場風 (0=東,1=南,2=西,3=北)
            is_menzen: 門前かどうか

    Returns:
        最高得点の(役リスト, 翻数, 分解パターン)
        役リスト: [(役名, 翻数), ...]
    """
    hand = win_info["hand"]
    melds = win_info["melds"]
    is_menzen = win_info["is_menzen"]

    # 役満チェック
    yakuman = _check_yakuman(win_info)
    if yakuman:
        return yakuman, -1, None  # -1 は役満を示す

    # 七対子
    if len(melds) == 0 and _check_seven_pairs(hand):
        yaku_list = _judge_common_yaku(win_info, None, is_chitoitsu=True)
        yaku_list.append(("七対子", 2))
        total_han = sum(h for _, h in yaku_list)
        return yaku_list, total_han, None

    # 通常形: 全分解パターンから最高得点を選ぶ
    melds_count = len(melds)
    decompositions = decompose_regular(hand, melds_count)

    best_yaku = []
    best_han = 0
    best_decomp = None

    for decomp in decompositions:
        yaku_list = _judge_regular_yaku(win_info, decomp)
        total_han = sum(h for _, h in yaku_list)
        if total_han > best_han:
            best_han = total_han
            best_yaku = yaku_list
            best_decomp = decomp

    return best_yaku, best_han, best_decomp


def _judge_regular_yaku(win_info, decomp):
    """通常形（4面子1雀頭）の役判定"""
    yaku_list = _judge_common_yaku(win_info, decomp)
    head = decomp["head"]
    mentsu = decomp["mentsu"]
    melds = win_info["melds"]
    is_menzen = win_info["is_menzen"]
    winning_tile = win_info["winning_tile"]

    # 全面子（手牌+副露）を統合
    all_mentsu = list(mentsu)
    for m in melds:
        mt = m["type"]
        tile = m["tiles"][0]
        if mt in ("pon", "daiminkan", "kakan"):
            all_mentsu.append(("koutsu", tile))
        elif mt == "ankan":
            all_mentsu.append(("koutsu", tile))
        elif mt == "chi":
            all_mentsu.append(("shuntsu", min(m["tiles"])))

    # 平和（門前のみ）
    if is_menzen and _is_pinfu(win_info, decomp):
        yaku_list.append(("平和", 1))

    # 一盃口（門前のみ）
    if is_menzen:
        iipeikou_count = _count_same_shuntsu(mentsu)
        if iipeikou_count == 1:
            yaku_list.append(("一盃口", 1))
        elif iipeikou_count == 2:
            yaku_list.append(("二盃口", 3))

    # 役牌
    _check_yakuhai(yaku_list, all_mentsu, win_info)

    # 断么九
    if _is_tanyao(win_info, head, all_mentsu):
        yaku_list.append(("断么九", 1))

    # 対々和
    if _is_toitoi(all_mentsu):
        yaku_list.append(("対々和", 2))

    # 三暗刻
    if _count_ankou(win_info, decomp) >= 3:
        yaku_list.append(("三暗刻", 2))

    # 混全帯么九
    if _is_chanta(head, all_mentsu):
        han = 2 if is_menzen else 1
        yaku_list.append(("混全帯么九", han))

    # 純全帯么九
    if _is_junchan(head, all_mentsu):
        han = 3 if is_menzen else 2
        # 純チャンがあれば混チャンを除外
        yaku_list = [(n, h) for n, h in yaku_list if n != "混全帯么九"]
        yaku_list.append(("純全帯么九", han))

    # 混一色
    if _is_honitsu(head, all_mentsu):
        han = 3 if is_menzen else 2
        yaku_list.append(("混一色", han))

    # 清一色
    if _is_chinitsu(head, all_mentsu):
        han = 6 if is_menzen else 5
        # 清一色があれば混一色を除外
        yaku_list = [(n, h) for n, h in yaku_list if n != "混一色"]
        yaku_list.append(("清一色", han))

    # 三色同順
    if _is_sanshoku(all_mentsu):
        han = 2 if is_menzen else 1
        yaku_list.append(("三色同順", han))

    # 一気通貫
    if _is_ikkitsuu(all_mentsu):
        han = 2 if is_menzen else 1
        yaku_list.append(("一気通貫", han))

    # 三色同刻
    if _is_sanshoku_doukou(all_mentsu):
        yaku_list.append(("三色同刻", 2))

    # 小三元
    if _is_shousangen(head, all_mentsu):
        yaku_list.append(("小三元", 2))

    return yaku_list


def _judge_common_yaku(win_info, decomp, is_chitoitsu=False):
    """分解パターンに依存しない共通役"""
    yaku_list = []
    is_menzen = win_info["is_menzen"]
    is_tsumo = win_info["is_tsumo"]

    # リーチ（門前のみ）
    if win_info["is_riichi"]:
        yaku_list.append(("リーチ", 1))

    # 門前清自摸和（門前ツモ）
    if is_menzen and is_tsumo:
        yaku_list.append(("門前清自摸和", 1))

    return yaku_list


# === 個別役判定 ===

def _is_pinfu(win_info, decomp):
    """平和: 全て順子、雀頭が役牌でない、両面待ち"""
    head = decomp["head"]
    mentsu = decomp["mentsu"]

    # 全て順子か
    if any(mt != "shuntsu" for mt, _ in mentsu):
        return False

    # 雀頭が役牌でないか
    seat_wind_tile = KAZEHAI[win_info["seat_wind"]]
    round_wind_tile = KAZEHAI[win_info["round_wind"]]
    if head in SANGENPAI or head == seat_wind_tile or head == round_wind_tile:
        return False

    # 両面待ちか（和了牌が順子の端でないチェック）
    wt = win_info["winning_tile"]
    for mt, start in mentsu:
        if mt == "shuntsu":
            # wt == start: 辺張or両面の下側
            # wt == start+2: 辺張or両面の上側
            # wt == start+1: 嵌張
            if wt == start + 1:
                continue  # 嵌張はNG
            if wt == start and (start % 9) == 6:
                continue  # 7-8-9の辺張
            if wt == start + 2 and (start % 9) == 0:
                continue  # 1-2-3の辺張
            if wt == start or wt == start + 2:
                return True  # 両面待ち

    return False


def _check_yakuhai(yaku_list, all_mentsu, win_info):
    """役牌判定（三元牌・場風・自風）"""
    seat_wind_tile = KAZEHAI[win_info["seat_wind"]]
    round_wind_tile = KAZEHAI[win_info["round_wind"]]

    for mt, tile in all_mentsu:
        if mt != "koutsu":
            continue
        if tile == HAKU:
            yaku_list.append(("役牌 白", 1))
        elif tile == HATSU:
            yaku_list.append(("役牌 發", 1))
        elif tile == CHUN:
            yaku_list.append(("役牌 中", 1))
        if tile == round_wind_tile:
            yaku_list.append(("場風牌", 1))
        if tile == seat_wind_tile:
            yaku_list.append(("自風牌", 1))


def _is_tanyao(win_info, head, all_mentsu):
    """断么九: 全ての牌が中張牌(2-8)"""
    if is_terminal_or_honor(head):
        return False
    for mt, tile in all_mentsu:
        if mt == "koutsu":
            if is_terminal_or_honor(tile):
                return False
        elif mt == "shuntsu":
            if (tile % 9) == 0 or (tile % 9) == 6:
                return False
    return True


def _is_toitoi(all_mentsu):
    """対々和: 全て刻子"""
    return all(mt == "koutsu" for mt, _ in all_mentsu)


def _count_ankou(win_info, decomp):
    """暗刻の数を数える"""
    count = 0
    wt = win_info["winning_tile"]
    is_tsumo = win_info["is_tsumo"]

    for mt, tile in decomp["mentsu"]:
        if mt == "koutsu":
            # ロン和了で和了牌がこの刻子の牌なら明刻扱い
            if not is_tsumo and tile == wt:
                continue
            count += 1

    # 副露の暗槓も暗刻として数える
    for m in win_info["melds"]:
        if m["type"] == "ankan":
            count += 1

    return count


def _count_same_shuntsu(mentsu):
    """同じ順子の対(一盃口/二盃口)を数える"""
    shuntsu = [t for mt, t in mentsu if mt == "shuntsu"]
    count = 0
    used = [False] * len(shuntsu)
    for i in range(len(shuntsu)):
        if used[i]:
            continue
        for j in range(i + 1, len(shuntsu)):
            if not used[j] and shuntsu[i] == shuntsu[j]:
                count += 1
                used[i] = True
                used[j] = True
                break
    return count


def _is_chanta(head, all_mentsu):
    """混全帯么九: 全てのグループに么九牌を含む"""
    if not is_terminal_or_honor(head):
        return False
    has_honor = is_honor(head)
    has_shuntsu = False
    for mt, tile in all_mentsu:
        if mt == "koutsu":
            if not is_terminal_or_honor(tile):
                return False
            if is_honor(tile):
                has_honor = True
        elif mt == "shuntsu":
            has_shuntsu = True
            if (tile % 9) != 0 and (tile % 9) != 6:
                return False
    # 字牌を含まないなら純チャン（混チャンではない）
    return has_honor and has_shuntsu


def _is_junchan(head, all_mentsu):
    """純全帯么九: 全てのグループに老頭牌を含む（字牌なし）"""
    if not is_terminal(head):
        return False
    has_shuntsu = False
    for mt, tile in all_mentsu:
        if mt == "koutsu":
            if not is_terminal(tile):
                return False
        elif mt == "shuntsu":
            has_shuntsu = True
            if (tile % 9) != 0 and (tile % 9) != 6:
                return False
    return has_shuntsu


def _is_honitsu(head, all_mentsu):
    """混一色: 一種類の数牌+字牌のみ"""
    suits = set()
    has_honor = False
    tiles_to_check = [head]
    for mt, tile in all_mentsu:
        tiles_to_check.append(tile)

    for tile in tiles_to_check:
        if is_honor(tile):
            has_honor = True
        elif tile < 9:
            suits.add("m")
        elif tile < 18:
            suits.add("p")
        else:
            suits.add("s")

    return len(suits) == 1 and has_honor


def _is_chinitsu(head, all_mentsu):
    """清一色: 一種類の数牌のみ"""
    if is_honor(head):
        return False
    suit_start = (head // 9) * 9
    for mt, tile in all_mentsu:
        if is_honor(tile):
            return False
        if (tile // 9) * 9 != suit_start:
            return False
    return True


def _is_sanshoku(all_mentsu):
    """三色同順: 同じ数字の順子が3色"""
    shuntsu = [t for mt, t in all_mentsu if mt == "shuntsu"]
    for s in shuntsu:
        num = s % 9
        if num in [t % 9 for t in shuntsu if t // 9 == 0] and \
           num in [t % 9 for t in shuntsu if t // 9 == 1] and \
           num in [t % 9 for t in shuntsu if t // 9 == 2]:
            return True
    return False


def _is_ikkitsuu(all_mentsu):
    """一気通貫: 同色の1-2-3, 4-5-6, 7-8-9"""
    shuntsu = set(t for mt, t in all_mentsu if mt == "shuntsu")
    for base in (0, 9, 18):
        if base in shuntsu and (base + 3) in shuntsu and (base + 6) in shuntsu:
            return True
    return False


def _is_sanshoku_doukou(all_mentsu):
    """三色同刻: 同じ数字の刻子が3色"""
    koutsu = [t for mt, t in all_mentsu if mt == "koutsu" and is_suit(t)]
    for k in koutsu:
        num = k % 9
        suits = set((t // 9) for t in koutsu if t % 9 == num)
        if len(suits) >= 3:
            return True
    return False


def _is_shousangen(head, all_mentsu):
    """小三元: 三元牌のうち2つが刻子、1つが雀頭"""
    san_koutsu = sum(1 for mt, t in all_mentsu if mt == "koutsu" and t in SANGENPAI)
    return san_koutsu == 2 and head in SANGENPAI


# === 役満 ===

def _check_yakuman(win_info):
    """役満のチェック"""
    hand = win_info["hand"]
    melds = win_info["melds"]
    is_menzen = win_info["is_menzen"]
    yakuman = []

    # 国士無双
    if is_menzen and _check_kokushi(hand):
        yakuman.append(("国士無双", 13))
        return yakuman

    # 四暗刻（門前のみ）
    if is_menzen:
        decompositions = decompose_regular(hand, 0)
        for decomp in decompositions:
            ankou = _count_ankou(win_info, decomp)
            if ankou >= 4:
                yakuman.append(("四暗刻", 13))
                return yakuman

    # 大三元
    melds_count = len(melds)
    decompositions = decompose_regular(hand, melds_count)
    for decomp in decompositions:
        all_mentsu = _build_all_mentsu(decomp, melds)
        san_koutsu = sum(
            1 for mt, t in all_mentsu if mt == "koutsu" and t in SANGENPAI
        )
        if san_koutsu == 3:
            yakuman.append(("大三元", 13))
            return yakuman

    # 字一色
    all_tiles = list(range(NUM_TILE_TYPES))
    if all(hand[t] == 0 for t in all_tiles if is_suit(t)):
        meld_ok = all(
            is_honor(m["tiles"][0]) for m in melds
        )
        if meld_ok:
            yakuman.append(("字一色", 13))
            return yakuman

    # 緑一色
    green_tiles = {19, 20, 21, 23, 25, 32}  # 2s,3s,4s,6s,8s,發
    all_green = all(hand[t] == 0 for t in range(NUM_TILE_TYPES) if t not in green_tiles)
    if all_green:
        meld_ok = all(
            all(t in green_tiles for t in m["tiles"]) for m in melds
        )
        if meld_ok:
            yakuman.append(("緑一色", 13))
            return yakuman

    return yakuman if yakuman else None


def _build_all_mentsu(decomp, melds):
    """手牌の分解と副露を統合した全面子リスト"""
    all_mentsu = list(decomp["mentsu"])
    for m in melds:
        mt = m["type"]
        tile = m["tiles"][0]
        if mt in ("pon", "daiminkan", "kakan", "ankan"):
            all_mentsu.append(("koutsu", tile))
        elif mt == "chi":
            all_mentsu.append(("shuntsu", min(m["tiles"])))
    return all_mentsu
