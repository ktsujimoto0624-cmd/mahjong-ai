"""
棋譜HTMLビューア

棋譜をHTMLファイルとして出力し、ブラウザで視覚的に確認できるようにする。
実際の麻雀卓を上から見たレイアウト:
- テーブル中央に4人の河（捨て牌）
- 四辺に各プレイヤーの手牌
- 副露（鳴き）は各手牌エリアに表示
"""

import json
from mahjong.engine.tile import TILE_NAMES
from viewer.game_viewer.styles import get_css
from viewer.game_viewer.scripts import get_javascript

TILE_SVG_FILES = [
    "Man1", "Man2", "Man3", "Man4", "Man5", "Man6", "Man7", "Man8", "Man9",
    "Pin1", "Pin2", "Pin3", "Pin4", "Pin5", "Pin6", "Pin7", "Pin8", "Pin9",
    "Sou1", "Sou2", "Sou3", "Sou4", "Sou5", "Sou6", "Sou7", "Sou8", "Sou9",
    "Ton", "Nan", "Shaa", "Pei", "Haku", "Hatsu", "Chun",
]


def generate_html(record, filepath, tiles_dir="tiles"):
    actions_json = json.dumps(record.actions, ensure_ascii=False)
    initial_hands_json = json.dumps(record.initial_hands)
    result_json = json.dumps(record.result, ensure_ascii=False)
    metadata_json = json.dumps(record.metadata, ensure_ascii=False)
    tile_names_js = str(TILE_NAMES)
    tile_svgs_js = str(TILE_SVG_FILES)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>麻雀棋譜ビューア</title>
<style>
{get_css()}
</style>
</head>
<body>
<h1>麻雀棋譜ビューア</h1>
<div class="meta" id="meta"></div>
<div class="controls">
    <button id="btn-start" onclick="goStart()">|&lt;</button>
    <button id="btn-prev" onclick="goPrev()">&lt; 戻る</button>
    <span class="step-info" id="step-info">配牌</span>
    <button id="btn-next" onclick="goNext()">進む &gt;</button>
    <button id="btn-end" onclick="goEnd()">&gt;|</button>
    <button id="btn-auto" onclick="toggleAuto()">自動再生</button>
</div>

<!-- 麻雀卓レイアウト -->
<div class="mahjong-table">
    <!-- 対面(北=seat2) 手牌 -->
    <div class="hand-area hand-top" id="hand-2"></div>

    <!-- 中段: 左手(西=seat3) | 河エリア | 右手(東=seat1) -->
    <div class="middle-row">
        <div class="hand-area hand-left" id="hand-3"></div>
        <div class="river-table">
            <div class="river-area river-top" id="river-2"></div>
            <div class="river-middle">
                <div class="river-area river-left" id="river-3"></div>
                <div class="center-info" id="center-info"></div>
                <div class="river-area river-right" id="river-1"></div>
            </div>
            <div class="river-area river-bottom" id="river-0"></div>
        </div>
        <div class="hand-area hand-right" id="hand-1"></div>
    </div>

    <!-- 自分(南=seat0) 手牌 -->
    <div class="hand-area hand-bottom" id="hand-0"></div>
</div>

<div class="result-banner" id="result-banner"></div>

<script>
const TILES_DIR = "{tiles_dir}";
const TILE_NAMES = {tile_names_js};
const TILE_SVGS = {tile_svgs_js};
const ACTIONS = {actions_json};
const INITIAL_HANDS = {initial_hands_json};
const RESULT = {result_json};
const METADATA = {metadata_json};
const SEAT_NAMES = ["東家", "南家", "西家", "北家"];
const AGENTS = METADATA.agents || ["?","?","?","?"];
{get_javascript()}
</script>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
