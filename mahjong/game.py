"""
ゲームループ（1局の進行）

配牌 → ツモ → 打牌 → ... を繰り返し、
ツモ和了または流局で1局が終了する。

※ 現段階では鳴き（チー・ポン・カン）、ロン和了は未実装。
   まずツモ和了と流局のみで1局を回せるようにする。
"""

from mahjong.wall import Wall
from mahjong.player import Player
from mahjong.agari import is_agari
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

            # 打牌
            game_state = self._build_game_state()
            discard = self.agents[self.current_player].choose_discard(
                player, game_state
            )
            player.discard_tile(discard)
            self.record.record_discard(self.current_player, discard)

            if self.verbose:
                print(f"         打:{tile_name(discard)}")

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

    def _build_game_state(self):
        """エージェントに渡す局面情報を構築する。"""
        return {
            "turn": self.turn,
            "current_player": self.current_player,
            "discards": [p.discards[:] for p in self.players],
            "remaining_tiles": self.wall.remaining(),
            "dora_indicators": self.wall.get_dora_indicators(),
        }
