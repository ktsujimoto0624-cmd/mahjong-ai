"""ランダムに捨てるエージェント（動作確認用）"""

import random
from mahjong.engine.tile import NUM_TILE_TYPES
from agents.base import AgentBase


class RandomAgent(AgentBase):
    """ランダムに捨てるエージェント"""

    model = "random-v1"
    description = "手牌からランダムに1枚選んで捨てる。動作確認・ベースライン用。"

    def __init__(self, seed=None, name=None):
        super().__init__(name=name)
        self.rng = random.Random(seed)

    def choose_discard(self, player, game_state):
        candidates = []
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] > 0:
                candidates.append(tile_id)
        return self.rng.choice(candidates)
