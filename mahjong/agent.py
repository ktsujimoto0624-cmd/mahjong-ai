"""
エージェント（AI）のインターフェース

全てのAIはAgentBaseを継承し、choose_discard()を実装する。
"""

import random
from mahjong.tile import NUM_TILE_TYPES
from mahjong.agari import shanten_number


_agent_counter = 0


def _next_agent_id():
    global _agent_counter
    _agent_counter += 1
    return _agent_counter


class AgentBase:
    """AIエージェントの基底クラス"""

    def __init__(self):
        self.agent_id = _next_agent_id()
        self.agent_type = self.__class__.__name__

    @property
    def label(self):
        """表示用ラベル（例: 'ShantenAgent#3'）"""
        return f"{self.agent_type}#{self.agent_id}"

    def choose_discard(self, player, game_state):
        """
        何を捨てるか決める。

        Args:
            player: 自分のPlayerオブジェクト
            game_state: 現在の局面情報（辞書）

        Returns:
            捨てる牌のID
        """
        raise NotImplementedError


class RandomAgent(AgentBase):
    """ランダムに捨てるエージェント（動作確認用）"""

    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)

    def choose_discard(self, player, game_state):
        # 手牌にある牌からランダムに選ぶ
        candidates = []
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] > 0:
                candidates.append(tile_id)
        return self.rng.choice(candidates)


class ShantenAgent(AgentBase):
    """
    シャンテン数ベースのエージェント

    戦略:
    1. 各牌を仮に捨てて、シャンテン数が最小になる牌を選ぶ
    2. 同じシャンテン数なら、受入枚数（有効牌の数）が多い方を選ぶ
    3. それでも同じなら、ランダムに選ぶ
    """

    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)

    def choose_discard(self, player, game_state):
        melds_count = len(player.melds)
        best_tiles = []
        best_shanten = 99
        best_ukeire = -1

        # 手牌にある各牌種について、捨てた場合を評価
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] == 0:
                continue

            # 仮に捨てる
            player.hand[tile_id] -= 1
            s = shanten_number(player.hand, melds_count)

            if s < best_shanten:
                # より良いシャンテン数が見つかった
                best_shanten = s
                best_ukeire = self._count_ukeire(player.hand, melds_count, s)
                best_tiles = [tile_id]
            elif s == best_shanten:
                # 同じシャンテン数なら受入枚数で比較
                u = self._count_ukeire(player.hand, melds_count, s)
                if u > best_ukeire:
                    best_ukeire = u
                    best_tiles = [tile_id]
                elif u == best_ukeire:
                    best_tiles.append(tile_id)

            # 元に戻す
            player.hand[tile_id] += 1

        return self.rng.choice(best_tiles)

    def _count_ukeire(self, hand, melds_count, current_shanten):
        """
        受入枚数を数える。
        「引いたらシャンテン数が下がる牌」が何種何枚あるか。

        Args:
            hand: 1枚捨てた後の手牌（13枚状態）
            melds_count: 副露数
            current_shanten: 現在のシャンテン数

        Returns:
            受入枚数（種類数 × 残り枚数は未考慮、種類数のみ）
        """
        count = 0
        for tile_id in range(NUM_TILE_TYPES):
            if hand[tile_id] >= 4:
                continue  # もう4枚あるので引けない
            hand[tile_id] += 1
            s = shanten_number(hand, melds_count)
            if s < current_shanten:
                count += 1
            hand[tile_id] -= 1
        return count
