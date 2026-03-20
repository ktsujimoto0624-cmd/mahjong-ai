"""
棋譜HTMLビューア

棋譜をHTMLファイルとして出力し、ブラウザで視覚的に確認できるようにする。
巡目ごとにステップ再生でき、各プレイヤーの手牌・河をSVG牌画像で表示する。
"""

from mahjong.tile import TILE_NAMES, hand_to_str, NUM_TILE_TYPES
from mahjong.record import GameRecord


# 牌IDからSVGファイル名へのマッピング
TILE_SVG_FILES = [
    "Man1", "Man2", "Man3", "Man4", "Man5", "Man6", "Man7", "Man8", "Man9",
    "Pin1", "Pin2", "Pin3", "Pin4", "Pin5", "Pin6", "Pin7", "Pin8", "Pin9",
    "Sou1", "Sou2", "Sou3", "Sou4", "Sou5", "Sou6", "Sou7", "Sou8", "Sou9",
    "Ton", "Nan", "Shaa", "Pei", "Haku", "Hatsu", "Chun",
]


def generate_html(record, filepath, tiles_dir="tiles"):
    """
    棋譜からHTMLファイルを生成する。

    Args:
        record: GameRecordオブジェクト
        filepath: 出力先HTMLファイルパス
        tiles_dir: 牌画像ディレクトリの相対パス（HTML基準）
    """
    import json
    actions_json = json.dumps(record.actions, ensure_ascii=False)
    initial_hands_json = json.dumps(record.initial_hands)
    result_json = json.dumps(record.result, ensure_ascii=False)
    metadata_json = json.dumps(record.metadata, ensure_ascii=False)
    tile_names_js = str(TILE_NAMES)
    tile_svgs_js = str(TILE_SVG_FILES)

    html = _build_html(
        actions_json, initial_hands_json, result_json,
        metadata_json, tile_names_js, tile_svgs_js, tiles_dir,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


def _build_html(actions_json, initial_hands_json, result_json,
                metadata_json, tile_names_js, tile_svgs_js, tiles_dir):
    """HTML文字列を構築する"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>麻雀棋譜ビューア</title>
<style>
{_css()}
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

<div class="table">
    <div class="player player-north" id="player-2"></div>
    <div class="player player-west"  id="player-3"></div>
    <div class="center"><div class="center-info" id="center-info">巡目: 0</div></div>
    <div class="player player-east"  id="player-1"></div>
    <div class="player player-south" id="player-0"></div>
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

{_javascript()}
</script>
</body>
</html>"""


def _css():
    return """* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Meiryo', 'Yu Gothic', sans-serif; background: #1a472a; color: #fff; padding: 20px; }
h1 { text-align: center; margin-bottom: 10px; font-size: 20px; }
.meta { text-align: center; color: #aaa; margin-bottom: 15px; font-size: 13px; }

.controls { text-align: center; margin: 15px 0; }
.controls button {
    background: #2d6a3f; border: 1px solid #4a9; color: #fff;
    padding: 8px 18px; margin: 0 4px; cursor: pointer; border-radius: 4px; font-size: 14px;
}
.controls button:hover { background: #3a8a5f; }
.controls button:disabled { opacity: 0.4; cursor: default; }
.controls .step-info { display: inline-block; min-width: 120px; font-size: 14px; }

.table {
    display: grid;
    grid-template-areas: ".    north ." "west center east" ".    south .";
    grid-template-columns: 1fr 2fr 1fr;
    grid-template-rows: auto auto auto;
    gap: 10px; max-width: 1100px; margin: 0 auto;
}

.player { background: #0d2818; border: 1px solid #2a5; border-radius: 8px; padding: 12px; min-height: 120px; }
.player.active { border-color: #ff0; box-shadow: 0 0 10px rgba(255,255,0,0.3); }
.player.winner { border-color: #f44; box-shadow: 0 0 15px rgba(255,80,80,0.5); }
.player-north { grid-area: north; }
.player-east  { grid-area: east; }
.player-south { grid-area: south; }
.player-west  { grid-area: west; }

.center { grid-area: center; display: flex; align-items: center; justify-content: center; }
.center-info { background: #0a1f10; border-radius: 8px; padding: 15px; text-align: center; border: 1px solid #2a5; }

.player-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 13px; }
.seat-name { font-weight: bold; font-size: 15px; }
.agent-name { color: #8c8; font-size: 12px; }

.hand { margin: 5px 0; }
.hand-label { font-size: 11px; color: #8a8; margin-bottom: 3px; }
.tiles { display: flex; flex-wrap: wrap; gap: 2px; align-items: flex-end; }

.tile-img {
    height: 48px; width: auto; border-radius: 4px; transition: transform 0.1s;
    background: #f5f0e0; padding: 2px; border: 1px solid #bba;
}
.tile-img:hover { transform: translateY(-3px); }
.tile-img.draw-highlight {
    background: #fffbe6; box-shadow: 0 0 10px 3px #ffe066;
    border: 2px solid #ffcc00; border-radius: 5px;
}
.tile-img.discard-last {
    background: #ffe0e0; box-shadow: 0 0 8px 2px #ff6666;
    border: 2px solid #ff4444; border-radius: 5px;
}

.tile-img-small {
    height: 36px; width: auto; border-radius: 3px;
    background: #e8e0d0; padding: 1px; border: 1px solid #a99;
}
.tile-img-small.discard-last {
    background: #ffe0e0; box-shadow: 0 0 6px 2px #ff6666;
    border: 2px solid #ff4444; border-radius: 4px;
}

.river { display: flex; flex-wrap: wrap; gap: 2px; margin-top: 4px; }

.result-banner {
    text-align: center; margin: 15px 0; padding: 12px;
    background: #0d2818; border: 2px solid #f84; border-radius: 8px;
    font-size: 16px; display: none;
}

.credit { text-align: center; margin-top: 15px; font-size: 11px; color: #586; }
.credit a { color: #8b6; }"""


def _javascript():
    # JavaScriptはPythonのf-string内なので {{ }} でエスケープ
    return """
let step = -1;
let autoTimer = null;
let hands = [[], [], [], []];
let rivers = [[], [], [], []];
let lastDraw = [null, null, null, null];

document.getElementById("meta").textContent =
    "seed: " + (METADATA.wall_seed || "?") + " | " + AGENTS.join(" vs ");

function tileSvgUrl(tileId) {
    return TILES_DIR + "/" + TILE_SVGS[tileId] + ".svg";
}

function renderTile(tileId, cls) {
    return '<img class="tile-img ' + cls + '" src="' + tileSvgUrl(tileId) +
           '" alt="' + TILE_NAMES[tileId] + '" title="' + TILE_NAMES[tileId] + '">';
}

function renderTileSmall(tileId, cls) {
    return '<img class="tile-img-small ' + cls + '" src="' + tileSvgUrl(tileId) +
           '" alt="' + TILE_NAMES[tileId] + '" title="' + TILE_NAMES[tileId] + '">';
}

function resetState() {
    for (let s = 0; s < 4; s++) {
        hands[s] = INITIAL_HANDS[s].slice();
        rivers[s] = [];
        lastDraw[s] = null;
    }
}

function applyActions(upTo) {
    resetState();
    for (let i = 0; i <= upTo; i++) {
        let a = ACTIONS[i];
        if (a.type === "draw") {
            hands[a.seat][a.tile]++;
            lastDraw[a.seat] = a.tile;
        } else if (a.type === "discard") {
            hands[a.seat][a.tile]--;
            rivers[a.seat].push({ tile: a.tile, isLast: false });
            if (lastDraw[a.seat] === a.tile) lastDraw[a.seat] = null;
        }
    }
    for (let s = 0; s < 4; s++) {
        if (rivers[s].length > 0) {
            rivers[s][rivers[s].length - 1].isLast = (upTo >= 0);
        }
    }
}

function getCurrentTurn() {
    if (step < 0) return 0;
    let draws = [0, 0, 0, 0];
    for (let i = 0; i <= step; i++) {
        if (ACTIONS[i].type === "draw") draws[ACTIONS[i].seat]++;
    }
    return Math.max(0, Math.floor((Math.max(...draws) - 1)));
}

function getActiveSeat() {
    if (step < 0) return -1;
    return ACTIONS[step].seat;
}

function render() {
    if (step < 0) { resetState(); } else { applyActions(step); }

    let activeSeat = getActiveSeat();
    let isEnd = (step >= ACTIONS.length - 1) && RESULT;
    let winnerSeat = (RESULT && RESULT.type === "tsumo") ? RESULT.winner : -1;

    for (let s = 0; s < 4; s++) {
        let el = document.getElementById("player-" + s);
        el.className = "player player-" + ["south","east","north","west"][s];
        if (isEnd && s === winnerSeat) el.classList.add("winner");
        else if (s === activeSeat) el.classList.add("active");

        let html = '<div class="player-header">' +
            '<span class="seat-name">' + SEAT_NAMES[s] + '</span>' +
            '<span class="agent-name">' + AGENTS[s] + '</span></div>';

        // hand
        html += '<div class="hand"><div class="hand-label">手牌</div><div class="tiles">';
        for (let t = 0; t < 34; t++) {
            for (let c = 0; c < hands[s][t]; c++) {
                let cls = (lastDraw[s] === t && c === hands[s][t] - 1) ? "draw-highlight" : "";
                html += renderTile(t, cls);
            }
        }
        html += '</div></div>';

        // river
        html += '<div class="hand"><div class="hand-label">河（捨て牌）</div><div class="river">';
        for (let r = 0; r < rivers[s].length; r++) {
            let cls = rivers[s][r].isLast ? "discard-last" : "";
            html += renderTileSmall(rivers[s][r].tile, cls);
        }
        html += '</div></div>';

        el.innerHTML = html;
    }

    let turn = getCurrentTurn();
    document.getElementById("center-info").innerHTML =
        "<div>巡目: " + turn + "</div>" +
        "<div style='font-size:12px;color:#8a8;margin-top:5px;'>残り: " +
        (122 - countDraws()) + "枚</div>";

    let info = "配牌";
    if (step >= 0) {
        let a = ACTIONS[step];
        info = SEAT_NAMES[a.seat] + " " +
               (a.type === "draw" ? "ツモ " : "打 ") +
               TILE_NAMES[a.tile];
    }
    document.getElementById("step-info").textContent =
        (step + 1) + "/" + ACTIONS.length + " " + info;

    let banner = document.getElementById("result-banner");
    if (isEnd) {
        banner.style.display = "block";
        if (RESULT.type === "tsumo") {
            banner.innerHTML = "ツモ和了! " + SEAT_NAMES[RESULT.winner] +
                " (" + AGENTS[RESULT.winner] + ") " + RESULT.turn + "巡目" +
                " 和了牌: " + '<img class="tile-img" src="' +
                tileSvgUrl(RESULT.winning_tile) + '" style="vertical-align:middle;">';
        } else {
            banner.innerHTML = "流局 (" + RESULT.turn + "巡目)";
        }
    } else {
        banner.style.display = "none";
    }
    updateButtons();
}

function countDraws() {
    let c = 0;
    for (let i = 0; i <= step; i++) {
        if (ACTIONS[i].type === "draw") c++;
    }
    return c;
}

function updateButtons() {
    document.getElementById("btn-prev").disabled = (step < 0);
    document.getElementById("btn-start").disabled = (step < 0);
    document.getElementById("btn-next").disabled = (step >= ACTIONS.length - 1);
    document.getElementById("btn-end").disabled = (step >= ACTIONS.length - 1);
}

function goNext() { if (step < ACTIONS.length - 1) { step++; render(); } }
function goPrev() { if (step >= 0) { step--; render(); } }
function goStart() { step = -1; render(); }
function goEnd() { step = ACTIONS.length - 1; render(); }

function toggleAuto() {
    if (autoTimer) {
        clearInterval(autoTimer); autoTimer = null;
        document.getElementById("btn-auto").textContent = "自動再生";
    } else {
        autoTimer = setInterval(() => {
            if (step >= ACTIONS.length - 1) {
                clearInterval(autoTimer); autoTimer = null;
                document.getElementById("btn-auto").textContent = "自動再生";
                return;
            }
            goNext();
        }, 300);
        document.getElementById("btn-auto").textContent = "停止";
    }
}

document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") goNext();
    else if (e.key === "ArrowLeft") goPrev();
    else if (e.key === "Home") goStart();
    else if (e.key === "End") goEnd();
    else if (e.key === " ") { e.preventDefault(); toggleAuto(); }
});

render();
"""
