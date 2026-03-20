"""
ゲームループ（1局の進行）

配牌 → ツモ → リーチ判定 → 打牌 → ロン判定 → ... を繰り返し、
ツモ和了、ロン和了、または流局で1局が終了する。

※ 鳴き（チー・ポン・カン）は未実装。
※ リーチ後はツモ切り固定。
"""

from mahjong.wall import Wall
from mahjong.player import Player
from mahjong.agari import is_agari, shanten_number
from mahjong.tile import tile_name, hand_to_str
from mahjong.record import GameRecord


class GameRound:
    """1局を管理するクラス"""

    SEAT_NAMES = ["東", "南", "西", "北"]

    def __init__(self, agents, wall_seed=None, verbose=False):
        """
        Args:
            agents: 4つのAgentBaseオブジェクトのリスト
            wall_seed: 山の乱数シード
            verbose: 詳細ログを出力するか
        """
        self.agents = agents
        self.wall = Wall(seed=wall_seed)
        self.players = [Player(seat=i) for i in range(4)]
        self.verbose = verbose
        self.turn = 0
        self.current_player = 0
        self.result = None

        # 棋譜記録
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
                self.result = {"type": "ryukyoku", "winner": None, "turn": self.turn}
                self.record.record_result(self.result)
                if self.verbose:
                    print(f"\n=== 流局（{self.turn}巡目） ===")
                break

            player = self.players[self.current_player]
            player.draw_tile(tile)
            self.record.record_draw(self.current_player, tile)

            if self.verbose:
                print(
                    f"[{self.turn}巡目] {self.SEAT_NAMES[self.current_player]}家 "
                    f"ツモ:{tile_name(tile)} "
                    f"手牌:{hand_to_str(player.hand)}"
                )

            # ツモ和了判定
            melds_count = len(player.melds)
            if is_agari(player.hand, melds_count):
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
                break

            # リーチ判定 & 打牌
            game_state = self._build_game_state()
            riichi_declared = False

            if player.is_riichi:
                # リーチ中はツモ切り
                discard = tile
            elif self._can_riichi(player):
                # リーチ可能か？
                wants_riichi = self.agents[self.current_player].choose_riichi(
                    player, game_state
                )
                if wants_riichi:
                    discard = self.agents[self.current_player].choose_discard_riichi(
                        player, game_state
                    )
                    riichi_declared = True
                else:
                    discard = self.agents[self.current_player].choose_discard(
                        player, game_state
                    )
            else:
                discard = self.agents[self.current_player].choose_discard(
                    player, game_state
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
                self.current_player, discard, is_riichi=riichi_declared
            )

            if self.verbose:
                print(f"         打:{tile_name(discard)}")

            # ロン和了判定（頭ハネ: 打牌者の下家から順に判定）
            ron_winner = self._check_ron(self.current_player, discard)
            if ron_winner is not None:
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
                    print(
                        f"    手牌: "
                        f"{hand_to_str(self.players[ron_winner].hand)}"
                    )
                break

            # 次のプレイヤーへ
            self.current_player = (self.current_player + 1) % 4
            if self.current_player == 0:
                self.turn += 1

        return self.result

    def _deal(self):
        """配牌: 各プレイヤーに13枚ずつ"""
        for _ in range(13):
            for p in self.players:
                tile = self.wall.draw()
                p.draw_tile(tile)

        # 配牌を記録
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

    def _can_riichi(self, player):
        """
        リーチ宣言可能か判定する。

        条件:
        - 門前であること（鳴いていない）
        - まだリーチしていない
        - ツモ後の手牌（14枚）からいずれかの牌を切ってテンパイになる
        - 山に残り牌がある（最低1回のツモ機会が必要）
        """
        if player.is_riichi:
            return False
        if not player.is_menzen():
            return False
        if self.wall.remaining() == 0:
            return False

        # いずれかの牌を捨ててテンパイになるか
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

    def _check_ron(self, discarder, tile):
        """
        ロン和了の判定。打牌者の下家から順にチェック（頭ハネ）。

        Returns:
            ロンするプレイヤーの席番号。誰もロンしなければ None。
        """
        game_state = self._build_game_state()
        for i in range(1, 4):
            seat = (discarder + i) % 4
            player = self.players[seat]
            melds_count = len(player.melds)

            # 仮にその牌を手牌に加えて和了判定
            player.hand[tile] += 1
            can_agari = is_agari(player.hand, melds_count)
            player.hand[tile] -= 1

            if can_agari:
                # エージェントにロンするか確認
                wants_ron = self.agents[seat].choose_ron(
                    player, tile, discarder, game_state
                )
                if wants_ron:
                    return seat
        return None

    def _build_game_state(self):
        """エージェントに渡す局面情報を構築する。"""
        return {
            "turn": self.turn,
            "current_player": self.current_player,
            "discards": [p.discards[:] for p in self.players],
            "remaining_tiles": self.wall.remaining(),
            "dora_indicators": self.wall.get_dora_indicators(),
            "riichi": [p.is_riichi for p in self.players],
        }
