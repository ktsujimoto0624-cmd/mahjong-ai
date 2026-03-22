"""
棋譜記録（GameRecord）

1局の全アクションを記録し、再生・保存・HTML出力できるようにする。
"""

import json
import os
from mahjong.engine.tile import tile_name, hand_to_str, TILE_NAMES, NUM_TILE_TYPES


class GameRecord:
    """1局の棋譜を記録するクラス"""

    def __init__(self):
        self.metadata = {}    # 局のメタ情報
        self.actions = []     # アクションのリスト
        self.initial_hands = []  # 配牌（4人分のカウント配列）
        self.result = None    # 局の結果

    def set_metadata(self, **kwargs):
        """メタ情報を設定（エージェント名、シード等）"""
        self.metadata.update(kwargs)

    def record_deal(self, hands):
        """配牌を記録"""
        self.initial_hands = [list(h) for h in hands]

    def record_draw(self, seat, tile_id):
        """ツモを記録"""
        self.actions.append({
            "type": "draw",
            "seat": seat,
            "tile": tile_id,
        })

    def record_discard(self, seat, tile_id, is_riichi=False):
        """打牌を記録"""
        self.actions.append({
            "type": "discard",
            "seat": seat,
            "tile": tile_id,
            "riichi": is_riichi,
        })

    def record_riichi(self, seat):
        """リーチ宣言を記録"""
        self.actions.append({
            "type": "riichi",
            "seat": seat,
        })

    def record_meld(self, seat, meld_type, tiles, from_seat, taken_tile):
        """
        副露（鳴き）を記録

        Args:
            seat: 鳴いたプレイヤーの席番号
            meld_type: "chi", "pon", "daiminkan", "ankan", "kakan"
            tiles: 副露の牌IDリスト
            from_seat: 鳴いた相手の席番号（ankanはNone）
            taken_tile: 鳴いた牌のID
        """
        self.actions.append({
            "type": "meld",
            "seat": seat,
            "meld_type": meld_type,
            "tiles": tiles,
            "from_seat": from_seat,
            "taken_tile": taken_tile,
        })

    def record_result(self, result):
        """局の結果を記録"""
        self.result = result

    def to_dict(self):
        """棋譜を辞書形式で返す"""
        return {
            "metadata": self.metadata,
            "initial_hands": self.initial_hands,
            "actions": self.actions,
            "result": self.result,
        }

    def save_json(self, filepath):
        """棋譜をJSONファイルに保存"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, filepath):
        """JSONファイルから棋譜を読み込む"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        rec = cls()
        rec.metadata = data["metadata"]
        rec.initial_hands = data["initial_hands"]
        rec.actions = data["actions"]
        rec.result = data["result"]
        return rec

    def to_mjai(self):
        """mjai形式のイベントリストとして返す"""
        from mahjong.record.mjai_converter import to_mjai
        return to_mjai(self)

    def to_mjai_string(self):
        """mjai形式のJSON Lines文字列として返す"""
        from mahjong.record.mjai_converter import to_mjai_string
        return to_mjai_string(self)

    def to_text(self):
        """棋譜をテキスト形式で出力"""
        seat_names = ["東", "南", "西", "北"]
        lines = []

        # メタ情報
        if self.metadata:
            for k, v in self.metadata.items():
                lines.append(f"# {k}: {v}")
            lines.append("")

        # 配牌
        lines.append("=== 配牌 ===")
        for seat in range(4):
            hand_str = hand_to_str(self.initial_hands[seat])
            agent = self.metadata.get("agents", ["?"] * 4)[seat]
            lines.append(f"  {seat_names[seat]}家 ({agent}): {hand_str}")
        lines.append("")

        # アクション
        lines.append("=== 進行 ===")
        turn = 0
        last_seat = -1
        for action in self.actions:
            seat = action["seat"]
            name = seat_names[seat]

            if action["type"] == "draw":
                if seat == 0 and last_seat != 0:
                    turn += 1
                t = tile_name(action["tile"])
                lines.append(f"[{turn:2d}巡] {name}家 ツモ:{t}")
            elif action["type"] == "riichi":
                lines.append(f"       {name}家 *** リーチ! ***")
            elif action["type"] == "discard":
                t = tile_name(action["tile"])
                riichi_mark = " (リーチ宣言牌)" if action.get("riichi") else ""
                lines.append(f"       {name}家 打 :{t}{riichi_mark}")
            elif action["type"] == "meld":
                mt = action["meld_type"]
                tiles_str = " ".join(tile_name(t) for t in action["tiles"])
                from_name = seat_names[action["from_seat"]] if action["from_seat"] is not None else ""
                label = {"chi": "チー", "pon": "ポン", "daiminkan": "大明槓",
                         "ankan": "暗槓", "kakan": "加槓"}[mt]
                src = f" ← {from_name}家" if from_name else ""
                lines.append(f"       {name}家 {label}{src} [{tiles_str}]")

            last_seat = seat
        lines.append("")

        # 結果
        if self.result:
            lines.append("=== 結果 ===")
            if self.result["type"] == "tsumo":
                winner = self.result["winner"]
                wt = tile_name(self.result["winning_tile"])
                lines.append(
                    f"  ツモ和了: {seat_names[winner]}家 "
                    f"({self.result['turn']}巡目) 和了牌:{wt}"
                )
            elif self.result["type"] == "ron":
                winner = self.result["winner"]
                from_p = self.result["from_player"]
                wt = tile_name(self.result["winning_tile"])
                lines.append(
                    f"  ロン和了: {seat_names[winner]}家 "
                    f"← {seat_names[from_p]}家 "
                    f"({self.result['turn']}巡目) 和了牌:{wt}"
                )
            else:
                lines.append(f"  流局 ({self.result['turn']}巡目)")

        return "\n".join(lines)
