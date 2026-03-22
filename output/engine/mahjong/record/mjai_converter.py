"""
mjai形式変換モジュール

SimMahjongのGameRecordとmjai形式（JSON Lines）の相互変換を行う。

mjai形式の仕様:
  - JSON Lines形式（1行1イベント）
  - イベントタイプ: start_game, start_kyoku, tsumo, dahai, pon, chi,
    kakan, ankan, daiminkan, reach, hora, ryukyoku, end_kyoku, end_game
  - 牌表記: "1m"-"9m", "1p"-"9p", "1s"-"9s", "E","S","W","N","P","F","C"

SimMahjongの牌 ID:
  0-8:   萬子 (1m-9m)
  9-17:  筒子 (1p-9p)
  18-26: 索子 (1s-9s)
  27-33: 字牌 (東南西北白發中)
"""

import json


# --- 牌表記の変換テーブル ---

# SimMahjong牌ID → mjai牌表記
_TILE_ID_TO_MJAI = [
    "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
    "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
    "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
    "E", "S", "W", "N", "P", "F", "C",
]

# mjai牌表記 → SimMahjong牌ID
_MJAI_TO_TILE_ID = {name: i for i, name in enumerate(_TILE_ID_TO_MJAI)}

# 場風のマッピング
_WIND_TO_MJAI = {0: "E", 1: "S", 2: "W", 3: "N"}
_MJAI_TO_WIND = {"E": 0, "S": 1, "W": 2, "N": 3}


def tile_id_to_mjai(tile_id):
    """SimMahjong牌IDをmjai牌表記に変換する"""
    if tile_id < 0 or tile_id >= len(_TILE_ID_TO_MJAI):
        raise ValueError(f"Invalid tile_id: {tile_id}")
    return _TILE_ID_TO_MJAI[tile_id]


def mjai_to_tile_id(mjai_tile):
    """mjai牌表記をSimMahjong牌IDに変換する"""
    if mjai_tile not in _MJAI_TO_TILE_ID:
        raise ValueError(f"Invalid mjai tile: {mjai_tile}")
    return _MJAI_TO_TILE_ID[mjai_tile]


def _hand_counts_to_tile_list(hand_counts):
    """カウント配列を牌IDリストに変換する"""
    tiles = []
    for tile_id, count in enumerate(hand_counts):
        for _ in range(count):
            tiles.append(tile_id)
    return tiles


def _tile_list_to_hand_counts(tile_ids, size=34):
    """牌IDリストをカウント配列に変換する"""
    counts = [0] * size
    for tile_id in tile_ids:
        counts[tile_id] += 1
    return counts


