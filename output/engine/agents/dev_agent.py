"""
作成中エージェント (ひよこベース)

調整可能パラメータ:
- BETAORI_SHANTEN: ベタオリに切り替えるシャンテン数 (default: 2)
- RIICHI_MIN_WAITS: リーチする最低待ち枚数 (default: 1)
- CALL_YAKUHAI_AGGRESSIVELY: 役牌を積極的に鳴くか (default: True)
- CALL_SHANTEN_THRESHOLD: 鳴きでシャンテンが進む場合に鳴くか (default: True)
- DANGER_WEIGHT: 危険度の重み (default: 1.0, 大きいほど守備的)
- DORA_KEEP_BONUS: ドラ温存のボーナス (default: 3)
"""

import random
from mahjong.engine.tile import (
    NUM_TILE_TYPES, NUM_EACH_TILE, SANGENPAI, KAZEHAI,
    is_suit, is_honor, is_terminal_or_honor, dora_from_indicator,
)
from mahjong.engine.agari import shanten_number, waiting_tiles
from agents.base import AgentBase


# ---------------------------------------------------------------------------
# 調整可能パラメータ
# ---------------------------------------------------------------------------
BETAORI_SHANTEN = 2
RIICHI_MIN_WAITS = 1
CALL_YAKUHAI_AGGRESSIVELY = True
CALL_SHANTEN_THRESHOLD = True
DANGER_WEIGHT = 1.0
DORA_KEEP_BONUS = 3

# ---------------------------------------------------------------------------
# 定数 (AlphaJong の parameters.js を参考)
# ---------------------------------------------------------------------------
SAFETY_WEIGHT = 1.0       # 安全度の重み（高いほど守備的）
EFFICIENCY_WEIGHT = 1.0   # 効率の重み


