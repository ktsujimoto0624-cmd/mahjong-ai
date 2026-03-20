"""
ゲームループ（1局の進行）

配牌 → ツモ → 暗槓/加槓判定 → リーチ判定 → 打牌
     → ロン判定 → ポン/カン判定 → チー判定 → ... を繰り返し、
ツモ和了、ロン和了、または流局で1局が終了する。

※ リーチ後はツモ切り固定。
"""

from mahjong.wall import Wall
from mahjong.player import Player
from mahjong.agari import is_agari, shanten_number
from mahjong.tile import tile_name, hand_to_str, is_suit
from mahjong.record import GameRecord


class GameRound:
    """1局を管理するクラス"""

    SEAT_NAMES = ["東", "南", "西", "北"]

    def __init__(self, agents, wall_seed=None, verbose=False):
        self.agents = agents
        self.wall = Wall(seed=wall_seed)
        self.players = [Player(seat=i) for i in range(4)]
        self.verbose = verbose
        self.turn = 0
        self.current_player = 0
        self.result = None

        self.record = GameRecord()
        self.record.set_metadata(
            wall_seed=wall_seed,
            agents=[a.label for a in agents],
        )

    def run(self):
        """1局を実行し、結果と棋譜を返す。"""
        self._deal()

        while True:
            # ツモ
            tile = self.wall.draw()
            if tile is None:
                self._finish_ryukyoku()
                break

            player = self.players[self.current_player]
            player.draw_tile(tile)
            self.record.record_draw(self.current_player, tile)

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
                # 鳴いた人は打牌のみ（ツモなし）
                continue

            # チー判定（下家のみ）
            chi_seat = self._handle_chi(discard)
            if chi_seat is not None:
                self.current_player = chi_seat
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

        self.result = {
            "type": "tsumo",
            "winner": self.current_player,
            "turn": self.turn,
            "winning_tile": tile,
        }
        self.record.record_result(self.result)
        if self.verbose:
            print(
                f"\n*** ツモ和了! {self.SEAT_NAMES[self.current_player]}家 "
                f"({self.turn}巡目) ***"
            )
            print(f"    手牌: {hand_to_str(player.hand)}")
        return True

    # === 暗槓・加槓 ===

    def _handle_self_kan(self, player):
        """
        暗槓・加槓の処理。

        Returns:
            "tsumo": 嶺上ツモ和了
            "rinshan": 嶺上ツモ後、打牌フェーズ継続
            None: カンなし
        """
        agent = self.agents[self.current_player]
        game_state = self._build_game_state()

        # 暗槓チェック
        ankan_tile = agent.choose_ankan(player, game_state)
        if ankan_tile is not None and player.hand[ankan_tile] >= 4:
            return self._execute_kan(
                player, "ankan", ankan_tile, None,
                [ankan_tile] * 4,
            )

        # 加槓チェック
        kakan_tile = agent.choose_kakan(player, game_state)
        if kakan_tile is not None:
            for meld in player.melds:
                if meld["type"] == "pon" and meld["tiles"][0] == kakan_tile:
                    if player.hand[kakan_tile] >= 1:
                        return self._execute_kan(
                            player, "kakan", kakan_tile, meld["from"],
                            [kakan_tile] * 4,
                        )

        return None

    def _execute_kan(self, player, kan_type, tile_id, from_seat, tiles):
        """カンを実行し、嶺上牌をツモる"""
        if kan_type == "ankan":
            player.add_ankan(tile_id)
        elif kan_type == "kakan":
            player.add_kakan(tile_id)
        elif kan_type == "daiminkan":
            player.add_daiminkan(tile_id, from_seat)

        self.record.record_meld(
            self.current_player, kan_type, tiles, from_seat, tile_id,
        )
        self.wall.add_dora_indicator()

        if self.verbose:
            label = {"ankan": "暗槓", "kakan": "加槓", "daiminkan": "大明槓"}[kan_type]
            print(
                f"         *** {label}! "
                f"{self.SEAT_NAMES[self.current_player]}家 "
                f"{tile_name(tile_id)} ***"
            )

        # 嶺上牌をツモ
        rinshan = self.wall.draw_from_dead_wall()
        player.draw_tile(rinshan)
        self.record.record_draw(self.current_player, rinshan)

        if self.verbose:
            print(
                f"         嶺上ツモ: {tile_name(rinshan)} "
                f"手牌:{hand_to_str(player.hand)}"
            )

        # 嶺上ツモ和了判定
        melds_count = len(player.melds)
        if is_agari(player.hand, melds_count):
            self.result = {
                "type": "tsumo",
                "winner": self.current_player,
                "turn": self.turn,
                "winning_tile": rinshan,
            }
            self.record.record_result(self.result)
            if self.verbose:
                print(
                    f"\n*** 嶺上開花! "
                    f"{self.SEAT_NAMES[self.current_player]}家 ***"
                )
            return "tsumo"

        return "rinshan"

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

        self.result = {
            "type": "ron",
            "winner": ron_winner,
            "from_player": self.current_player,
            "turn": self.turn,
            "winning_tile": discard,
        }
        self.record.record_result(self.result)
        if self.verbose:
            winner_name = self.SEAT_NAMES[ron_winner]
            from_name = self.SEAT_NAMES[self.current_player]
            print(
                f"\n*** ロン和了! {winner_name}家 ← {from_name}家 "
                f"({self.turn}巡目) ***"
            )
            print(f"    手牌: {hand_to_str(self.players[ron_winner].hand)}")
        return True

    def _check_ron(self, discarder, tile):
        """ロン和了判定。頭ハネ（下家優先）。"""
        game_state = self._build_game_state()
        for i in range(1, 4):
            seat = (discarder + i) % 4
            player = self.players[seat]
            melds_count = len(player.melds)

            player.hand[tile] += 1
            can_agari = is_agari(player.hand, melds_count)
            player.hand[tile] -= 1

            if can_agari:
                wants_ron = self.agents[seat].choose_ron(
                    player, tile, discarder, game_state,
                )
                if wants_ron:
                    return seat
        return None

    # === ポン・大明槓 ===

    def _handle_pon_kan(self, discard):
        """
        ポン・大明槓判定。鳴いた場合は鳴いた席番号を返す。

        優先度: 大明槓 > ポン
        """
        game_state = self._build_game_state()
        discarder = self.current_player

        for i in range(1, 4):
            seat = (discarder + i) % 4
            player = self.players[seat]

            if player.is_riichi:
                continue  # リーチ中は鳴けない

            # 大明槓チェック
            if player.hand[discard] >= 3:
                wants_kan = self.agents[seat].choose_kan(
                    player, discard, discarder, game_state,
                )
                if wants_kan:
                    player.add_daiminkan(discard, discarder)
                    self.record.record_meld(
                        seat, "daiminkan",
                        [discard] * 4, discarder, discard,
                    )
                    self.wall.add_dora_indicator()

                    if self.verbose:
                        print(
                            f"         *** 大明槓! "
                            f"{self.SEAT_NAMES[seat]}家 ← "
                            f"{self.SEAT_NAMES[discarder]}家 "
                            f"{tile_name(discard)} ***"
                        )

                    # 嶺上ツモ
                    rinshan = self.wall.draw_from_dead_wall()
                    player.draw_tile(rinshan)
                    self.record.record_draw(seat, rinshan)

                    if self.verbose:
                        print(f"         嶺上ツモ: {tile_name(rinshan)}")

                    return seat

            # ポンチェック
            if player.hand[discard] >= 2:
                wants_pon = self.agents[seat].choose_pon(
                    player, discard, discarder, game_state,
                )
                if wants_pon:
                    player.add_pon(discard, discarder)
                    self.record.record_meld(
                        seat, "pon",
                        [discard] * 3, discarder, discard,
                    )

                    if self.verbose:
                        print(
                            f"         *** ポン! "
                            f"{self.SEAT_NAMES[seat]}家 ← "
                            f"{self.SEAT_NAMES[discarder]}家 "
                            f"{tile_name(discard)} ***"
                        )

                    return seat

        return None

    # === チー ===

    def _handle_chi(self, discard):
        """チー判定。チーした場合は鳴いた席番号を返す。"""
        if not is_suit(discard):
            return None  # 字牌はチーできない

        next_seat = (self.current_player + 1) % 4
        player = self.players[next_seat]

        if player.is_riichi:
            return None  # リーチ中は鳴けない

        game_state = self._build_game_state()
        hand_tiles = self.agents[next_seat].choose_chi(
            player, discard, self.current_player, game_state,
        )

        if hand_tiles is None:
            return None

        # チー実行
        player.add_chi(discard, hand_tiles, self.current_player)
        meld_tiles = sorted([discard] + hand_tiles)
        self.record.record_meld(
            next_seat, "chi", meld_tiles, self.current_player, discard,
        )

        if self.verbose:
            tiles_str = " ".join(tile_name(t) for t in meld_tiles)
            print(
                f"         *** チー! "
                f"{self.SEAT_NAMES[next_seat]}家 ← "
                f"{self.SEAT_NAMES[self.current_player]}家 "
                f"[{tiles_str}] ***"
            )

        return next_seat

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
        if self.current_player == 0:
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

    def _log_draw(self, tile, player):
        """ツモのログ出力"""
        print(
            f"[{self.turn}巡目] {self.SEAT_NAMES[self.current_player]}家 "
            f"ツモ:{tile_name(tile)} "
            f"手牌:{hand_to_str(player.hand)}"
        )
