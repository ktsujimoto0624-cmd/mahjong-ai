"""ランダムに捨てるエージェント（動作確認用）"""

import random
from mahjong.engine.tile import NUM_TILE_TYPES
from agents.base import AgentBase


class RandomAgent(AgentBase):
    """ランダムに捨てるエージェント"""

    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)

    def choose_discard(self, player, game_state):
        candidates = []
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] > 0:
                candidates.append(tile_id)
        return self.rng.choice(candidates)
