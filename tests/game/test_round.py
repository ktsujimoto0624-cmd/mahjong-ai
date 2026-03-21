"""ゲームループのテスト: ランダムエージェント4人で対局"""

from mahjong.game.round import GameRound
from agents import RandomAgent, ShantenAgent


def test_single_round():
    """1局を実行"""
    print("=== 1局テスト（詳細表示） ===")
    agents = [RandomAgent(seed=i) for i in range(4)]
    game = GameRound(agents, wall_seed=42, verbose=True)
    result = game.run()
    print(f"\n結果: {result}")
    print()


def test_many_rounds():
    """100局を実行して統計を取る"""
    print("=== 100局統計テスト ===")
    tsumo_count = 0
    ryukyoku_count = 0
    winner_counts = [0, 0, 0, 0]

    for i in range(100):
        agents = [RandomAgent(seed=i * 4 + j) for j in range(4)]
        game = GameRound(agents, wall_seed=i * 100)
        result = game.run()

        if result["type"] == "tsumo":
            tsumo_count += 1
            winner_counts[result["winner"]] += 1
        else:
            ryukyoku_count += 1

    print(f"ツモ和了: {tsumo_count}局")
    print(f"流局:     {ryukyoku_count}局")
    print(f"和了者別: 東={winner_counts[0]} 南={winner_counts[1]} "
          f"西={winner_counts[2]} 北={winner_counts[3]}")
    print("OK\n")


def test_riichi():
    """リーチ宣言のテスト: ShantenAgent同士で対局しリーチが発生する"""
    print("=== リーチテスト ===")
    riichi_count = 0
    games_with_riichi = 0

    for i in range(50):
        agents = [ShantenAgent(seed=i * 4 + j) for j in range(4)]
        game = GameRound(agents, wall_seed=i)
        game.run()

        riichi_actions = [a for a in game.record.actions if a["type"] == "riichi"]
        if riichi_actions:
            games_with_riichi += 1
            riichi_count += len(riichi_actions)

        # リーチ宣言した人はis_riichiフラグが立っている
        for p in game.players:
            if p.is_riichi:
                assert p.riichi_turn >= 0

    print(f"リーチ発生局: {games_with_riichi}/50")
    print(f"リーチ宣言数: {riichi_count}")
    assert games_with_riichi > 0, "50局中リーチが1回も出ないのは異常"
    print("OK\n")


if __name__ == "__main__":
    test_single_round()
    test_many_rounds()
    test_riichi()
