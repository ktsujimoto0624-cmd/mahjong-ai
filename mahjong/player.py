"""
プレイヤーの状態管理

手牌・河（捨て牌）・副露（鳴き）・点数を管理する。
"""

from mahjong.tile import (
    empty_hand, hand_to_str, hand_total, tile_name, NUM_TILE_TYPES,
)


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
