"""ビューアのJavaScript定義"""


def get_javascript():
    return """
let step = -1;
let autoTimer = null;
let hands = [[], [], [], []];
let rivers = [[], [], [], []];
let melds = [[], [], [], []];
let lastDraw = [null, null, null, null];
let riichiState = [false, false, false, false];

document.getElementById("meta").textContent =
    "seed: " + (METADATA.wall_seed || "?") + " | " + AGENTS.join(" vs ");

function tileSvgUrl(id) { return TILES_DIR + "/" + TILE_SVGS[id] + ".svg"; }

function tileImg(id, cls) {
    return '<img class="tile-img ' + cls + '" src="' + tileSvgUrl(id) +
           '" title="' + TILE_NAMES[id] + '">';
}
function tileVert(id, cls) {
    return '<img class="tile-vert ' + cls + '" src="' + tileSvgUrl(id) +
           '" title="' + TILE_NAMES[id] + '">';
}
function tileRiver(id, cls) {
    return '<img class="tile-river ' + cls + '" src="' + tileSvgUrl(id) +
           '" title="' + TILE_NAMES[id] + '">';
}
function tileRiverVert(id, cls) {
    return '<img class="tile-river-vert ' + cls + '" src="' + tileSvgUrl(id) +
           '" title="' + TILE_NAMES[id] + '">';
}

function resetState() {
    for (let s = 0; s < 4; s++) {
        hands[s] = INITIAL_HANDS[s].slice();
        rivers[s] = [];
        melds[s] = [];
        lastDraw[s] = null;
        riichiState[s] = false;
    }
}

function applyActions(upTo) {
    resetState();
    for (let i = 0; i <= upTo; i++) {
        let a = ACTIONS[i];
        if (a.type === "draw") {
            hands[a.seat][a.tile]++;
            lastDraw[a.seat] = a.tile;
        } else if (a.type === "riichi") {
            riichiState[a.seat] = true;
        } else if (a.type === "discard") {
            hands[a.seat][a.tile]--;
            rivers[a.seat].push({ tile: a.tile, isLast: false, riichi: !!a.riichi });
            if (lastDraw[a.seat] === a.tile) lastDraw[a.seat] = null;
        } else if (a.type === "meld") {
            let mt = a.meld_type;
            let tiles = a.tiles;
            let taken = a.taken_tile;
            if (mt === "chi") {
                for (let t of tiles) {
                    if (t !== taken) hands[a.seat][t]--;
                }
            } else if (mt === "pon") {
                hands[a.seat][taken] -= 2;
            } else if (mt === "daiminkan") {
                hands[a.seat][taken] -= 3;
            } else if (mt === "ankan") {
                hands[a.seat][taken] -= 4;
            } else if (mt === "kakan") {
                hands[a.seat][taken] -= 1;
                for (let m of melds[a.seat]) {
                    if (m.meld_type === "pon" && m.tiles[0] === taken) {
                        m.meld_type = "kakan";
                        m.tiles.push(taken);
                    }
                }
            }
            if (mt !== "kakan") {
                melds[a.seat].push({
                    meld_type: mt, tiles: tiles,
                    from_seat: a.from_seat, taken_tile: taken
                });
            }
            if (a.from_seat !== null && a.from_seat !== undefined
                && mt !== "ankan" && mt !== "kakan") {
                let fromRiver = rivers[a.from_seat];
                if (fromRiver.length > 0) fromRiver.pop();
            }
        }
    }
    for (let s = 0; s < 4; s++) {
        if (rivers[s].length > 0)
            rivers[s][rivers[s].length - 1].isLast = true;
    }
}

function getCurrentTurn() {
    if (step < 0) return 0;
    let draws = [0, 0, 0, 0];
    for (let i = 0; i <= step; i++) {
        if (ACTIONS[i].type === "draw") draws[ACTIONS[i].seat]++;
    }
    return Math.max(0, Math.max(...draws) - 1);
}

function getActiveSeat() {
    if (step < 0) return -1;
    return ACTIONS[step].seat;
}

function renderHand(seat, isVertical) {
    let html = '';
    let reversed = (seat === 1);
    let start = reversed ? 33 : 0;
    let end = reversed ? -1 : 34;
    let step = reversed ? -1 : 1;
    for (let t = start; t !== end; t += step) {
        for (let c = 0; c < hands[seat][t]; c++) {
            let cls = (lastDraw[seat] === t && c === hands[seat][t] - 1) ? "draw-highlight" : "";
            html += isVertical ? tileVert(t, cls) : tileImg(t, cls);
        }
    }
    return html;
}

function renderRiver(seat, isVertical) {
    let tiles = rivers[seat];
    let html = '';
    for (let r = 0; r < tiles.length; r++) {
        let cls = tiles[r].isLast ? "discard-last" : "";
        if (tiles[r].riichi) cls += " riichi-tile";
        html += isVertical ? tileRiverVert(tiles[r].tile, cls) :
                             tileRiver(tiles[r].tile, cls);
    }
    return html;
}

function renderMelds(seat, isVertical) {
    let seatMelds = melds[seat];
    if (seatMelds.length === 0) return '';
    let html = '';
    let tCls = isVertical ? 'tile-meld-vert' : 'tile-meld';

    function meldTile(tid, extra, lbl) {
        return '<img class="' + tCls + ' ' + extra +
            '" src="' + tileSvgUrl(tid) +
            '" title="' + lbl + ' ' + TILE_NAMES[tid] + '">';
    }

    for (let m of seatMelds) {
        html += '<span class="meld-group">';
        let label = {
            chi:"\\u30C1\\u30FC", pon:"\\u30DD\\u30F3",
            daiminkan:"\\u660E\\u69FB", ankan:"\\u6697\\u69FB",
            kakan:"\\u52A0\\u69FB"
        }[m.meld_type] || "";

        if (m.meld_type === 'ankan') {
            for (let i = 0; i < 4; i++) {
                let cls = (i === 0 || i === 3) ? 'meld-facedown' : '';
                html += meldTile(m.tiles[i], cls, label);
            }
        } else {
            let relPos = (m.from_seat - seat + 4) % 4;
            let swPos = relPos === 3 ? 0 : relPos === 2 ? 1 : 2;

            if (m.meld_type === 'chi') {
                html += meldTile(m.taken_tile, 'tile-sideways', label);
                let rest = m.tiles.filter(function(t) {
                    return t !== m.taken_tile;
                }).sort(function(a, b) { return a - b; });
                for (let j = 0; j < rest.length; j++) {
                    html += meldTile(rest[j], '', label);
                }
            } else if (m.meld_type === 'pon') {
                for (let i = 0; i < 3; i++) {
                    let cls = (i === swPos) ? 'tile-sideways' : '';
                    html += meldTile(m.tiles[i], cls, label);
                }
            } else if (m.meld_type === 'daiminkan' || m.meld_type === 'kakan') {
                for (let i = 0; i < 3; i++) {
                    if (i === swPos) {
                        html += '<span class="kakan-stack">' +
                            meldTile(m.tiles[i], 'tile-sideways', label) +
                            meldTile(m.tiles[3], 'tile-stacked', label) +
                            '</span>';
                    } else {
                        html += meldTile(m.tiles[i], '', label);
                    }
                }
            }
        }
        html += '</span>';
    }
    return html;
}

function render() {
    if (step < 0) { resetState(); } else { applyActions(step); }
    let active = getActiveSeat();
    let isEnd = (step >= ACTIONS.length - 1) && RESULT;
    let winner = (RESULT && (RESULT.type === "tsumo" || RESULT.type === "ron"))
        ? RESULT.winner : -1;

    let positions = [
        { seat: 2, id: "hand-2", pos: "hand-top", vertical: false },
        { seat: 3, id: "hand-3", pos: "hand-left", vertical: true },
        { seat: 1, id: "hand-1", pos: "hand-right", vertical: true },
        { seat: 0, id: "hand-0", pos: "hand-bottom", vertical: false },
    ];

    for (let p of positions) {
        let el = document.getElementById(p.id);
        el.className = "hand-area " + p.pos;
        if (isEnd && p.seat === winner) el.classList.add("winner");
        else if (p.seat === active) el.classList.add("active");

        let dealer = METADATA.dealer || 0;
        let seatWind = (p.seat - dealer + 4) % 4;
        let windName = ["\\u6771","\\u5357","\\u897F","\\u5317"][seatWind];
        let isDealer = (p.seat === dealer);
        let dealerMark = isDealer ? '<span class="dealer-mark">\\u89AA</span>' : '';
        let rMark = riichiState[p.seat]
            ? '<span class="riichi-mark">\\u30EA\\u30FC\\u30C1</span>' : '';
        let pts = (METADATA.points) ? METADATA.points[p.seat] : '';
        let ptsHtml = pts !== '' ? '<span class="pts">' + pts + '</span>' : '';
        let label = '<div class="hand-label">' +
            '<span>' + windName + dealerMark + rMark + '</span>' +
            '<span class="agent">' + AGENTS[p.seat] + '</span>' +
            ptsHtml + '</div>';
        let meldsHtml = renderMelds(p.seat, p.vertical);
        let meldsDiv = meldsHtml
            ? '<div class="melds-area">' + meldsHtml + '</div>' : '';
        let tiles = '<div class="hand-tiles">' +
            '<div class="hand-pure">' + renderHand(p.seat, p.vertical) + '</div>' +
            meldsDiv + '</div>';
        el.innerHTML = label + tiles;
    }

    let riverConfigs = [
        { seat: 2, id: "river-2", vertical: false },
        { seat: 3, id: "river-3", vertical: true },
        { seat: 1, id: "river-1", vertical: true },
        { seat: 0, id: "river-0", vertical: false },
    ];
    for (let rc of riverConfigs) {
        document.getElementById(rc.id).innerHTML = renderRiver(rc.seat, rc.vertical);
    }

    let turn = getCurrentTurn();
    let windNames = ["\\u6771","\\u5357","\\u897F","\\u5317"];
    let rw = METADATA.round_wind || 0;
    let rn = (METADATA.round_number || 0) + 1;
    let honba = METADATA.honba || 0;
    let pool = METADATA.riichi_pool || 0;
    let roundLabel = windNames[rw] + rn + "\\u5C40";
    if (honba > 0) roundLabel += " " + honba + "\\u672C\\u5834";

    let doraHtml = '';
    let doraList = METADATA.dora_indicators || [];
    let kanCount = 0;
    for (let i = 0; i <= step && i < ACTIONS.length; i++) {
        if (ACTIONS[i].type === 'meld' &&
            (ACTIONS[i].meld_type === 'ankan' || ACTIONS[i].meld_type === 'daiminkan'
             || ACTIONS[i].meld_type === 'kakan')) kanCount++;
    }
    for (let d = 0; d < Math.min(doraList.length, 1 + kanCount); d++) {
        doraHtml += '<img class="tile-dora" src="' + tileSvgUrl(doraList[d]) +
            '" title="\\u30C9\\u30E9\\u8868\\u793A\\u724C">';
    }
    for (let d = Math.min(doraList.length, 1 + kanCount); d < 5; d++) {
        doraHtml += '<span class="tile-dora tile-dora-hidden"></span>';
    }

    let centerHtml =
        '<div class="center-round">' + roundLabel + '</div>' +
        '<div class="center-dora"><span class="dora-label">\\u30C9\\u30E9</span>' +
        doraHtml + '</div>' +
        '<div class="center-sticks">' +
        (honba > 0 ? '<span class="stick-honba">' + honba +
            '\\u672C\\u5834</span>' : '') +
        (pool > 0 ? '<span class="stick-riichi">\\u4F9B\\u8A17' + pool +
            '\\u70B9</span>' : '') +
        '</div>' +
        '<div class="center-stats">' +
        '<span>\\u5DE1\\u76EE:' + turn + '</span>' +
        '<span>\\u6B8B:' + (122 - countDraws()) + '</span>' +
        '</div>';
    document.getElementById("center-info").innerHTML = centerHtml;

    let info = "\\u914D\\u724C";
    if (step >= 0) {
        let a = ACTIONS[step];
        if (a.type === "riichi") {
            info = SEAT_NAMES[a.seat] + " \\u30EA\\u30FC\\u30C1!";
        } else if (a.type === "meld") {
            let mLabel = {
                chi:"\\u30C1\\u30FC", pon:"\\u30DD\\u30F3",
                daiminkan:"\\u660E\\u69FB", ankan:"\\u6697\\u69FB",
                kakan:"\\u52A0\\u69FB"
            }[a.meld_type] || "";
            info = SEAT_NAMES[a.seat] + " " + mLabel + "! " + TILE_NAMES[a.taken_tile];
        } else {
            info = SEAT_NAMES[a.seat] + " " +
                   (a.type === "draw" ? "\\u30C4\\u30E2 " : "\\u6253 ") +
                   TILE_NAMES[a.tile];
        }
    }
    document.getElementById("step-info").textContent =
        (step + 1) + "/" + ACTIONS.length + " " + info;

    let banner = document.getElementById("result-banner");
    if (isEnd) {
        banner.style.display = "block";
        let bHtml = '';
        if (RESULT.type === "tsumo" || RESULT.type === "ron") {
            let wSeat = RESULT.winner;
            let wDealer = METADATA.dealer || 0;
            let wWind = ["\\u6771","\\u5357","\\u897F","\\u5317"][(wSeat - wDealer + 4) % 4];
            let typeLabel = RESULT.type === "tsumo"
                ? "\\u30C4\\u30E2\\u548C\\u4E86" : "\\u30ED\\u30F3\\u548C\\u4E86";
            bHtml += '<div class="result-title">' + typeLabel + '!</div>';
            bHtml += '<div class="result-winner">' + wWind +
                '\\u5BB6 ' + AGENTS[wSeat];
            if (RESULT.type === "ron") {
                let fWind = ["\\u6771","\\u5357","\\u897F","\\u5317"][
                    (RESULT.from_player - wDealer + 4) % 4];
                bHtml += ' \\u2190 ' + fWind + '\\u5BB6\\u653E\\u9283';
            }
            bHtml += '</div>';
            bHtml += '<div class="result-tile">' +
                '<span>\\u548C\\u4E86\\u724C</span>' +
                '<img class="tile-img result-win-tile" src="' +
                tileSvgUrl(RESULT.winning_tile) + '">' + '</div>';
            let sc = RESULT.score;
            if (sc) {
                bHtml += '<div class="result-yaku">';
                for (let y of sc.yaku) {
                    bHtml += '<span class="yaku-item">' + y[0] +
                        '<em>' + y[1] + '\\u7FFB</em></span>';
                }
                bHtml += '</div>';
                bHtml += '<div class="result-score">' +
                    sc.han + '\\u7FFB ' + sc.fu + '\\u7B26 ' +
                    sc.payments.total + '\\u70B9</div>';
                let pay = sc.payments;
                let payDetail = '';
                if (RESULT.type === 'tsumo') {
                    if (pay.from_dealer > 0) {
                        payDetail = '\\u5B50' + pay.from_each_non_dealer +
                            '\\u70B9/\\u89AA' + pay.from_dealer + '\\u70B9';
                    } else {
                        payDetail = '\\u5404' + pay.from_each_non_dealer + '\\u70B9';
                    }
                } else {
                    payDetail = pay.from_discarder + '\\u70B9';
                }
                if ((METADATA.honba || 0) > 0) {
                    payDetail += ' +\\u672C\\u5834' +
                        (METADATA.honba * (RESULT.type === 'tsumo' ? 100 : 300)) +
                        '\\u70B9';
                }
                bHtml += '<div class="result-payment">' + payDetail + '</div>';
            } else {
                bHtml += '<div class="result-score">\\u5F79\\u306A\\u3057</div>';
            }

            // 和了者の手牌を表示
            bHtml += '<div class="result-hand">';
            for (let t = 0; t < 34; t++) {
                for (let c = 0; c < hands[wSeat][t]; c++) {
                    bHtml += '<img class="tile-result" src="' +
                        tileSvgUrl(t) + '">';
                }
            }
            bHtml += '</div>';

        } else {
            bHtml += '<div class="result-title">\\u6D41\\u5C40</div>' +
                '<div class="result-score">' + RESULT.turn +
                '\\u5DE1\\u76EE</div>';
        }

        // 次の局へボタン
        let roundIdx = METADATA.round_index;
        if (roundIdx !== undefined && roundIdx !== null) {
            let nextUrl = 'round_' + (roundIdx + 1) + '.html';
            bHtml += '<div class="result-nav">' +
                '<a class="btn-next-round" href="' + nextUrl +
                '">\\u6B21\\u306E\\u5C40\\u3078 \\u25B6</a>' +
                '</div>';
        }

        banner.innerHTML = bHtml;
    } else { banner.style.display = "none"; }
    updateButtons();
}

function countDraws() {
    let c = 0;
    for (let i = 0; i <= step; i++) { if (ACTIONS[i].type === "draw") c++; }
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
        document.getElementById("btn-auto").textContent = "\\u81EA\\u52D5\\u518D\\u751F";
    } else {
        autoTimer = setInterval(() => {
            if (step >= ACTIONS.length - 1) {
                clearInterval(autoTimer); autoTimer = null;
                document.getElementById("btn-auto").textContent =
                    "\\u81EA\\u52D5\\u518D\\u751F";
                return;
            }
            goNext();
        }, 100);
        document.getElementById("btn-auto").textContent = "\\u505C\\u6B62";
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
