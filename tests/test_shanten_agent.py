"""ShantenAgent vs RandomAgent の対戦テスト"""

from mahjong.game import GameRound
from mahjong.agent import RandomAgent, ShantenAgent


def test_shanten_vs_random(num_games=100):
    """ShantenAgent 2人 vs RandomAgent 2人 で対戦"""
    print(f"=== ShantenAgent vs RandomAgent ({num_games}局) ===")
    print("席: 東=Shanten, 南=Random, 西=Shanten, 北=Random\n")

    wins = {"shanten": 0, "random": 0}
    ryukyoku = 0

    for i in range(num_games):
        agents = [
            ShantenAgent(seed=i * 10),
            RandomAgent(seed=i * 10 + 1),
            ShantenAgent(seed=i * 10 + 2),
            RandomAgent(seed=i * 10 + 3),
        ]
        game = GameRound(agents, wall_seed=i * 100)
        result = game.run()

        if result["type"] == "tsumo":
            winner = result["winner"]
            if winner in (0, 2):  # Shanten
                wins["shanten"] += 1
            else:  # Random
                wins["random"] += 1
        else:
            ryukyoku += 1

    total_agari = wins["shanten"] + wins["random"]
    print(f"ShantenAgent 和了: {wins['shanten']}局")
    print(f"RandomAgent  和了: {wins['random']}局")
    print(f"流局:              {ryukyoku}局")
    if total_agari > 0:
        pct = wins["shanten"] / total_agari * 100
        print(f"\n和了のうちShantenAgentの割合: {pct:.1f}%")
    print()


def test_shanten_only(num_games=100):
    """ShantenAgent 4人で対戦"""
    print(f"=== ShantenAgent 4人対戦 ({num_games}局) ===")

    tsumo = 0
    ryukyoku = 0
    total_turns = 0

    for i in range(num_games):
        agents = [ShantenAgent(seed=i * 10 + j) for j in range(4)]
        game = GameRound(agents, wall_seed=i * 100)
        result = game.run()

        if result["type"] == "tsumo":
            tsumo += 1
            total_turns += result["turn"]
        else:
            ryukyoku += 1

    print(f"ツモ和了: {tsumo}局")
    print(f"流局:     {ryukyoku}局")
    if tsumo > 0:
        print(f"平均和了巡目: {total_turns / tsumo:.1f}")
    print()


if __name__ == "__main__":
    test_shanten_only()
    test_shanten_vs_random()
