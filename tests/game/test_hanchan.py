"""半荘（東風戦・東南戦）の進行管理テスト"""

from mahjong.game.hanchan import Hanchan
from agents import ShantenAgent


def test_tonpusen_completes():
    """東風戦が正常に完了する"""
    agents = [ShantenAgent(seed=i) for i in range(4)]
    hanchan = Hanchan(agents, mode="tonpusen", base_seed=42)
    result = hanchan.run()

    assert result["mode"] == "tonpusen"
    assert result["rounds_played"] >= 4  # 最低4局（連荘で増える）
    assert len(result["rankings"]) == 4
    assert len(result["points"]) == 4
    # 点数合計は100000（供託なければ保存）
    total = sum(result["points"]) + hanchan.riichi_pool
    assert total == 100000, f"点数合計が不正: {total}"


def test_tonnansen_completes():
    """東南戦が正常に完了する"""
    agents = [ShantenAgent(seed=i) for i in range(4)]
    hanchan = Hanchan(agents, mode="tonnansen", base_seed=100)
    result = hanchan.run()

    assert result["mode"] == "tonnansen"
    assert result["rounds_played"] >= 8
    total = sum(result["points"]) + hanchan.riichi_pool
    assert total == 100000


def test_dealer_rotation():
    """親が正しく交代する"""
    agents = [ShantenAgent(seed=i) for i in range(4)]
    hanchan = Hanchan(agents, mode="tonpusen", base_seed=42)
    hanchan.run()

    dealers_seen = set()
    for r in hanchan.round_results:
        dealers_seen.add(r["dealer"])

    # 東風戦なので少なくとも親が0から始まる
    assert 0 in dealers_seen


def test_points_never_created():
    """点数が無から生まれない（合計は常に100000）"""
    agents = [ShantenAgent(seed=i) for i in range(4)]
    hanchan = Hanchan(agents, mode="tonpusen", base_seed=77)
    hanchan.run()

    total = sum(hanchan.points) + hanchan.riichi_pool
    assert total == 100000, f"点数合計: {total}（供託: {hanchan.riichi_pool}）"


def test_round_wind_advances():
    """場風が東→南に進む（東南戦）"""
    agents = [ShantenAgent(seed=i) for i in range(4)]
    hanchan = Hanchan(agents, mode="tonnansen", base_seed=200)
    hanchan.run()

    winds_seen = set()
    for r in hanchan.round_results:
        winds_seen.add(r["round_wind"])

    # 東南戦では南場まで進むはず
    assert 0 in winds_seen  # 東場
    assert 1 in winds_seen  # 南場


def test_verbose_output(capsys):
    """verbose=Trueでログ出力される"""
    agents = [ShantenAgent(seed=i) for i in range(4)]
    hanchan = Hanchan(agents, mode="tonpusen", base_seed=42, verbose=True)
    hanchan.run()
    captured = capsys.readouterr()
    assert "東1局" in captured.out
    assert "点数" in captured.out


if __name__ == "__main__":
    # 手動実行用
    agents = [ShantenAgent(seed=i) for i in range(4)]
    hanchan = Hanchan(agents, mode="tonpusen", base_seed=42, verbose=True)
    result = hanchan.run()
    print(f"\n{'='*50}")
    print("=== 最終結果 ===")
    for rank, seat in enumerate(result["rankings"]):
        print(f"  {rank+1}位: {result['agents'][seat]} "
              f"({result['points'][seat]}点)")
    print(f"  対局数: {result['rounds_played']}")
