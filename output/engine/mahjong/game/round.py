"""
ゲームループ（1局の進行）

配牌 → ツモ → 暗槓/加槓判定 → リーチ判定 → 打牌
     → ロン判定 → ポン/カン判定 → チー判定 → ... を繰り返し、
ツモ和了、ロン和了、または流局で1局が終了する。

※ リーチ後はツモ切り固定。
"""

from mahjong.engine.wall import Wall
from mahjong.engine.player import Player
from mahjong.engine.agari import is_agari, shanten_number
from mahjong.engine.tile import tile_name, hand_to_str, is_suit, dora_from_indicator
from mahjong.record.record import GameRecord
from mahjong.scoring.score import calculate_score
from mahjong.game.naki import NakiMixin


class GameRound(NakiMixin):
    """1局を管理するクラス"""

    SEAT_NAMES = ["東", "南", "西", "北"]

    def __init__(self, agents, wall_seed=None, verbose=False,
                 dealer=0, round_wind=0):
        self.agents = agents
        self.wall = Wall(seed=wall_seed)
        self.players = [Player(seat=i) for i in range(4)]
        self.verbose = verbose
        self.turn = 0
        self.dealer = dealer
        self.round_wind = round_wind
        self.current_player = dealer
        self.result = None

        # 同巡フリテン: ロン可能牌を見逃したプレイヤー（ツモで解除）
        self.temporary_furiten = [False, False, False, False]
        # リーチ後フリテン: リーチ後にロン可能牌を見逃し（解除不可）
        self.permanent_furiten = [False, False, False, False]

        self.record = GameRecord()
        self.record.set_metadata(
            wall_seed=wall_seed,
            agents=[a.label for a in agents],
            dealer=dealer,
            round_wind=round_wind,
        )

    def run(self):
        """1局を実行し、結果と棋譜を返す。"""
        self._deal()
        naki_player = None  # 鳴いた直後のプレイヤー（ツモ不要）

        while True:
            player = self.players[self.current_player]

            if naki_player is not None:
                # チー/ポン/大明槓後 → ツモなしで打牌のみ
                naki_player = None
            else:
                # 通常ツモ
                tile = self.wall.draw()
                if tile is None:
                    self._finish_ryukyoku()
                    break

                player.draw_tile(tile)
                self.record.record_draw(self.current_player, tile)

                # ツモ時に同巡フリテンを解除
                self.temporary_furiten[self.current_player] = False

                if self.verbose:
                    self._log_draw(tile, player)

                # ツモ和了判定
                if self._check_tsumo(player, tile):
                    break

                # 暗槓・加槓判定（ツモ後、打牌前）
                kan_result = self._handle_self_kan(player)
                if kan_result == "tsumo":
                    break
                if kan_result == "rinshan":
                    # 嶺上ツモ後、再度打牌フェーズへ
                    continue

            # リーチ判定 & 打牌
            discard = self._handle_discard(player)

            # ロン和了判定
            if self._handle_ron(discard):
                break

            # ポン・大明槓判定
            naki_seat = self._handle_pon_kan(discard)
            if naki_seat is not None:
                self.current_player = naki_seat
                naki_player = naki_seat
                continue

            # チー判定（下家のみ）
            chi_seat = self._handle_chi(discard)
            if chi_seat is not None:
                self.current_player = chi_seat
                naki_player = chi_seat
                continue

            # 次のプレイヤーへ
            self._advance_turn()

        return self.result

    # === 配牌 ===

    def _deal(self):
        """配牌: 各プレイヤーに13枚ずつ"""
        for _ in range(13):
            for p in self.players:
                tile = self.wall.draw()
                p.draw_tile(tile)

        self.record.record_deal([p.hand for p in self.players])
        self.record.set_metadata(
            dora_indicators=self.wall.get_dora_indicators(),
        )

        if self.verbose:
            print("=== 配牌 ===")
            for p in self.players:
                agent_label = self.agents[p.seat].label
                print(
                    f"  {self.SEAT_NAMES[p.seat]}家 ({agent_label}): "
                    f"{hand_to_str(p.hand)}"
                )
            print()

    # === ツモ和了 ===

    def _check_tsumo(self, player, tile):
        """ツモ和了判定。和了ならTrue"""
        melds_count = len(player.melds)
        if not is_agari(player.hand, melds_count):
            return False

        score = self._calc_score(player, tile, is_tsumo=True)
        # 役なし → 和了不成立
        if score is None:
            return False

        self.result = {
            "type": "tsumo",
            "winner": self.current_player,
            "turn": self.turn,
            "winning_tile": tile,
            "score": score,
        }
        self.record.record_result(self.result)
        if self.verbose:
            print(
                f"\n*** ツモ和了! {self.SEAT_NAMES[self.current_player]}家 "
                f"({self.turn}巡目) ***"
            )
            print(f"    手牌: {hand_to_str(player.hand)}")
            self._log_score(score)
        return True

    # === リーチ & 打牌 ===

    def _handle_discard(self, player):
        """リーチ判定と打牌を処理し、捨て牌を返す"""
        game_state = self._build_game_state()
        riichi_declared = False

        if player.is_riichi:
            # リーチ中はツモ切り
            discard = self._find_last_draw(player)
        elif self._can_riichi(player):
            wants_riichi = self.agents[self.current_player].choose_riichi(
                player, game_state,
            )
            if wants_riichi:
                discard = self.agents[self.current_player].choose_discard_riichi(
                    player, game_state,
                )
                riichi_declared = True
            else:
                discard = self.agents[self.current_player].choose_discard(
                    player, game_state,
                )
        else:
            discard = self.agents[self.current_player].choose_discard(
                player, game_state,
            )

        if riichi_declared:
            player.is_riichi = True
            player.riichi_turn = self.turn
            self.record.record_riichi(self.current_player)
            if self.verbose:
                print(
                    f"         *** リーチ! "
                    f"{self.SEAT_NAMES[self.current_player]}家 ***"
                )

        player.discard_tile(discard)
        self.record.record_discard(
            self.current_player, discard, is_riichi=riichi_declared,
        )

        if self.verbose:
            print(f"         打:{tile_name(discard)}")

        return discard

    def _find_last_draw(self, player):
        """直前にツモった牌を特定する（リーチ中のツモ切り用）"""
        # 棋譜の最後のdrawアクションを参照
        for action in reversed(self.record.actions):
            if action["type"] == "draw" and action["seat"] == self.current_player:
                return action["tile"]
        # フォールバック: 手牌からランダム
        for tile_id in range(34):
            if player.hand[tile_id] > 0:
                return tile_id
        return 0

    # === ロン和了 ===

    def _handle_ron(self, discard):
        """ロン和了判定。和了ならTrue"""
        ron_winner = self._check_ron(self.current_player, discard)
        if ron_winner is None:
            return False

        winner_player = self.players[ron_winner]
        # ロン: 和了牌を手牌に加えてから点数計算
        winner_player.hand[discard] += 1
        score = self._calc_score(
            winner_player, discard, is_tsumo=False, seat=ron_winner,
        )
        winner_player.hand[discard] -= 1

        # 役なし → 和了不成立
        if score is None:
            if self.verbose:
                print(
                    f"         ({self.SEAT_NAMES[ron_winner]}家: "
                    f"役なしのためロン不可)"
                )
            return False

        self.result = {
            "type": "ron",
            "winner": ron_winner,
            "from_player": self.current_player,
            "turn": self.turn,
            "winning_tile": discard,
            "score": score,
        }
        self.record.record_result(self.result)
        if self.verbose:
            winner_name = self.SEAT_NAMES[ron_winner]
            from_name = self.SEAT_NAMES[self.current_player]
            print(
                f"\n*** ロン和了! {winner_name}家 ← {from_name}家 "
                f"({self.turn}巡目) ***"
            )
            print(f"    手牌: {hand_to_str(winner_player.hand)}")
            self._log_score(score)
        return True

    def _check_ron(self, discarder, tile):
        """ロン和了判定。フリテンチェック付き。頭ハネ（下家優先）。"""
        game_state = self._build_game_state()
        for i in range(1, 4):
            seat = (discarder + i) % 4
            player = self.players[seat]
            melds_count = len(player.melds)

            player.hand[tile] += 1
            can_agari = is_agari(player.hand, melds_count)
            player.hand[tile] -= 1

            if not can_agari:
                continue

            # フリテン判定（3種類）
            furiten_reason = None
            if player.is_furiten():
                furiten_reason = "捨て牌フリテン"
            elif self.temporary_furiten[seat]:
                furiten_reason = "同巡フリテン"
            elif self.permanent_furiten[seat]:
                furiten_reason = "リーチ後フリテン"

            if furiten_reason:
                if self.verbose:
                    print(
                        f"         ({self.SEAT_NAMES[seat]}家: "
                        f"{furiten_reason}のためロン不可)"
                    )
                continue

            wants_ron = self.agents[seat].choose_ron(
                player, tile, discarder, game_state,
            )
            if wants_ron:
                return seat

            # ロン可能だが見逃した → フリテン設定
            self.temporary_furiten[seat] = True
            if player.is_riichi:
                self.permanent_furiten[seat] = True

        return None

    # === ユーティリティ ===

    def _finish_ryukyoku(self):
        """流局処理"""
        self.result = {"type": "ryukyoku", "winner": None, "turn": self.turn}
        self.record.record_result(self.result)
        if self.verbose:
            print(f"\n=== 流局（{self.turn}巡目） ===")

    def _advance_turn(self):
        """次のプレイヤーに進める"""
        self.current_player = (self.current_player + 1) % 4
        if self.current_player == self.dealer:
            self.turn += 1

    def _can_riichi(self, player):
        """リーチ宣言可能か判定"""
        if player.is_riichi:
            return False
        if not player.is_menzen():
            return False
        if self.wall.remaining() == 0:
            return False

        melds_count = len(player.melds)
        for tile_id in range(34):
            if player.hand[tile_id] == 0:
                continue
            player.hand[tile_id] -= 1
            s = shanten_number(player.hand, melds_count)
            player.hand[tile_id] += 1
            if s == 0:
                return True
        return False

    def _build_game_state(self):
        """エージェントに渡す局面情報を構築する。"""
        return {
            "turn": self.turn,
            "current_player": self.current_player,
            "discards": [p.discards[:] for p in self.players],
            "remaining_tiles": self.wall.remaining(),
            "dora_indicators": self.wall.get_dora_indicators(),
            "riichi": [p.is_riichi for p in self.players],
            "melds": [[m.copy() for m in p.melds] for p in self.players],
        }

    def _calc_score(self, player, winning_tile, is_tsumo, seat=None):
        """点数計算用の win_info を構築して計算する"""
        if seat is None:
            seat = self.current_player

        # ドラ枚数を数える
        dora_tiles = [
            dora_from_indicator(ind)
            for ind in self.wall.get_dora_indicators()
        ]
        dora_count = 0
        for dt in dora_tiles:
            dora_count += player.hand[dt]
            for m in player.melds:
                dora_count += m["tiles"].count(dt)

        win_info = {
            "hand": list(player.hand),
            "melds": player.melds,
            "winning_tile": winning_tile,
            "is_tsumo": is_tsumo,
            "is_riichi": player.is_riichi,
            "seat_wind": (seat - self.dealer + 4) % 4,
            "round_wind": self.round_wind,
            "is_menzen": player.is_menzen(),
        }

        score = calculate_score(win_info)

        # ドラ加算
        if score is not None and dora_count > 0 and not score["is_yakuman"]:
            score["yaku"].append(("ドラ", dora_count))
            score["han"] += dora_count
            # 翻数が変わったので基本点を再計算
            from mahjong.scoring.score import _han_fu_to_base, _calculate_payments
            score["base_points"] = _han_fu_to_base(
                score["han"], score["fu"],
            )
            score["payments"] = _calculate_payments(
                score["base_points"], is_tsumo,
                is_dealer=(seat == 0),
            )

        return score

    def _log_score(self, score):
        """点数のログ出力"""
        if score is None:
            print("    役なし")
            return
        yaku_str = ", ".join(
            f"{name}({han}翻)" for name, han in score["yaku"]
        )
        print(f"    {yaku_str}")
        print(f"    {score['han']}翻 {score['fu']}符 {score['payments']['total']}点")

    def _log_draw(self, tile, player):
        """ツモのログ出力"""
        print(
            f"[{self.turn}巡目] {self.SEAT_NAMES[self.current_player]}家 "
            f"ツモ:{tile_name(tile)} "
            f"手牌:{hand_to_str(player.hand)}"
        )
