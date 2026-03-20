"""Phase 1 基本動作テスト: 牌・山・プレイヤーの動作確認"""

from mahjong.tile import tile_name, hand_to_str, is_man, is_honor, suit_number
from mahjong.wall import Wall
from mahjong.player import Player


def test_tile_basics():
    """牌の基本機能テスト"""
    print("=== 牌の基本テスト ===")
    print(f"牌ID 0 = {tile_name(0)}")   # 1m
    print(f"牌ID 9 = {tile_name(9)}")   # 1p
    print(f"牌ID 27 = {tile_name(27)}")  # 東
    print(f"牌ID 33 = {tile_name(33)}")  # 中

    assert is_man(0) and is_man(8)
    assert not is_man(9)
    assert is_honor(27) and is_honor(33)
    assert suit_number(0) == 1
    assert suit_number(8) == 9
    print("OK\n")


def test_wall():
    """山のテスト"""
    print("=== 山のテスト ===")
    wall = Wall(seed=42)
    print(f"残り枚数: {wall.remaining()}")  # 122 (136 - 14王牌)

    # 全部ツモってみる
    drawn = []
    while True:
        tile = wall.draw()
        if tile is None:
            break
        drawn.append(tile)

    print(f"ツモった枚数: {len(drawn)}")  # 122
    assert len(drawn) == 122

    # 各牌種が4枚あるか確認（王牌にある分を除くと合計は一致しないが、
    # 全136枚中の配分は正しいはず）
    print(f"ドラ表示牌: {[tile_name(t) for t in wall.get_dora_indicators()]}")
    print("OK\n")


def test_deal():
    """配牌テスト: 4人に13枚ずつ配る"""
    print("=== 配牌テスト ===")
    wall = Wall(seed=123)
    players = [Player(seat=i) for i in range(4)]

    # 配牌: 各プレイヤーに13枚
    for _ in range(13):
        for p in players:
            tile = wall.draw()
            p.draw_tile(tile)

    for p in players:
        print(p)
        assert p.closed_tile_count() == 13

    print(f"\n山の残り: {wall.remaining()}枚")
    print("OK\n")


def test_discard():
    """打牌テスト"""
    print("=== 打牌テスト ===")
    wall = Wall(seed=456)
    player = Player(seat=0)

    # 13枚配る
    for _ in range(13):
        tile = wall.draw()
        player.draw_tile(tile)

    print(f"配牌: {player}")

    # 1枚ツモって1枚捨てる
    drawn = wall.draw()
    player.draw_tile(drawn)
    print(f"ツモ: {tile_name(drawn)}")

    # 手牌にある牌の中から最初の1枚を捨てる
    discard = player.hand_tiles()[0]
    player.discard_tile(discard)
    print(f"打牌: {tile_name(discard)}")
    print(f"結果: {player}")
    print(f"河: {[tile_name(t) for t in player.discards]}")

    assert player.closed_tile_count() == 13
    print("OK\n")


if __name__ == "__main__":
    test_tile_basics()
    test_wall()
    test_deal()
    test_discard()
    print("全テスト合格!")
