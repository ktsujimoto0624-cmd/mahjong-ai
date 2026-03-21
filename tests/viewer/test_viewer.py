"""棋譜記録とHTMLビューアのテスト"""

import os
from mahjong.game.round import GameRound
from agents import ShantenAgent
from viewer.game_viewer.generator import generate_html


def test_record_and_view():
    """ShantenAgent 4人で1局やって棋譜をHTMLに出力"""
    agents = [ShantenAgent(seed=i) for i in range(4)]
    game = GameRound(agents, wall_seed=42)
    result = game.run()

    # テキスト棋譜を表示
    print(game.record.to_text())

    # JSON保存
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "sample_record.json")
    game.record.save_json(json_path)
    print(f"\nJSON保存: {json_path}")

    # HTML出力
    html_path = os.path.join(out_dir, "sample_record.html")
    generate_html(game.record, html_path)
    print(f"HTML保存: {html_path}")
    print("\nブラウザで開いて確認してください。")
    print("操作: ← → キーでステップ移動、スペースで自動再生")


if __name__ == "__main__":
    test_record_and_view()
