"""
山（壁牌）の管理

136枚の牌をシャッフルし、順にツモる機能を提供する。
王牌（嶺上牌・ドラ表示牌）の管理も含む。
"""

import random
from mahjong.engine.tile import NUM_TILE_TYPES, NUM_EACH_TILE, NUM_TOTAL_TILES


class Wall:
    """山（壁牌）を管理するクラス"""

    # 王牌は最後の14枚
    DEAD_WALL_SIZE = 14

    def __init__(self, seed=None):
        """
        山を生成してシャッフルする。

        Args:
            seed: 乱数シード（再現性のため）
        """
        # 136枚の牌を生成（牌種IDの配列）
        # 各牌種が4枚ずつ
        self.tiles = []
        for tile_id in range(NUM_TILE_TYPES):
            for _ in range(NUM_EACH_TILE):
                self.tiles.append(tile_id)

        # シャッフル
        rng = random.Random(seed)
        rng.shuffle(self.tiles)

        # ツモ位置（先頭から引いていく）
        self.draw_pos = 0

        # 王牌の範囲: 末尾14枚
        self.dead_wall_start = NUM_TOTAL_TILES - self.DEAD_WALL_SIZE

        # ドラ表示牌の位置（王牌の中、末尾から5番目）
        # 標準的な配置: 嶺上牌4枚 + ドラ表示5枚 + 裏ドラ表示5枚 = 14枚
        self.dora_indicator_count = 1  # 最初は1枚表示

    def draw(self):
        """
        山から1枚ツモる。

        Returns:
            牌種ID、またはツモ切れの場合None
        """
        if self.draw_pos >= self.dead_wall_start:
            return None  # ツモ切れ（王牌に到達）
        tile = self.tiles[self.draw_pos]
        self.draw_pos += 1
        return tile

    def remaining(self):
        """ツモ可能な残り枚数"""
        return self.dead_wall_start - self.draw_pos

    def draw_from_dead_wall(self):
        """
        嶺上牌（カンしたときのツモ）を引く。

        Returns:
            牌種ID
        """
        # 嶺上牌は王牌の先頭から
        idx = self.dead_wall_start
        tile = self.tiles[idx]
        self.dead_wall_start += 1  # 嶺上牌を消費
        return tile

    def get_dora_indicators(self):
        """
        現在のドラ表示牌を返す。

        Returns:
            ドラ表示牌のリスト
        """
        indicators = []
        # ドラ表示牌は王牌の末尾側に配置
        base = NUM_TOTAL_TILES - 5  # 末尾から5番目がドラ表示1枚目
        for i in range(self.dora_indicator_count):
            indicators.append(self.tiles[base - i * 2])
        return indicators

    def add_dora_indicator(self):
        """カンドラを追加（カン時に呼ぶ）"""
        self.dora_indicator_count += 1
