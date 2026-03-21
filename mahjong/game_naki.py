"""
鳴き（チー・ポン・カン）処理

GameRound から鳴き判定・実行ロジックを分離したMixin。
"""

from mahjong.agari import is_agari
from mahjong.tile import tile_name, hand_to_str, is_suit


class NakiMixin:
    """鳴き処理を提供するMixin"""

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
            # 点数計算は game.py の _calc_score を使う
            score = self._calc_score(player, rinshan, is_tsumo=True)
            self.result["score"] = score
            self.record.record_result(self.result)
            if self.verbose:
                print(
                    f"\n*** 嶺上開花! "
                    f"{self.SEAT_NAMES[self.current_player]}家 ***"
                )
                self._log_score(score)
            return "tsumo"

        return "rinshan"

    def _handle_pon_kan(self, discard):
        """ポン・大明槓判定。鳴いた場合は鳴いた席番号を返す。"""
        game_state = self._build_game_state()
        discarder = self.current_player

        for i in range(1, 4):
            seat = (discarder + i) % 4
            player = self.players[seat]

            if player.is_riichi:
                continue

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

    def _handle_chi(self, discard):
        """チー判定。チーした場合は鳴いた席番号を返す。"""
        if not is_suit(discard):
            return None

        next_seat = (self.current_player + 1) % 4
        player = self.players[next_seat]

        if player.is_riichi:
            return None

        game_state = self._build_game_state()
        hand_tiles = self.agents[next_seat].choose_chi(
            player, discard, self.current_player, game_state,
        )

        if hand_tiles is None:
            return None

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
