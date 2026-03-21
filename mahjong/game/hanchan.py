"""
半荘（東風戦・東南戦）の進行管理

複数の局（GameRound）を管理し、点数・親・場風を追跡する。

東風戦: 東1局～東4局（親が1周）
東南戦: 東1局～南4局（親が2周）
"""

from mahjong.game.round import GameRound


WIND_NAMES = ["東", "南", "西", "北"]


class Hanchan:
    """半荘（複数局）を管理するクラス"""

    def __init__(self, agents, mode="tonnansen", starting_points=25000,
                 verbose=False, base_seed=None):
        """
        Args:
            agents: 4人分のエージェント
            mode: "tonpusen"(東風戦) or "tonnansen"(東南戦)
            starting_points: 初期持ち点
            verbose: ログ出力
            base_seed: 牌山シード（Noneでランダム）
        """
        self.agents = agents
        self.mode = mode
        self.max_wind = 1 if mode == "tonpusen" else 2
        self.verbose = verbose
        self.base_seed = base_seed

        self.points = [starting_points] * 4
        self.round_wind = 0    # 0=東, 1=南
        self.round_number = 0  # 0-3（局番号、0始まり）
        self.honba = 0         # 本場
        self.riichi_pool = 0   # 供託リーチ棒（1000点単位の合計）
        self.dealer = 0        # 親の席番号

        self.round_results = []  # 各局の結果リスト
        self.is_finished = False

    def run(self):
        """半荘を実行し、最終結果を返す"""
        round_index = 0

        while not self.is_finished:
            seed = None
            if self.base_seed is not None:
                seed = self.base_seed + round_index

            result = self._play_one_round(seed)
            self.round_results.append(result)
            round_index += 1

            if self.verbose:
                self._log_standings()

        return self._build_final_result()

    def _play_one_round(self, wall_seed):
        """1局を実行し、点数を反映する"""
        round_label = (
            f"{WIND_NAMES[self.round_wind]}{self.round_number + 1}局"
            f"{self.honba}本場"
        )
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"=== {round_label} (親: {WIND_NAMES[self.dealer]}家) ===")
            print(f"    点数: {self._format_points()}")
            print(f"    供託: {self.riichi_pool}点")

        game = GameRound(
            self.agents,
            wall_seed=wall_seed,
            verbose=self.verbose,
            dealer=self.dealer,
            round_wind=self.round_wind,
        )
        game.run()

        # リーチ供託を回収
        riichi_count = sum(1 for p in game.players if p.is_riichi)
        self.riichi_pool += riichi_count * 1000
        for seat in range(4):
            if game.players[seat].is_riichi:
                self.points[seat] -= 1000

        result = game.result
        result["round_label"] = round_label
        result["round_wind"] = self.round_wind
        result["round_number"] = self.round_number
        result["honba"] = self.honba
        result["dealer"] = self.dealer

        # 点数移動
        self._apply_payments(result)

        # 親の継続・交代と局の進行
        self._advance_round(result)

        # 終了判定
        self._check_end()

        return result

    def _apply_payments(self, result):
        """和了結果に基づく点数移動"""
        if result["type"] == "ryukyoku":
            return

        score = result.get("score")
        if score is None:
            return

        payments = score["payments"]
        winner = result["winner"]
        is_dealer_win = (winner == self.dealer)

        if result["type"] == "tsumo":
            for seat in range(4):
                if seat == winner:
                    continue
                if is_dealer_win:
                    pay = payments["from_each_non_dealer"]
                else:
                    pay = (payments["from_dealer"]
                           if seat == self.dealer
                           else payments["from_each_non_dealer"])
                # 本場ボーナス: 各自 +100×本場
                pay += self.honba * 100
                self.points[seat] -= pay
                self.points[winner] += pay

        elif result["type"] == "ron":
            discarder = result["from_player"]
            pay = payments["from_discarder"]
            # 本場ボーナス: 放銃者から +300×本場
            pay += self.honba * 300
            self.points[discarder] -= pay
            self.points[winner] += pay

        # 供託リーチ棒を和了者が獲得
        self.points[winner] += self.riichi_pool
        self.riichi_pool = 0

    def _advance_round(self, result):
        """親の交代・局の進行を判定"""
        dealer_won = (
            result["type"] in ("tsumo", "ron")
            and result["winner"] == self.dealer
        )

        if dealer_won:
            # 連荘: 親続行、本場+1
            self.honba += 1
        elif result["type"] == "ryukyoku":
            # 流局: 親続行、本場+1
            self.honba += 1
        else:
            # 子の和了: 親交代、本場リセット
            self.honba = 0
            self.round_number += 1
            if self.round_number >= 4:
                self.round_number = 0
                self.round_wind += 1
            self.dealer = (self.dealer + 1) % 4

    def _check_end(self):
        """終了条件の判定"""
        # 誰かが0点未満（飛び）
        if any(p < 0 for p in self.points):
            self.is_finished = True
            return

        # 規定の場が終了
        if self.round_wind >= self.max_wind:
            self.is_finished = True
            return

    def _build_final_result(self):
        """最終結果を構築"""
        # 順位計算（点数降順、同点は席番号順）
        rankings = sorted(
            range(4),
            key=lambda s: (-self.points[s], s),
        )

        return {
            "mode": self.mode,
            "points": list(self.points),
            "rankings": rankings,
            "rounds_played": len(self.round_results),
            "round_results": self.round_results,
            "agents": [a.label for a in self.agents],
        }

    def _format_points(self):
        """点数表示用フォーマット"""
        parts = []
        for seat in range(4):
            wind = WIND_NAMES[seat]
            parts.append(f"{wind}:{self.points[seat]}")
        return " ".join(parts)

    def _log_standings(self):
        """現在の点数状況をログ出力"""
        print(f"    → 点数: {self._format_points()}")
        if self.riichi_pool > 0:
            print(f"    → 供託: {self.riichi_pool}点")
