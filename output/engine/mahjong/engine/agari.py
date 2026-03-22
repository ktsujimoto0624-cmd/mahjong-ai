"""
和了（アガリ）判定

手牌が和了形かどうかを判定する。
和了形: 4面子 + 1雀頭（基本形）、七対子、国士無双

面子 = 順子(123等) または 刻子(111等)
雀頭 = 同じ牌2枚

カウント配列を使って再帰的に判定する。
"""

from mahjong.engine.tile import (
    NUM_TILE_TYPES, HONOR_START, is_suit, is_honor,
)


def is_agari(hand, melds_count=0):
    """
    手牌が和了形かどうか判定する。

    Args:
        hand: カウント配列 (34要素)
        melds_count: 副露の数（面子の数に加算）

    Returns:
        True if 和了形
    """
    total = sum(hand)

    # 手牌 + 副露×3 = 14 であること
    if total + melds_count * 3 != 14:
        return False

    # 基本形（4面子1雀頭）の判定
    if _check_regular(hand, melds_count):
        return True

    # 七対子（門前のみ、副露なし）
    if melds_count == 0 and _check_seven_pairs(hand):
        return True

    # 国士無双（門前のみ）
    if melds_count == 0 and _check_kokushi(hand):
        return True

    return False


def _check_regular(hand, melds_count):
    """4面子1雀頭の判定"""
    needed_mentsu = 4 - melds_count  # 手牌から作る必要がある面子の数

    # 雀頭候補を試す
    for head in range(NUM_TILE_TYPES):
        if hand[head] < 2:
            continue

        # 雀頭を抜く
        work = list(hand)
        work[head] -= 2

        # 残りで面子を作れるか
        if _extract_mentsu(work, needed_mentsu):
            return True

    return False


def _extract_mentsu(hand, needed):
    """
    手牌から指定数の面子を取り出せるか再帰的に判定。
    貪欲法: 左（小さいID）から順に処理する。
    """
    if needed == 0:
        return all(c == 0 for c in hand)

    # 最初に牌がある位置を探す
    for i in range(NUM_TILE_TYPES):
        if hand[i] > 0:
            break
    else:
        return False

    # 刻子を試す (同じ牌が3枚)
    if hand[i] >= 3:
        hand[i] -= 3
        if _extract_mentsu(hand, needed - 1):
            hand[i] += 3
            return True
        hand[i] += 3

    # 順子を試す (数牌で連続3枚: i, i+1, i+2)
    if is_suit(i) and (i % 9) <= 6:  # 7以下なら順子の先頭になれる
        if hand[i + 1] > 0 and hand[i + 2] > 0:
            hand[i] -= 1
            hand[i + 1] -= 1
            hand[i + 2] -= 1
            if _extract_mentsu(hand, needed - 1):
                hand[i] += 1
                hand[i + 1] += 1
                hand[i + 2] += 1
                return True
            hand[i] += 1
            hand[i + 1] += 1
            hand[i + 2] += 1

    return False


def _check_seven_pairs(hand):
    """七対子の判定: 7種類の牌がちょうど2枚ずつ"""
    pairs = 0
    for count in hand:
        if count == 2:
            pairs += 1
        elif count != 0:
            return False
    return pairs == 7


def _check_kokushi(hand):
    """
    国士無双の判定:
    么九牌13種を全て1枚以上持ち、うち1種が2枚（雀頭）
    """
    # 么九牌のID: 1m,9m,1p,9p,1s,9s,東,南,西,北,白,發,中
    kokushi_tiles = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]

    # 么九牌以外を持っていたらNG
    for i in range(NUM_TILE_TYPES):
        if i not in kokushi_tiles and hand[i] > 0:
            return False

    # 13種全て持っているか
    pair_found = False
    for i in kokushi_tiles:
        if hand[i] == 0:
            return False
        if hand[i] == 2:
            if pair_found:
                return False  # 2種以上の対子はNG
            pair_found = True

    return pair_found


def shanten_number(hand, melds_count=0):
    """
    シャンテン数を計算する（基本形のみ、簡易版）。

    シャンテン数 = 和了まであと何枚交換が必要か
    0 = テンパイ、-1 = 和了

    Args:
        hand: カウント配列
        melds_count: 副露数

    Returns:
        シャンテン数
    """
    # 和了チェック
    if is_agari(hand, melds_count):
        return -1

    min_shanten = 8  # 最大は8向聴

    needed_mentsu = 4 - melds_count

    # 基本形のシャンテン数
    s = _shanten_regular(hand, needed_mentsu)
    min_shanten = min(min_shanten, s)

    # 七対子（門前のみ）
    if melds_count == 0:
        s = _shanten_seven_pairs(hand)
        min_shanten = min(min_shanten, s)

    # 国士無双（門前のみ）
    if melds_count == 0:
        s = _shanten_kokushi(hand)
        min_shanten = min(min_shanten, s)

    return min_shanten


