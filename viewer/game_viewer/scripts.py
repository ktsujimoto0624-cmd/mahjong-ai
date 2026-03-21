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

        let rMark = riichiState[p.seat]
            ? '<span class="riichi-mark">\\u30EA\\u30FC\\u30C1</span>' : '';
        let label = '<div class="hand-label"><span>' + SEAT_NAMES[p.seat] + rMark +
                    '</span><span class="agent">' + AGENTS[p.seat] + '</span></div>';
        let meldsHtml = renderMelds(p.seat, p.vertical);
        let meldsDiv = meldsHtml
            ? '<div class="melds-area">' + meldsHtml + '</div>' : '';
        let tiles = '<div class="hand-tiles">' +
            renderHand(p.seat, p.vertical) + meldsDiv + '</div>';
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
    document.getElementById("center-info").innerHTML =
        "<div style='font-size:18px;'>\\u5DE1\\u76EE: " + turn + "</div>" +
        "<div style='font-size:12px;color:#8a8;margin-top:4px;'>\\u6B8B\\u308A: " +
        (122 - countDraws()) + "\\u679A</div>";

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
        if (RESULT.type === "tsumo") {
            banner.innerHTML = "\\u30C4\\u30E2\\u548C\\u4E86! " +
                SEAT_NAMES[RESULT.winner] +
                " (" + AGENTS[RESULT.winner] + ") " + RESULT.turn +
                "\\u5DE1\\u76EE \\u548C\\u4E86\\u724C: " +
                '<img class="tile-img" src="' + tileSvgUrl(RESULT.winning_tile) +
                '" style="vertical-align:middle;">';
        } else if (RESULT.type === "ron") {
            banner.innerHTML = "\\u30ED\\u30F3\\u548C\\u4E86! " +
                SEAT_NAMES[RESULT.winner] +
                " (" + AGENTS[RESULT.winner] + ") \\u2190 " +
                SEAT_NAMES[RESULT.from_player] +
                " " + RESULT.turn + "\\u5DE1\\u76EE \\u548C\\u4E86\\u724C: " +
                '<img class="tile-img" src="' + tileSvgUrl(RESULT.winning_tile) +
                '" style="vertical-align:middle;">';
        } else {
            banner.innerHTML = "\\u6D41\\u5C40 (" + RESULT.turn + "\\u5DE1\\u76EE)";
        }
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
        }, 300);
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