def to_mjai(game_record):
    """
    GameRecordからmjai形式のイベントリストに変換する。

    Args:
        game_record: GameRecordインスタンス（またはto_dict()の辞書）

    Returns:
        list[dict]: mjaiイベントの辞書リスト
    """
    if hasattr(game_record, "to_dict"):
        data = game_record.to_dict()
    else:
        data = game_record

    metadata = data.get("metadata", {})
    initial_hands = data.get("initial_hands", [])
    actions = data.get("actions", [])
    result = data.get("result", {})

    events = []

    # start_game
    agent_names = metadata.get("agents", ["player0", "player1", "player2", "player3"])
    events.append({
        "type": "start_game",
        "names": list(agent_names),
    })

    # start_kyoku
    bakaze = _WIND_TO_MJAI.get(metadata.get("round_wind", 0), "E")
    dealer = metadata.get("dealer", 0)
    kyoku = metadata.get("round_number", 1)
    honba = metadata.get("honba", 0)
    kyotaku = metadata.get("riichi_pool", 0)
    dora_markers = [
        tile_id_to_mjai(d)
        for d in metadata.get("dora_indicators", [])
    ]

    # 配牌をmjai形式に変換
    tehais = []
    for hand in initial_hands:
        tile_list = _hand_counts_to_tile_list(hand)
        tehais.append([tile_id_to_mjai(t) for t in tile_list])

    events.append({
        "type": "start_kyoku",
        "bakaze": bakaze,
        "dora_marker": dora_markers[0] if dora_markers else "1m",
        "kyoku": kyoku,
        "honba": honba,
        "kyotaku": kyotaku,
        "oya": dealer,
        "tehais": tehais,
    })

    # アクションを変換
    for action in actions:
        action_type = action["type"]
        seat = action["seat"]

        if action_type == "draw":
            events.append({
                "type": "tsumo",
                "actor": seat,
                "pai": tile_id_to_mjai(action["tile"]),
            })

        elif action_type == "riichi":
            events.append({
                "type": "reach",
                "actor": seat,
            })

        elif action_type == "discard":
            pai = tile_id_to_mjai(action["tile"])
            tsumogiri = False
            events.append({
                "type": "dahai",
                "actor": seat,
                "pai": pai,
                "tsumogiri": tsumogiri,
            })

        elif action_type == "meld":
            meld_type = action["meld_type"]
            tiles = action["tiles"]
            from_seat = action.get("from_seat")
            taken_tile = action.get("taken_tile")

            if meld_type == "chi":
                consumed = [
                    tile_id_to_mjai(t)
                    for t in tiles if t != taken_tile
                ]
                events.append({
                    "type": "chi",
                    "actor": seat,
                    "target": from_seat,
                    "pai": tile_id_to_mjai(taken_tile),
                    "consumed": consumed,
                })

            elif meld_type == "pon":
                consumed = [
                    tile_id_to_mjai(t)
                    for t in tiles if t != taken_tile
                ]
                events.append({
                    "type": "pon",
                    "actor": seat,
                    "target": from_seat,
                    "pai": tile_id_to_mjai(taken_tile),
                    "consumed": consumed,
                })

            elif meld_type == "daiminkan":
                consumed = [
                    tile_id_to_mjai(t)
                    for t in tiles if t != taken_tile
                ]
                events.append({
                    "type": "daiminkan",
                    "actor": seat,
                    "target": from_seat,
                    "pai": tile_id_to_mjai(taken_tile),
                    "consumed": consumed,
                })

            elif meld_type == "ankan":
                events.append({
                    "type": "ankan",
                    "actor": seat,
                    "consumed": [tile_id_to_mjai(t) for t in tiles],
                })

            elif meld_type == "kakan":
                events.append({
                    "type": "kakan",
                    "actor": seat,
                    "pai": tile_id_to_mjai(taken_tile),
                    "consumed": [
                        tile_id_to_mjai(t)
                        for t in tiles if t != taken_tile
                    ],
                })

    # 結果イベント
    if result:
        result_type = result.get("type")
        if result_type in ("tsumo", "ron"):
            winner = result["winner"]
            winning_tile = tile_id_to_mjai(result["winning_tile"])
            score_info = result.get("score", {})
            yaku_list = score_info.get("yaku", [])

            hora_event = {
                "type": "hora",
                "actor": winner,
                "pai": winning_tile,
                "uradora_markers": [],
                "who": winner,
            }

            if result_type == "ron":
                hora_event["target"] = result["from_player"]
            else:
                hora_event["target"] = winner

            # 役情報
            if yaku_list:
                hora_event["yakus"] = [
                    y[0] if isinstance(y, (list, tuple)) else y
                    for y in yaku_list
                ]

            # 点数
            payments = score_info.get("payments", {})
            if payments:
                hora_event["ten"] = payments.get("total", 0)

            events.append(hora_event)

        elif result_type == "ryukyoku":
            events.append({
                "type": "ryukyoku",
            })

    # end_kyoku, end_game
    events.append({"type": "end_kyoku"})
    events.append({"type": "end_game"})

    return events


def to_mjai_string(game_record):
    """
    GameRecordをmjai形式のJSON Lines文字列に変換する。

    Args:
        game_record: GameRecordインスタンス（またはto_dict()の辞書）

    Returns:
        str: JSON Lines形式の文字列（.mjsonファイルの内容）
    """
    mjai_events = to_mjai(game_record)
    lines = [json.dumps(event, ensure_ascii=False) for event in mjai_events]
    return "\n".join(lines)


