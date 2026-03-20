"""
エージェント（AI）のインターフェース

全てのAIはAgentBaseを継承し、choose_discard()を実装する。
"""

import random
from mahjong.tile import NUM_TILE_TYPES, is_suit
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

    def choose_riichi(self, player, game_state):
        """
        リーチ宣言するかどうか決める。

        Args:
            player: 自分のPlayerオブジェクト（ツモ後14枚の状態）
            game_state: 現在の局面情報（辞書）

        Returns:
            True if リーチする
        """
        return True  # デフォルトはテンパイ門前なら常にリーチ

    def choose_discard_riichi(self, player, game_state):
        """
        リーチ宣言時にどの牌を捨てるか決める。
        捨てた後にテンパイを維持する牌を選ぶ必要がある。

        Args:
            player: 自分のPlayerオブジェクト（ツモ後14枚の状態）
            game_state: 現在の局面情報（辞書）

        Returns:
            捨てる牌のID
        """
        # デフォルトは choose_discard と同じ
        return self.choose_discard(player, game_state)

    def choose_ron(self, player, tile, from_seat, game_state):
        """
        ロン和了するかどうか決める。

        Returns:
            True if ロンする
        """
        return True  # デフォルトはロンできるなら常にロン

    def choose_pon(self, player, tile, from_seat, game_state):
        """
        ポンするかどうか決める。

        Returns:
            True if ポンする
        """
        return False  # デフォルトは鳴かない

    def choose_chi(self, player, tile, from_seat, game_state):
        """
        チーするかどうか決める。

        Returns:
            チーする場合は手牌から出す2枚のリスト、しない場合はNone
        """
        return None  # デフォルトは鳴かない

    def choose_kan(self, player, tile, from_seat, game_state):
        """
        大明槓するかどうか決める。

        Returns:
            True if 大明槓する
        """
        return False  # デフォルトは鳴かない

    def choose_ankan(self, player, game_state):
        """
        暗槓するかどうか決める（ツモ後、打牌前に判定）。

        Returns:
            暗槓する牌ID、またはNone
        """
        return None  # デフォルトはしない

    def choose_kakan(self, player, game_state):
        """
        加槓するかどうか決める（ツモ後、打牌前に判定）。

        Returns:
            加槓する牌ID、またはNone
        """
        return None  # デフォルトはしない


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
            if s == 0:  # テンパイ維持
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

        # ポン後をシミュレート: 手牌から2枚減、副露+1
        player.hand[tile] -= 2
        new_s = shanten_number(player.hand, melds_count + 1)
        player.hand[tile] += 2

        # シャンテン数が下がるならポン（打牌で1枚減る分も考慮済み）
        return new_s < current_s

    def choose_chi(self, player, tile, from_seat, game_state):
        """チー判断: シャンテン数が下がるならチーする"""
        if not is_suit(tile):
            return None

        melds_count = len(player.melds)
        current_s = shanten_number(player.hand, melds_count)
        best_pair = None
        best_s = current_s

        # チーできる組み合わせを列挙
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
        num = tile % 9  # 0-8
        base = tile - num  # 萬子/筒子/索子の先頭ID
        candidates = []

        # tile-2, tile-1 で順子
        if num >= 2:
            a, b = base + num - 2, base + num - 1
            if player.hand[a] > 0 and player.hand[b] > 0:
                candidates.append((a, b))

        # tile-1, tile+1 で順子
        if num >= 1 and num <= 7:
            a, b = base + num - 1, base + num + 1
            if player.hand[a] > 0 and player.hand[b] > 0:
                candidates.append((a, b))

        # tile+1, tile+2 で順子
        if num <= 6:
            a, b = base + num + 1, base + num + 2
            if player.hand[a] > 0 and player.hand[b] > 0:
                candidates.append((a, b))

        return candidates

    def choose_ankan(self, player, game_state):
        """暗槓判断: 4枚揃っていたら暗槓する"""
        if player.is_riichi:
            return None  # リーチ中は暗槓しない（簡易実装）
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
