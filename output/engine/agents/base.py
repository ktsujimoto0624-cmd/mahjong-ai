"""
エージェント（AI）の基底クラスとユーティリティ

全てのAIはAgentBaseを継承し、choose_discard()を実装する。
"""


_agent_counter = 0


def _next_agent_id():
    global _agent_counter
    _agent_counter += 1
    return _agent_counter


class AgentBase:
    """AIエージェントの基底クラス"""

    # サブクラスで上書きするメタ情報
    model = "base"          # モデル名（バージョン管理用）
    description = ""        # 戦略の概要説明

    def __init__(self, name=None):
        self.agent_id = _next_agent_id()
        self.agent_type = self.__class__.__name__
        self.name = name or f"{self.agent_type}#{self.agent_id}"

    @property
    def label(self):
        """表示用ラベル"""
        return self.name

    @property
    def info(self):
        """エージェント情報の辞書"""
        return {
            "name": self.name,
            "type": self.agent_type,
            "model": self.model,
            "description": self.description,
        }

    def choose_discard(self, player, game_state):
        """何を捨てるか決める。"""
        raise NotImplementedError

    def choose_riichi(self, player, game_state):
        """リーチ宣言するかどうか決める。"""
        return True

    def choose_discard_riichi(self, player, game_state):
        """リーチ宣言時にどの牌を捨てるか決める。"""
        return self.choose_discard(player, game_state)

    def choose_ron(self, player, tile, from_seat, game_state):
        """ロン和了するかどうか決める。"""
        return True

    def choose_pon(self, player, tile, from_seat, game_state):
        """ポンするかどうか決める。"""
        return False

    def choose_chi(self, player, tile, from_seat, game_state):
        """チーするかどうか決める。"""
        return None

    def choose_kan(self, player, tile, from_seat, game_state):
        """大明槓するかどうか決める。"""
        return False

    def choose_ankan(self, player, game_state):
        """暗槓するかどうか決める。"""
        return None

    def choose_kakan(self, player, game_state):
        """加槓するかどうか決める。"""
        return None
