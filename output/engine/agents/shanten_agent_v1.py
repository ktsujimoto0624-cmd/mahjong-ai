"""
シャンテン数ベースのエージェント

戦略:
1. 各牌を仮に捨てて、シャンテン数が最小になる牌を選ぶ
2. 同じシャンテン数なら、受入枚数（有効牌の数）が多い方を選ぶ
3. それでも同じなら、ランダムに選ぶ
"""

import random
from mahjong.engine.tile import NUM_TILE_TYPES, is_suit
from mahjong.engine.agari import shanten_number
from agents.base import AgentBase


class ShantenAgentV1(AgentBase):
    """シャンテン数ベースのエージェント"""

    model = "shanten-v1"
    description = "シャンテン数最小化で打牌。テンパイ即リーチ。門前重視。"

    def __init__(self, seed=None, name=None):
        super().__init__(name=name)
        self.rng = random.Random(seed)

    def choose_discard(self, player, game_state):
        melds_count = len(player.melds)
        best_tiles = []
        best_shanten = 99
        best_ukeire = -1

        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] == 0:
                continue

            player.hand[tile_id] -= 1
            s = shanten_number(player.hand, melds_count)

            if s < best_shanten:
                best_shanten = s
                best_ukeire = self._count_ukeire(player.hand, melds_count, s)
                best_tiles = [tile_id]
            elif s == best_shanten:
                u = self._count_ukeire(player.hand, melds_count, s)
                if u > best_ukeire:
                    best_ukeire = u
                    best_tiles = [tile_id]
                elif u == best_ukeire:
                    best_tiles.append(tile_id)

            player.hand[tile_id] += 1

        return self.rng.choice(best_tiles)

    def choose_discard_riichi(self, player, game_state):
        """リーチ宣言時の打牌: テンパイを維持する牌を選ぶ（受入最大）"""
        melds_count = len(player.melds)
        best_tiles = []
        best_ukeire = -1

        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] == 0:
                continue

            player.hand[tile_id] -= 1
            s = shanten_number(player.hand, melds_count)
            if s == 0:
                u = self._count_ukeire(player.hand, melds_count, 0)
                if u > best_ukeire:
                    best_ukeire = u
                    best_tiles = [tile_id]
                elif u == best_ukeire:
                    best_tiles.append(tile_id)
            player.hand[tile_id] += 1

        return self.rng.choice(best_tiles)

    def choose_pon(self, player, tile, from_seat, game_state):
        """ポン判断: シャンテン数が下がるならポンする"""
        melds_count = len(player.melds)
        current_s = shanten_number(player.hand, melds_count)

        player.hand[tile] -= 2
        new_s = shanten_number(player.hand, melds_count + 1)
        player.hand[tile] += 2

        return new_s < current_s

    def choose_chi(self, player, tile, from_seat, game_state):
        """チー判断: シャンテン数が下がるならチーする"""
        if not is_suit(tile):
            return None

        melds_count = len(player.melds)
        current_s = shanten_number(player.hand, melds_count)
        best_pair = None
        best_s = current_s

        for pair in self._chi_candidates(player, tile):
            player.hand[pair[0]] -= 1
            player.hand[pair[1]] -= 1
            new_s = shanten_number(player.hand, melds_count + 1)
            player.hand[pair[0]] += 1
            player.hand[pair[1]] += 1

            if new_s < best_s:
                best_s = new_s
                best_pair = list(pair)

        return best_pair

    def _chi_candidates(self, player, tile):
        """チー可能な手牌の2枚の組み合わせを列挙"""
        if not is_suit(tile):
            return []
        num = tile % 9
        base = tile - num
        candidates = []

        if num >= 2:
            a, b = base + num - 2, base + num - 1
            if player.hand[a] > 0 and player.hand[b] > 0:
                candidates.append((a, b))

        if num >= 1 and num <= 7:
            a, b = base + num - 1, base + num + 1
            if player.hand[a] > 0 and player.hand[b] > 0:
                candidates.append((a, b))

        if num <= 6:
            a, b = base + num + 1, base + num + 2
            if player.hand[a] > 0 and player.hand[b] > 0:
                candidates.append((a, b))

        return candidates

    def choose_ankan(self, player, game_state):
        """暗槓判断: 4枚揃っていたら暗槓する"""
        if player.is_riichi:
            return None
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] >= 4:
                return tile_id
        return None

    def choose_kakan(self, player, game_state):
        """加槓判断: ポンした牌の4枚目を持っていたら加槓する"""
        if player.is_riichi:
            return None
        for meld in player.melds:
            if meld["type"] == "pon":
                tile_id = meld["tiles"][0]
                if player.hand[tile_id] >= 1:
                    return tile_id
        return None

    def _count_ukeire(self, hand, melds_count, current_shanten):
        """受入枚数を数える（種類数のみ）"""
        count = 0
        for tile_id in range(NUM_TILE_TYPES):
            if hand[tile_id] >= 4:
                continue
            hand[tile_id] += 1
            s = shanten_number(hand, melds_count)
            if s < current_shanten:
                count += 1
            hand[tile_id] -= 1
        return count