def from_mjai(events):
    """
    mjai形式のイベントリストからGameRecordに変換する。

    Args:
        events: list[dict] mjaiイベントの辞書リスト

    Returns:
        GameRecord: 変換されたGameRecordインスタンス
    """
    from mahjong.record.record import GameRecord

    record = GameRecord()

    for event in events:
        event_type = event.get("type")

        if event_type == "start_game":
            names = event.get("names", [])
            if names:
                record.set_metadata(agents=names)

        elif event_type == "start_kyoku":
            bakaze_str = event.get("bakaze", "E")
            round_wind = _MJAI_TO_WIND.get(bakaze_str, 0)
            dealer = event.get("oya", 0)
            kyoku = event.get("kyoku", 1)
            honba = event.get("honba", 0)
            kyotaku = event.get("kyotaku", 0)
            dora_marker = event.get("dora_marker")

            record.set_metadata(
                round_wind=round_wind,
                dealer=dealer,
                round_number=kyoku,
                honba=honba,
                riichi_pool=kyotaku,
            )
            if dora_marker:
                record.set_metadata(
                    dora_indicators=[mjai_to_tile_id(dora_marker)],
                )

            # 配牌
            tehais = event.get("tehais", [])
            hands = []
            for tehai in tehais:
                tile_ids = [mjai_to_tile_id(t) for t in tehai]
                hands.append(_tile_list_to_hand_counts(tile_ids))
            if hands:
                record.record_deal(hands)

        elif event_type == "tsumo":
            actor = event["actor"]
            pai = mjai_to_tile_id(event["pai"])
            record.record_draw(actor, pai)

        elif event_type == "dahai":
            actor = event["actor"]
            pai = mjai_to_tile_id(event["pai"])
            record.record_discard(actor, pai)

        elif event_type == "reach":
            actor = event["actor"]
            record.record_riichi(actor)

        elif event_type == "chi":
            actor = event["actor"]
            target = event.get("target")
            pai = mjai_to_tile_id(event["pai"])
            consumed = [mjai_to_tile_id(t) for t in event.get("consumed", [])]
            all_tiles = [pai] + consumed
            record.record_meld(actor, "chi", all_tiles, target, pai)

        elif event_type == "pon":
            actor = event["actor"]
            target = event.get("target")
            pai = mjai_to_tile_id(event["pai"])
            consumed = [mjai_to_tile_id(t) for t in event.get("consumed", [])]
            all_tiles = [pai] + consumed
            record.record_meld(actor, "pon", all_tiles, target, pai)

        elif event_type == "daiminkan":
            actor = event["actor"]
            target = event.get("target")
            pai = mjai_to_tile_id(event["pai"])
            consumed = [mjai_to_tile_id(t) for t in event.get("consumed", [])]
            all_tiles = [pai] + consumed
            record.record_meld(actor, "daiminkan", all_tiles, target, pai)

        elif event_type == "ankan":
            actor = event["actor"]
            consumed = [mjai_to_tile_id(t) for t in event.get("consumed", [])]
            taken = consumed[0] if consumed else None
            record.record_meld(actor, "ankan", consumed, None, taken)

        elif event_type == "kakan":
            actor = event["actor"]
            pai = mjai_to_tile_id(event["pai"])
            consumed = [mjai_to_tile_id(t) for t in event.get("consumed", [])]
            all_tiles = [pai] + consumed
            record.record_meld(actor, "kakan", all_tiles, None, pai)

        elif event_type == "hora":
            winner = event.get("actor", event.get("who"))
            target = event.get("target")
            pai = mjai_to_tile_id(event["pai"])
            is_tsumo = (winner == target)

            result = {
                "type": "tsumo" if is_tsumo else "ron",
                "winner": winner,
                "winning_tile": pai,
                "turn": 0,
            }
            if not is_tsumo:
                result["from_player"] = target

            ten = event.get("ten", 0)
            yakus = event.get("yakus", [])
            if ten or yakus:
                result["score"] = {
                    "yaku": [[y, 0] for y in yakus],
                    "payments": {"total": ten},
                }

            record.record_result(result)

        elif event_type == "ryukyoku":
            record.record_result({
                "type": "ryukyoku",
                "turn": 0,
            })

    return record


def from_mjai_string(mjai_string):
    """
    mjai形式のJSON Lines文字列からGameRecordに変換する。

    Args:
        mjai_string: JSON Lines形式の文字列

    Returns:
        GameRecord: 変換されたGameRecordインスタンス
    """
    events = []
    for line in mjai_string.strip().split("\n"):
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return from_mjai(events)


def records_to_mjai_string(records):
    """
    複数のGameRecordをmjai形式のJSON Lines文字列に変換する。
    半荘全体（複数局）を1つの.mjsonファイルにまとめる。

    Args:
        records: list[GameRecord] or list[dict] 局ごとのGameRecordリスト

    Returns:
        str: JSON Lines形式の文字列
    """
    if not records:
        return ""

    all_lines = []

    # 最初のrecordからstart_gameイベントを生成
    first = records[0]
    if hasattr(first, "to_dict"):
        first_data = first.to_dict()
    else:
        first_data = first

    agents = first_data.get("metadata", {}).get(
        "agents", ["player0", "player1", "player2", "player3"]
    )
    all_lines.append(json.dumps({
        "type": "start_game",
        "names": list(agents),
    }, ensure_ascii=False))

    # 各局のイベントを追加（start_game/end_gameは除外）
    for rec in records:
        mjai_events = to_mjai(rec)
        for event in mjai_events:
            if event["type"] in ("start_game", "end_game"):
                continue
            all_lines.append(json.dumps(event, ensure_ascii=False))

    # end_game
    all_lines.append(json.dumps({"type": "end_game"}, ensure_ascii=False))

    return "\n".join(all_lines)
