"""
プレイヤーの状態管理

手牌・河（捨て牌）・副露（鳴き）・点数を管理する。
"""

from mahjong.engine.tile import (
    empty_hand, hand_to_str, hand_total, tile_name, NUM_TILE_TYPES,
)
from mahjong.engine.agari import waiting_tiles


class Player:
    """1人のプレイヤーの状態"""

    def __init__(self, seat, points=25000):
        """
        Args:
            seat: 席番号 (0=東, 1=南, 2=西, 3=北)
            points: 初期持ち点
        """
        self.seat = seat
        self.points = points

        # 手牌（カウント配列: 34要素）
        self.hand = empty_hand()

        # 河（捨て牌の履歴）: 牌種IDのリスト
        self.discards = []

        # 副露（鳴き）のリスト
        # 各要素は辞書: {"type": "chi"|"pon"|"kan", "tiles": [...], "from": seat}
        self.melds = []

        # リーチ宣言しているか
        self.is_riichi = False

        # リーチ宣言した巡目
        self.riichi_turn = -1

    def draw_tile(self, tile_id):
        """ツモ: 手牌に1枚加える"""
        self.hand[tile_id] += 1

    def discard_tile(self, tile_id):
        """打牌: 手牌から1枚捨てる"""
        if self.hand[tile_id] <= 0:
            raise ValueError(f"{tile_name(tile_id)}を持っていないのに捨てようとした")
        self.hand[tile_id] -= 1
        self.discards.append(tile_id)

    def hand_tiles(self):
        """手牌にある牌種IDのリストを返す（重複あり）"""
        tiles = []
        for tile_id in range(NUM_TILE_TYPES):
            for _ in range(self.hand[tile_id]):
                tiles.append(tile_id)
        return tiles

    def closed_tile_count(self):
        """門前の手牌枚数"""
        return hand_total(self.hand)

    def add_meld(self, meld_type, tiles, from_seat=None):
        """
        副露（鳴き）を追加する。

        Args:
            meld_type: "chi", "pon", "daiminkan", "ankan", "kakan"
            tiles: 副露に含まれる牌IDのリスト
            from_seat: 鳴いた相手の席番号（ankanはNone）
        """
        self.melds.append({
            "type": meld_type,
            "tiles": tiles,
            "from": from_seat,
        })

    def add_chi(self, taken_tile, hand_tiles, from_seat):
        """
        チーを実行する。

        Args:
            taken_tile: 鳴いた牌（他家の捨て牌）
            hand_tiles: 手牌から出す2枚のリスト
            from_seat: 鳴いた相手の席番号
        """
        for t in hand_tiles:
            self.hand[t] -= 1
        meld_tiles = sorted([taken_tile] + hand_tiles)
        self.add_meld("chi", meld_tiles, from_seat)

    def add_pon(self, taken_tile, from_seat):
        """
        ポンを実行する。

        Args:
            taken_tile: 鳴いた牌（他家の捨て牌）
            from_seat: 鳴いた相手の席番号
        """
        self.hand[taken_tile] -= 2
        self.add_meld("pon", [taken_tile, taken_tile, taken_tile], from_seat)

    def add_daiminkan(self, taken_tile, from_seat):
        """
        大明槓を実行する。

        Args:
            taken_tile: 鳴いた牌（他家の捨て牌）
            from_seat: 鳴いた相手の席番号
        """
        self.hand[taken_tile] -= 3
        self.add_meld(
            "daiminkan",
            [taken_tile, taken_tile, taken_tile, taken_tile],
            from_seat,
        )

    def add_ankan(self, tile_id):
        """
        暗槓を実行する。

        Args:
            tile_id: 暗槓する牌のID
        """
        self.hand[tile_id] -= 4
        self.add_meld(
            "ankan",
            [tile_id, tile_id, tile_id, tile_id],
            None,
        )

    def add_kakan(self, tile_id):
        """
        加槓を実行する（既存のポンに1枚追加）。

        Args:
            tile_id: 加槓する牌のID
        """
        self.hand[tile_id] -= 1
        for meld in self.melds:
            if meld["type"] == "pon" and meld["tiles"][0] == tile_id:
                meld["type"] = "kakan"
                meld["tiles"].append(tile_id)
                return
        raise ValueError(f"{tile_name(tile_id)}のポンが見つからない")

    def is_furiten(self):
        """
        捨て牌フリテン判定。

        自分の待ち牌のいずれかが自分の河にある場合、フリテン。
        """
        waits = waiting_tiles(self.hand, len(self.melds))
        if not waits:
            return False
        for tile_id in waits:
            if tile_id in self.discards:
                return True
        return False

    def is_menzen(self):
        """門前（鳴いていない）かどうか"""
        # 暗槓は門前扱い
        for meld in self.melds:
            if meld["type"] != "ankan":
                return False
        return True

    def __str__(self):
        riichi_mark = " [リーチ]" if self.is_riichi else ""
        return (
            f"Player{self.seat}({self.points}点){riichi_mark}: "
            f"{hand_to_str(self.hand)}"
        )
