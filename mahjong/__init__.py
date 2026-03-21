"""
麻雀エンジンパッケージ

主要クラス・関数の再エクスポート（互換性レイヤー）
"""

from mahjong.engine.tile import *  # noqa: F401,F403
from mahjong.engine.wall import Wall  # noqa: F401
from mahjong.engine.player import Player  # noqa: F401
from mahjong.engine.agari import is_agari, shanten_number, decompose_regular  # noqa: F401
from mahjong.game.round import GameRound  # noqa: F401
from mahjong.scoring.yaku import judge_yaku  # noqa: F401
from mahjong.scoring.score import calculate_score  # noqa: F401
from mahjong.record.record import GameRecord  # noqa: F401