class DevAgent(AgentBase):
    """作成中エージェント (ひよこベースで戦略を調整中)"""

    model = "dev-v0"
    description = (
        "作成中。ひよこベースで戦略を調整中。"
    )

    def __init__(self, seed=None, name=None):
        super().__init__(name=name)
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    # 可視牌カウント（場に見えている牌の数）
    # ------------------------------------------------------------------

    def _build_visible_counts(self, player, game_state):
        """場に見えている牌の枚数を34要素配列で返す"""
        visible = [0] * NUM_TILE_TYPES
        for t in range(NUM_TILE_TYPES):
            visible[t] += player.hand[t]
        for discards in game_state["discards"]:
            for t in discards:
                visible[t] += 1
        for melds in game_state["melds"]:
            for m in melds:
                for t in m["tiles"]:
                    visible[t] += 1
        for ind in game_state["dora_indicators"]:
            visible[ind] += 1
        return visible

    def _remaining_count(self, tile_id, visible):
        """残り枚数（山+他家手牌に存在しうる枚数）"""
        return max(0, NUM_EACH_TILE - visible[tile_id])

    # ------------------------------------------------------------------
    # 受入枚数（実枚数ベース）
    # ------------------------------------------------------------------

    def _count_ukeire_weighted(self, hand, melds_count,
                               current_shanten, visible):
        """受入枚数を実際の残り枚数で計算する"""
        count = 0
        for tile_id in range(NUM_TILE_TYPES):
            remaining = self._remaining_count(tile_id, visible)
            if remaining <= 0 or hand[tile_id] >= 4:
                continue
            hand[tile_id] += 1
            s = shanten_number(hand, melds_count)
            if s < current_shanten:
                count += remaining
            hand[tile_id] -= 1
        return count

    # ------------------------------------------------------------------
    # 危険度評価 (AlphaJong の ai_defense.js を参考)
    # ------------------------------------------------------------------

    def _tile_danger(self, tile_id, player, game_state, visible):
        """
        牌の危険度を0-100で返す。

        考慮: リーチ状態、現物、筋、壁、字牌生牌、ドラ近接
        """
        danger = 0.0
        my_seat = game_state["current_player"]

        for seat in range(4):
            if seat == my_seat:
                continue
            if game_state["riichi"][seat]:
                danger += self._danger_against_riichi(
                    tile_id, seat, game_state, visible,
                )
            else:
                danger += self._base_danger_for_player(
                    tile_id, seat, game_state, visible,
                ) * 0.3

        return min(danger, 100.0)

    def _base_danger_for_player(self, tile_id, opponent_seat,
                                game_state, visible):
        """非リーチ相手に対する基本危険度"""
        if tile_id in game_state["discards"][opponent_seat]:
            return 0.0

        base = 10.0
        if is_honor(tile_id):
            if visible[tile_id] == 0:
                base = 20.0
            elif visible[tile_id] >= 2:
                base = 3.0

        if is_suit(tile_id):
            num = tile_id % 9
            if num == 0 or num == 8:
                base *= 0.7
            elif num == 1 or num == 7:
                base *= 0.85

        return base

    def _danger_against_riichi(self, tile_id, riichi_seat,
                               game_state, visible):
        """リーチ者に対する危険度"""
        if tile_id in game_state["discards"][riichi_seat]:
            return 0.0

        base = 30.0

        if self._is_suji_safe(tile_id, game_state["discards"][riichi_seat]):
            base *= 0.4

        base *= self._kabe_safety(tile_id, visible)

        if is_honor(tile_id):
            if visible[tile_id] >= 3:
                base = 2.0
            elif visible[tile_id] >= 2:
                base *= 0.5
            elif visible[tile_id] == 0:
                base *= 1.3

        if is_suit(tile_id):
            num = tile_id % 9
            if num == 0 or num == 8:
                base *= 0.7
            elif num == 1 or num == 7:
                base *= 0.85

        for ind in game_state["dora_indicators"]:
            dora_tile = dora_from_indicator(ind)
            if tile_id == dora_tile:
                base *= 1.15
            elif (is_suit(tile_id) and is_suit(dora_tile)
                  and tile_id // 9 == dora_tile // 9
                  and abs(tile_id - dora_tile) <= 2):
                base *= 1.05

        return min(base, 80.0)

    def _is_suji_safe(self, tile_id, opp_discards):
        """筋で安全か（両面待ちに当たらない）"""
        if not is_suit(tile_id):
            return False
        num = tile_id % 9
        base = tile_id - num
        suji_map = {
            0: [base + 3],
            1: [base + 4],
            2: [base + 5],
            3: [base + 0, base + 6],
            4: [base + 1, base + 7],
            5: [base + 2, base + 8],
            6: [base + 3],
            7: [base + 4],
            8: [base + 5],
        }
        return any(p in opp_discards for p in suji_map.get(num, []))

    def _kabe_safety(self, tile_id, visible):
        """壁分析: 隣接牌が多く見えていれば安全度UP"""
        if not is_suit(tile_id):
            return 1.0
        num = tile_id % 9
        base = tile_id - num
        factor = 1.0
        for offset in (-1, 1):
            nb = num + offset
            if 0 <= nb <= 8:
                seen = visible[base + nb]
                if seen >= 4:
                    factor *= 0.3
                elif seen >= 3:
                    factor *= 0.5
        return factor

    # ------------------------------------------------------------------
    # メイン打牌ロジック
    # ------------------------------------------------------------------

    def choose_discard(self, player, game_state):
        melds_count = len(player.melds)
        visible = self._build_visible_counts(player, game_state)
        current_shanten = shanten_number(player.hand, melds_count)

        my_seat = game_state["current_player"]
        any_riichi = any(
            game_state["riichi"][s] for s in range(4) if s != my_seat
        )

        # ベタオリ: リーチ者がいて自分が遠い場合
        if (any_riichi and current_shanten >= BETAORI_SHANTEN
                and not player.is_riichi):
            return self._choose_safest_discard(
                player, game_state, visible,
            )

        return self._choose_balanced_discard(
            player, game_state, visible, current_shanten,
            melds_count, any_riichi,
        )

    def _choose_safest_discard(self, player, game_state, visible):
        """ベタオリ: 最も安全な牌を切る"""
        safest_tiles = []
        min_danger = 999.0

        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] == 0:
                continue
            danger = self._tile_danger(
                tile_id, player, game_state, visible,
            )
            if danger < min_danger:
                min_danger = danger
                safest_tiles = [tile_id]
            elif abs(danger - min_danger) < 0.01:
                safest_tiles.append(tile_id)

        return self.rng.choice(safest_tiles)

    def _choose_balanced_discard(self, player, game_state, visible,
                                 current_shanten, melds_count,
                                 any_riichi):
        """
        効率と安全度を総合して打牌選択。
        AlphaJong の calculateTilePriority を参考。
        """
        best_tiles = []
        best_priority = -9999.0

        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] == 0:
                continue

            player.hand[tile_id] -= 1
            s = shanten_number(player.hand, melds_count)
            ukeire = self._count_ukeire_weighted(
                player.hand, melds_count, s, visible,
            )
            player.hand[tile_id] += 1

            # 効率スコア
            shanten_score = (8 - s) * 100.0
            ukeire_score = ukeire * 2.0
            efficiency = shanten_score + ukeire_score

            # 危険度ペナルティ
            danger = self._tile_danger(
                tile_id, player, game_state, visible,
            )
            danger_penalty = danger * SAFETY_WEIGHT * DANGER_WEIGHT
            if any_riichi and current_shanten >= 1:
                danger_penalty *= 1.5

            # ドラを切るペナルティ
            dora_penalty = 0.0
            for ind in game_state["dora_indicators"]:
                if tile_id == dora_from_indicator(ind):
                    dora_penalty = 30.0

            # 孤立牌ボーナス
            isolation = self._isolation_score(tile_id, player.hand)

            priority = (
                efficiency * EFFICIENCY_WEIGHT
                - danger_penalty
                - dora_penalty
                + isolation
            )

            if priority > best_priority:
                best_priority = priority
                best_tiles = [tile_id]
            elif abs(priority - best_priority) < 0.01:
                best_tiles.append(tile_id)

        return self.rng.choice(best_tiles)

    def _isolation_score(self, tile_id, hand):
        """孤立度スコア。孤立牌ほど高い値を返す。"""
        if is_honor(tile_id):
            return 5.0 if hand[tile_id] <= 1 else 0.0

        num = tile_id % 9
        base = tile_id - num
        has_neighbor = False
        if num > 0 and hand[base + num - 1] > 0:
            has_neighbor = True
        if num < 8 and hand[base + num + 1] > 0:
            has_neighbor = True
        if hand[tile_id] >= 2:
            has_neighbor = True

        if not has_neighbor:
            return 8.0
        if num == 0 or num == 8:
            return 3.0
        return 0.0

    # ------------------------------------------------------------------
    # リーチ判断 (AlphaJong の shouldRiichi を参考)
    # ------------------------------------------------------------------

    def choose_riichi(self, player, game_state):
        """待ち・残り枚数・相手状況でリーチを判断"""
        melds_count = len(player.melds)
        visible = self._build_visible_counts(player, game_state)
        remaining = game_state["remaining_tiles"]

        if remaining <= 4:
            return False

        waits = waiting_tiles(player.hand, melds_count)
        if not waits:
            return False

        total_wait_tiles = sum(
            self._remaining_count(w, visible) for w in waits
        )
        if total_wait_tiles == 0:
            return False

        my_seat = game_state["current_player"]
        opp_riichi = sum(
            1 for s in range(4)
            if s != my_seat and game_state["riichi"][s]
        )

        if opp_riichi >= 1 and total_wait_tiles <= 2:
            return False

        if remaining <= 10 and total_wait_tiles <= 2:
            return False

        if total_wait_tiles < RIICHI_MIN_WAITS:
            return False

        return True

    def choose_discard_riichi(self, player, game_state):
        """リーチ時打牌: 最良の待ちを選び、切る牌の安全度も考慮"""
        melds_count = len(player.melds)
        visible = self._build_visible_counts(player, game_state)
        best_tiles = []
        best_score = -1

        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] == 0:
                continue

            player.hand[tile_id] -= 1
            s = shanten_number(player.hand, melds_count)
            if s == 0:
                waits = waiting_tiles(player.hand, melds_count)
                wait_count = sum(
                    self._remaining_count(w, visible) for w in waits
                )
                score = wait_count * 10 + len(waits)
                danger = self._tile_danger(
                    tile_id, player, game_state, visible,
                )
                score -= danger * 0.3

                if score > best_score:
                    best_score = score
                    best_tiles = [tile_id]
                elif abs(score - best_score) < 0.01:
                    best_tiles.append(tile_id)
            player.hand[tile_id] += 1

        if not best_tiles:
            return self._fallback_riichi_discard(player, melds_count)
        return self.rng.choice(best_tiles)

    def _fallback_riichi_discard(self, player, melds_count):
        """リーチ打牌のフォールバック"""
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] == 0:
                continue
            player.hand[tile_id] -= 1
            s = shanten_number(player.hand, melds_count)
            player.hand[tile_id] += 1
            if s == 0:
                return tile_id
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] > 0:
                return tile_id
        return 0

    # ------------------------------------------------------------------
    # ポン判断 (AlphaJong の callTriple を参考)
    # ------------------------------------------------------------------

    def choose_pon(self, player, tile, from_seat, game_state):
        """
        シャンテン低減+役見込みで判断。
        役牌は積極的、門前テンパイは保持、遠い手は鳴かない。
        """
        melds_count = len(player.melds)
        current_s = shanten_number(player.hand, melds_count)

        player.hand[tile] -= 2
        new_s = shanten_number(player.hand, melds_count + 1)
        player.hand[tile] += 2

        if new_s > current_s:
            return False
        if new_s == current_s:
            return False

        # 役牌は積極的にポン
        if CALL_YAKUHAI_AGGRESSIVELY and tile in SANGENPAI:
            return True
        my_seat = game_state["current_player"]
        seat_wind = KAZEHAI[(my_seat + 4) % 4]
        round_wind = KAZEHAI[0]
        if CALL_YAKUHAI_AGGRESSIVELY and (
                tile == seat_wind or tile == round_wind):
            return True

        # 門前テンパイは維持
        if current_s == 0 and player.is_menzen():
            return False

        # 遠い手は門前維持
        if current_s >= 3 and player.is_menzen():
            return False

        # イーシャンテン→テンパイ or 2→1: 役見込みチェック
        if self._has_yaku_potential_after_call(
                player, tile, game_state):
            return True

        return False

    def _has_yaku_potential_after_call(self, player, called_tile,
                                      game_state):
        """鳴いた後に役がつく可能性の簡易チェック"""
        my_seat = game_state["current_player"]
        seat_wind = KAZEHAI[(my_seat + 4) % 4]
        round_wind = KAZEHAI[0]
        value_tiles = list(SANGENPAI) + [seat_wind, round_wind]

        for vt in value_tiles:
            if vt == called_tile or player.hand[vt] >= 3:
                return True

        # 断么九
        all_tanyao = all(
            not is_terminal_or_honor(t)
            for t in range(NUM_TILE_TYPES)
            if player.hand[t] > 0
        )
        if all_tanyao and not is_terminal_or_honor(called_tile):
            return True

        # 染め手チェック
        suits_used = set()
        for t in range(NUM_TILE_TYPES):
            if player.hand[t] > 0 and is_suit(t):
                suits_used.add(t // 9)
        if is_suit(called_tile):
            suits_used.add(called_tile // 9)
        for m in player.melds:
            t0 = m["tiles"][0]
            if is_suit(t0):
                suits_used.add(t0 // 9)
        if len(suits_used) <= 1:
            return True

        # ドラ多
        dora_count = 0
        for ind in game_state["dora_indicators"]:
            dt = dora_from_indicator(ind)
            dora_count += player.hand[dt]
            if dt == called_tile:
                dora_count += 1
        if dora_count >= 2:
            return True

        return False

    # ------------------------------------------------------------------
    # チー判断
    # ------------------------------------------------------------------

    def choose_chi(self, player, tile, from_seat, game_state):
        """シャンテン低減+役見込みで判断"""
        if not is_suit(tile):
            return None

        melds_count = len(player.melds)
        current_s = shanten_number(player.hand, melds_count)

        if current_s == 0 and player.is_menzen():
            return None

        visible = self._build_visible_counts(player, game_state)
        best_pair = None
        best_s = current_s
        best_ukeire = -1

        for pair in self._chi_candidates(player, tile):
            player.hand[pair[0]] -= 1
            player.hand[pair[1]] -= 1
            new_s = shanten_number(player.hand, melds_count + 1)

            if new_s < best_s:
                ukeire = self._count_ukeire_weighted(
                    player.hand, melds_count + 1, new_s, visible,
                )
                best_s = new_s
                best_ukeire = ukeire
                best_pair = list(pair)
            elif new_s == best_s and best_pair is not None:
                ukeire = self._count_ukeire_weighted(
                    player.hand, melds_count + 1, new_s, visible,
                )
                if ukeire > best_ukeire:
                    best_ukeire = ukeire
                    best_pair = list(pair)

            player.hand[pair[0]] += 1
            player.hand[pair[1]] += 1

        if best_pair is None:
            return None

        # 遠い手は門前維持
        if player.is_menzen() and current_s >= 3:
            return None

        # 門前からの鳴きは役が必要
        if player.is_menzen():
            if not self._has_chi_yaku_potential(
                    player, tile, best_pair, game_state):
                return None

        return best_pair

    def _has_chi_yaku_potential(self, player, chi_tile, pair,
                               game_state):
        """チー後に役がつくか簡易チェック"""
        chi_tiles = sorted([chi_tile] + pair)

        # 断么九
        all_tanyao = all(
            not is_terminal_or_honor(t)
            for t in range(NUM_TILE_TYPES)
            if player.hand[t] > 0
        )
        if all_tanyao and all(
                not is_terminal_or_honor(ct) for ct in chi_tiles):
            return True

        # 役牌刻子
        my_seat = game_state["current_player"]
        seat_wind = KAZEHAI[(my_seat + 4) % 4]
        round_wind = KAZEHAI[0]
        value_tiles = list(SANGENPAI) + [seat_wind, round_wind]
        for vt in value_tiles:
            if player.hand[vt] >= 3:
                return True
        for m in player.melds:
            if m["type"] == "pon" and m["tiles"][0] in value_tiles:
                return True

        # 染め手
        suits_used = set()
        for t in range(NUM_TILE_TYPES):
            if player.hand[t] > 0 and is_suit(t):
                suits_used.add(t // 9)
        for ct in chi_tiles:
            if is_suit(ct):
                suits_used.add(ct // 9)
        for m in player.melds:
            t0 = m["tiles"][0]
            if is_suit(t0):
                suits_used.add(t0 // 9)
        if len(suits_used) <= 1:
            return True

        # ドラ多
        dora_count = 0
        for ind in game_state["dora_indicators"]:
            dt = dora_from_indicator(ind)
            dora_count += player.hand[dt]
        if dora_count >= 2:
            return True

        return False

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

    # ------------------------------------------------------------------
    # 暗槓・加槓
    # ------------------------------------------------------------------

    def choose_ankan(self, player, game_state):
        """暗槓: シャンテン悪化しない場合のみ"""
        if player.is_riichi:
            return None
        melds_count = len(player.melds)
        current_s = shanten_number(player.hand, melds_count)
        for tile_id in range(NUM_TILE_TYPES):
            if player.hand[tile_id] >= 4:
                player.hand[tile_id] -= 4
                new_s = shanten_number(player.hand, melds_count + 1)
                player.hand[tile_id] += 4
                if new_s <= current_s:
                    return tile_id
        return None

    def choose_kakan(self, player, game_state):
        """加槓判断: ポンした牌の4枚目を持っていたら加槓"""
        if player.is_riichi:
            return None
        for meld in player.melds:
            if meld["type"] == "pon":
                tile_id = meld["tiles"][0]
                if player.hand[tile_id] >= 1:
                    return tile_id
        return None