def decompose_regular(hand, melds_count=0):
    """
    手牌を4面子1雀頭に分解する全パターンを列挙する。

    Args:
        hand: カウント配列 (34要素)
        melds_count: 副露数

    Returns:
        分解パターンのリスト。各パターンは辞書:
        {"head": tile_id, "mentsu": [(type, tile_id), ...]}
        type: "shuntsu" (順子) or "koutsu" (刻子)
        tile_id: 順子は先頭牌、刻子はその牌
    """
    results = []
    needed = 4 - melds_count

    for head in range(NUM_TILE_TYPES):
        if hand[head] < 2:
            continue
        work = list(hand)
        work[head] -= 2
        mentsu_list = []
        _find_mentsu(work, needed, mentsu_list, results, head)

    return results


def _find_mentsu(hand, needed, current, results, head):
    """面子を再帰的に抽出し、全パターンを収集する"""
    if needed == 0:
        if all(c == 0 for c in hand):
            results.append({"head": head, "mentsu": list(current)})
        return

    # 最初に牌がある位置を探す
    for i in range(NUM_TILE_TYPES):
        if hand[i] > 0:
            break
    else:
        return

    # 刻子
    if hand[i] >= 3:
        hand[i] -= 3
        current.append(("koutsu", i))
        _find_mentsu(hand, needed - 1, current, results, head)
        current.pop()
        hand[i] += 3

    # 順子
    if is_suit(i) and (i % 9) <= 6 and hand[i + 1] > 0 and hand[i + 2] > 0:
        hand[i] -= 1
        hand[i + 1] -= 1
        hand[i + 2] -= 1
        current.append(("shuntsu", i))
        _find_mentsu(hand, needed - 1, current, results, head)
        current.pop()
        hand[i] += 1
        hand[i + 1] += 1
        hand[i + 2] += 1


def _shanten_regular(hand, needed_mentsu):
    """基本形のシャンテン数（再帰探索）"""
    min_shanten = [8]

    def _search(hand, mentsu, partial, head, depth):
        """
        mentsu: 完成した面子の数
        partial: 対子や塔子（面子の一部、2枚組）の数
        head: 雀頭があるか
        """
        # 現在のシャンテン数
        # 公式: (必要面子数 - 完成面子) * 2 - partial - head
        effective = mentsu + partial
        if effective > needed_mentsu:
            partial -= (effective - needed_mentsu)
        s = (needed_mentsu - mentsu) * 2 - partial
        if head:
            s -= 1
        min_shanten[0] = min(min_shanten[0], s)

        # 枝刈り
        if s <= 0:
            return

        # depth位置から探索
        for i in range(depth, NUM_TILE_TYPES):
            if hand[i] == 0:
                continue

            # 刻子
            if hand[i] >= 3:
                hand[i] -= 3
                _search(hand, mentsu + 1, partial, head, i)
                hand[i] += 3

            # 順子
            if is_suit(i) and (i % 9) <= 6 and hand[i + 1] > 0 and hand[i + 2] > 0:
                hand[i] -= 1
                hand[i + 1] -= 1
                hand[i + 2] -= 1
                _search(hand, mentsu + 1, partial, head, i)
                hand[i] += 1
                hand[i + 1] += 1
                hand[i + 2] += 1

            # 対子（雀頭候補）
            if hand[i] >= 2 and not head:
                hand[i] -= 2
                _search(hand, mentsu, partial, True, i)
                hand[i] += 2

            # 対子（面子の一部として）
            if hand[i] >= 2:
                hand[i] -= 2
                _search(hand, mentsu, partial + 1, head, i)
                hand[i] += 2

            # 塔子（連続する2枚: i,i+1）
            if is_suit(i) and (i % 9) <= 7 and hand[i + 1] > 0:
                hand[i] -= 1
                hand[i + 1] -= 1
                _search(hand, mentsu, partial + 1, head, i)
                hand[i] += 1
                hand[i + 1] += 1

            # 嵌張（1つ飛びの2枚: i,i+2）
            if is_suit(i) and (i % 9) <= 6 and hand[i + 2] > 0:
                hand[i] -= 1
                hand[i + 2] -= 1
                _search(hand, mentsu, partial + 1, head, i)
                hand[i] += 1
                hand[i + 2] += 1

            break  # 最初の牌だけ処理して次の再帰に任せる

    work = list(hand)
    _search(work, 0, 0, False, 0)
    return min_shanten[0]


def _shanten_seven_pairs(hand):
    """七対子のシャンテン数: 6 - (対子の数)"""
    pairs = sum(1 for c in hand if c >= 2)
    return 6 - pairs


def _shanten_kokushi(hand):
    """国士無双のシャンテン数: 13 - (持っている么九牌種の数) - (么九牌の対子があれば1)"""
    kokushi_tiles = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
    kinds = sum(1 for i in kokushi_tiles if hand[i] > 0)
    has_pair = any(hand[i] >= 2 for i in kokushi_tiles)
    return 13 - kinds - (1 if has_pair else 0)


def waiting_tiles(hand, melds_count=0):
    """
    テンパイ時の待ち牌リストを返す。

    Args:
        hand: カウント配列 (34要素)
        melds_count: 副露数

    Returns:
        list[int]: 和了可能な牌IDのリスト（テンパイでなければ空）
    """
    waits = []
    for tile_id in range(NUM_TILE_TYPES):
        if hand[tile_id] >= 4:
            continue
        hand[tile_id] += 1
        if is_agari(hand, melds_count):
            waits.append(tile_id)
        hand[tile_id] -= 1
    return waits
