"""
牌(Tile)の定義とユーティリティ

牌の内部表現:
  0-8:   萬子 (1m-9m)
  9-17:  筒子 (1p-9p)
  18-26: 索子 (1s-9s)
  27-33: 字牌 (東南西北白發中)

手牌はカウント方式: 34要素のリストで、各牌種の所持枚数を保持する。
例: hand[0]=2 は 1萬を2枚持っていることを意味する。
"""

# --- 定数 ---

NUM_TILE_TYPES = 34   # 牌の種類数
NUM_EACH_TILE = 4     # 各牌種の枚数
NUM_TOTAL_TILES = 136  # 牌の総数

# 牌種のID範囲
MAN_START = 0   # 萬子の開始ID
PIN_START = 9   # 筒子の開始ID
SOU_START = 18  # 索子の開始ID
HONOR_START = 27  # 字牌の開始ID

# 字牌の個別ID
TON = 27    # 東
NAN = 28    # 南
SHA = 29    # 西
PEI = 30    # 北
HAKU = 31   # 白
HATSU = 32  # 發
CHUN = 33   # 中

# 三元牌
SANGENPAI = [HAKU, HATSU, CHUN]

# 風牌
KAZEHAI = [TON, NAN, SHA, PEI]

# 表示用の名前
TILE_NAMES = [
    "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
    "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
    "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
    "東", "南", "西", "北", "白", "發", "中",
]

TILE_NAMES_KANJI = [
    "一萬", "二萬", "三萬", "四萬", "五萬", "六萬", "七萬", "八萬", "九萬",
    "一筒", "二筒", "三筒", "四筒", "五筒", "六筒", "七筒", "八筒", "九筒",
    "一索", "二索", "三索", "四索", "五索", "六索", "七索", "八索", "九索",
    "東", "南", "西", "北", "白", "發", "中",
]


# --- ユーティリティ関数 ---

def tile_name(tile_id):
    """牌IDから表示名を返す"""
    return TILE_NAMES[tile_id]


def tile_name_kanji(tile_id):
    """牌IDから漢字表示名を返す"""
    return TILE_NAMES_KANJI[tile_id]


def is_man(tile_id):
    """萬子かどうか"""
    return MAN_START <= tile_id < PIN_START


def is_pin(tile_id):
    """筒子かどうか"""
    return PIN_START <= tile_id < SOU_START


def is_sou(tile_id):
    """索子かどうか"""
    return SOU_START <= tile_id < HONOR_START


def is_suit(tile_id):
    """数牌（萬子・筒子・索子）かどうか"""
    return tile_id < HONOR_START


def is_honor(tile_id):
    """字牌かどうか"""
    return tile_id >= HONOR_START


def is_terminal(tile_id):
    """老頭牌(1,9)かどうか"""
    if not is_suit(tile_id):
        return False
    num = tile_id % 9
    return num == 0 or num == 8


def is_terminal_or_honor(tile_id):
    """么九牌(1,9,字牌)かどうか"""
    return is_honor(tile_id) or is_terminal(tile_id)


def suit_number(tile_id):
    """数牌の数字(1-9)を返す。字牌の場合はNone"""
    if not is_suit(tile_id):
        return None
    return (tile_id % 9) + 1


def empty_hand():
    """空の手牌(カウント配列)を生成"""
    return [0] * NUM_TILE_TYPES


def hand_to_str(hand):
    """手牌(カウント配列)を文字列で表示"""
    parts = []
    for tile_id in range(NUM_TILE_TYPES):
        count = hand[tile_id]
        for _ in range(count):
            parts.append(TILE_NAMES[tile_id])
    return " ".join(parts)


def hand_total(hand):
    """手牌の合計枚数"""
    return sum(hand)


def dora_from_indicator(indicator_id):
    """
    ドラ表示牌からドラ牌を返す。

    数牌: 表示牌の次の数字（9→1に戻る）
    風牌: 東→南→西→北→東
    三元牌: 白→發→中→白
    """
    if is_suit(indicator_id):
        base = (indicator_id // 9) * 9
        num = indicator_id % 9
        return base + (num + 1) % 9
    elif indicator_id in KAZEHAI:
        idx = KAZEHAI.index(indicator_id)
        return KAZEHAI[(idx + 1) % 4]
    elif indicator_id in SANGENPAI:
        idx = SANGENPAI.index(indicator_id)
        return SANGENPAI[(idx + 1) % 3]
    return indicator_id
