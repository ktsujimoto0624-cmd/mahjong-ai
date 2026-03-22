// ===== ゲームを眺めるモード =====

// 設定をlocalStorageから復元
function watchLoadSettings() {
    try {
        var s = JSON.parse(localStorage.getItem('watchSettings') || '{}');
        return {
            speed: s.speed || 200,
            manualMode: !!s.manualMode,
            hideHands: !!s.hideHands,
            autoContinue: s.autoContinue !== undefined ? s.autoContinue : true,
        };
    } catch(e) { return { speed: 200, manualMode: false, hideHands: false, autoContinue: true }; }
}
function watchSaveSettings() {
    localStorage.setItem('watchSettings', JSON.stringify({
        speed: watchSpeed,
        manualMode: watchManualMode,
        hideHands: watchHideHands,
        autoContinue: watchAutoContinue,
    }));
}

var _ws = watchLoadSettings();
var watchActive = false;
var watchAutoTimer = null;
var watchSpeed = _ws.speed;
var watchManualMode = _ws.manualMode;
var watchHideHands = _ws.hideHands;
var watchCurrentRound = 0;
var watchPrevResult = null;
var watchAutoContinue = _ws.autoContinue;
var watchWaitingStart = false; // 手動モードで開始待ち
var originalVRenderHand = null;
var originalVRender = null;

function startWatchMode() {
    if (!simData || !simData.round_records || simData.round_records.length === 0) {
        alert('No simulation data');
        return;
    }
    watchActive = true;
    watchCurrentRound = 0;
    watchPrevResult = null;
    watchWaitingStart = false;
    if (!originalVRenderHand) originalVRenderHand = window.vRenderHand;
    window.vRenderHand = function(seat, isVertical) {
        if (watchActive && watchHideHands && seat !== 0) return watchRenderHiddenHand(seat, isVertical);
        return originalVRenderHand(seat, isVertical);
    };
    if (!originalVRender) originalVRender = window.vRender;
    window.vRender = function() {
        originalVRender();
        if (watchActive) watchPostRender();
    };
    watchLoadRound(0);
}

function watchRenderHiddenHand(seat, isVertical) {
    var count = 0;
    for (var t = 0; t < 34; t++) count += vHands[seat][t];
    var drawTile = vLastDraw[seat];
    var mainCount = count;
    if (drawTile !== null) mainCount--;
    var html = '';
    if (isVertical) {
        var st = 'display:block;width:28px;height:18px;background:#3a5068;border:1px solid #5a7a8a;border-radius:2px;margin:1px 0;';
        for (var i = 0; i < mainCount; i++) html += '<span style="' + st + '"></span>';
        if (drawTile !== null) {
            html += '<span style="margin-top:6px;display:block;"><span style="' + st + '"></span></span>';
        }
    } else {
        var st2 = 'display:inline-block;width:24px;height:32px;background:#3a5068;border:1px solid #5a7a8a;border-radius:2px;margin:0 1px;';
        for (var i2 = 0; i2 < mainCount; i2++) html += '<span style="' + st2 + '"></span>';
        if (drawTile !== null) {
            html += '<span style="margin-left:8px;display:inline-block;"><span style="' + st2 + '"></span></span>';
        }
    }
    return html;
}

function watchPostRender() {
    var turn = vGetCurrentTurn();
    var info = '\u914d\u724c';
    if (vStep >= 0) {
        var a = vActions[vStep];
        if (a.type === 'riichi') info = SEAT_NAMES_V[a.seat] + ' \u30ea\u30fc\u30c1!';
        else if (a.type === 'meld') {
            var mLabel = {chi:'\u30c1\u30fc',pon:'\u30dd\u30f3',daiminkan:'\u660e\u69fb',ankan:'\u6697\u69fb',kakan:'\u52a0\u69fb'}[a.meld_type] || '';
            info = SEAT_NAMES_V[a.seat] + ' ' + mLabel + '! ' + TILE_NAMES_V[a.taken_tile];
        } else {
            info = SEAT_NAMES_V[a.seat] + ' ' + (a.type === 'draw' ? '\u30c4\u30e2 ' : '\u6253 ') + TILE_NAMES_V[a.tile];
        }
    }
    var stepInfo = document.getElementById('v-step-info');
    if (stepInfo) stepInfo.textContent = turn + '\u5de1\u76ee ' + info;
    var centerEl = document.getElementById('v-center-info');
    if (centerEl) {
        var statsEl = centerEl.querySelector('.center-stats');
        if (statsEl) statsEl.innerHTML = '<span>\u5de1\u76ee:' + turn + '</span>';
    }
}

function watchLoadRound(roundIndex) {
    if (!simData.round_records[roundIndex]) return;
    var rec = simData.round_records[roundIndex];
    vActions = rec.actions;
    vInitialHands = rec.initial_hands;
    vResult = rec.result;
    vMetadata = rec.metadata;
    vStep = -1;
    vShowingResult = false;
    vResultPhase = 0;
    vCurrentRoundIndex = roundIndex;
    watchCurrentRound = roundIndex;
    if (vAutoTimer) { clearInterval(vAutoTimer); vAutoTimer = null; }
    if (watchAutoTimer) { clearInterval(watchAutoTimer); watchAutoTimer = null; }
    var agents = vMetadata.agents || ['?','?','?','?'];
    var controlsHtml = watchBuildControls();
    document.getElementById('haipu-body').innerHTML =
        '<div class="meta" id="v-meta">' + agents.join(' vs ') + '</div>' +
        controlsHtml +
        '<div class="mahjong-table">' +
        '<div class="hand-area hand-top" id="v-hand-2"></div>' +
        '<div class="middle-row">' +
        '<div class="hand-area hand-left" id="v-hand-3"></div>' +
        '<div class="river-table">' +
        '<div class="river-area river-top" id="v-river-2"></div>' +
        '<div class="river-middle">' +
        '<div class="river-area river-left" id="v-river-3"></div>' +
        '<div class="center-info" id="v-center-info"></div>' +
        '<div class="river-area river-right" id="v-river-1"></div>' +
        '</div>' +
        '<div class="river-area river-bottom" id="v-river-0"></div>' +
        '</div>' +
        '<div class="hand-area hand-right" id="v-hand-1"></div>' +
        '</div>' +
        '<div class="hand-area hand-bottom" id="v-hand-0"></div>' +
        '</div>' +
        '<div class="result-banner" id="v-result-banner"></div>' +
        '<div class="watch-round-result" id="watch-round-result"></div>';
    document.getElementById('haipu-modal').classList.add('show');
    if (watchPrevResult) watchShowPrevResult(watchPrevResult);
    vRender();

    if (watchAutoContinue) {
        // 局間自動: すぐに再生開始（打牌モードに関係なく強制）
        watchWaitingStart = false;
        watchStartAutoForced();
    } else {
        // 局間手動: 開始ボタン待ち
        watchWaitingStart = true;
        var stopBtn = document.getElementById('watch-btn-stop');
        if (stopBtn) { stopBtn.textContent = '\u958b\u59cb'; stopBtn.style.background = '#2a6a3f'; }
    }
}

function watchBuildControls() {
    var speeds = [
        { val: 10, label: '0.01\u79d2' },
        { val: 100, label: '0.1\u79d2' },
        { val: 200, label: '0.2\u79d2' },
        { val: 300, label: '0.3\u79d2' },
        { val: 400, label: '0.4\u79d2' },
        { val: 500, label: '0.5\u79d2' },
    ];
    var speedOptions = '';
    for (var i = 0; i < speeds.length; i++) {
        var sel = (speeds[i].val === watchSpeed) ? ' selected' : '';
        speedOptions += '<option value="' + speeds[i].val + '"' + sel + '>' + speeds[i].label + '</option>';
    }
    return '<div class="controls watch-controls">' +
        '<label style="font-size:12px;color:#aaa;">\u901f\u5ea6:</label>' +
        '<select id="watch-speed" onchange="watchChangeSpeed(this.value)" style="background:#1a3a2a;border:1px solid #4a9;color:#fff;padding:3px 6px;border-radius:4px;font-size:12px;">' +
        speedOptions + '</select>' +
        '<button id="watch-btn-mode" onclick="watchToggleManual()">' +
        (watchManualMode ? '\u81ea\u52d5' : '\u624b\u52d5') + '</button>' +
        '<button id="watch-btn-hands" onclick="watchToggleHands()">' +
        '\u624b\u724c: ' + (watchHideHands ? '\u5168\u8868\u793a' : '\u96a0\u3059') + '</button>' +
        '<button id="watch-btn-stop" onclick="watchStopResume()" style="background:' +
        (!watchAutoContinue ? '#2a6a3f;border:1px solid #4a9' : '#a64;border:1px solid #d96') + ';">' +
        (!watchAutoContinue ? '\u958b\u59cb' : '\u505c\u6b62') + '</button>' +
        '<button id="watch-btn-continue" onclick="watchToggleContinue()" style="background:' +
        (watchAutoContinue ? '#2a6a3f' : '#a64') + ';border:1px solid ' +
        (watchAutoContinue ? '#4a9' : '#d96') + ';">' +
        '\u5c40\u9593: ' + (watchAutoContinue ? '\u81ea\u52d5' : '\u624b\u52d5') + '</button>' +
        '<button onclick="watchClose()" style="background:#a33;border:1px solid #d66;">' +
        '\u00d7 \u9589\u3058\u308b</button>' +
        '<span class="step-info" id="v-step-info" style="margin-left:8px;">\u914d\u724c</span>' +
        '</div>';
}

function watchChangeSpeed(val) {
    watchSpeed = parseInt(val, 10);
    watchSaveSettings();
    if (watchAutoTimer) { clearInterval(watchAutoTimer); watchAutoTimer = null; watchStartAuto(); }
}

function watchToggleManual() {
    watchManualMode = !watchManualMode;
    watchSaveSettings();
    var btn = document.getElementById('watch-btn-mode');
    if (btn) btn.textContent = watchManualMode ? '\u81ea\u52d5' : '\u624b\u52d5';
    if (watchManualMode) {
        if (watchAutoTimer) { clearInterval(watchAutoTimer); watchAutoTimer = null; }
    } else {
        if (!watchAutoTimer && !watchWaitingStart && vStep < vActions.length - 1) watchStartAuto();
    }
}

function watchToggleHands() {
    watchHideHands = !watchHideHands;
    watchSaveSettings();
    var btn = document.getElementById('watch-btn-hands');
    if (btn) btn.textContent = '\u624b\u724c: ' + (watchHideHands ? '\u5168\u8868\u793a' : '\u96a0\u3059');
    vRender();
}

function watchStartAutoForced() {
    // 手動進行モードでも強制的に自動再生（局間自動用）
    if (watchAutoTimer) return;
    var stopBtn = document.getElementById('watch-btn-stop');
    if (stopBtn) { stopBtn.textContent = '\u505c\u6b62'; stopBtn.style.background = '#a64'; }
    watchAutoTimer = setInterval(function() {
        if (vStep >= vActions.length - 1) {
            clearInterval(watchAutoTimer);
            watchAutoTimer = null;
            watchOnRoundEnd();
            return;
        }
        vResultPhase = 0;
        vShowingResult = false;
        vStep++;
        vRender();
    }, watchSpeed);
}

function watchStartAuto() {
    if (watchAutoTimer) return;
    if (watchManualMode) return;
    var stopBtn = document.getElementById('watch-btn-stop');
    if (stopBtn) { stopBtn.textContent = '\u505c\u6b62'; stopBtn.style.background = '#a64'; }
    watchAutoTimer = setInterval(function() {
        if (vStep >= vActions.length - 1) {
            clearInterval(watchAutoTimer);
            watchAutoTimer = null;
            watchOnRoundEnd();
            return;
        }
        vResultPhase = 0;
        vShowingResult = false;
        vStep++;
        vRender();
    }, watchSpeed);
}

function watchStopResume() {
    if (watchWaitingStart) {
        // 開始待ち → 再生開始
        watchWaitingStart = false;
        var stopBtn = document.getElementById('watch-btn-stop');
        if (stopBtn) { stopBtn.textContent = '\u505c\u6b62'; stopBtn.style.background = '#a64'; }
        watchStartAuto();
        return;
    }
    var stopBtn = document.getElementById('watch-btn-stop');
    if (watchAutoTimer) {
        clearInterval(watchAutoTimer);
        watchAutoTimer = null;
        if (stopBtn) { stopBtn.textContent = '\u518d\u958b'; stopBtn.style.background = '#2a6a3f'; }
    } else {
        if (vStep < vActions.length - 1) watchStartAuto();
        if (stopBtn) { stopBtn.textContent = '\u505c\u6b62'; stopBtn.style.background = '#a64'; }
    }
}

function watchClose() {
    watchActive = false;
    watchWaitingStart = false;
    if (watchAutoTimer) { clearInterval(watchAutoTimer); watchAutoTimer = null; }
    if (originalVRenderHand) window.vRenderHand = originalVRenderHand;
    if (originalVRender) window.vRender = originalVRender;
    closeHaipu();
}

function watchOnRoundEnd() {
    var resultInfo = watchBuildRoundResultInfo();
    watchPrevResult = resultInfo;
    watchShowPrevResult(resultInfo);
    var nextIdx = watchCurrentRound + 1;
    var hasNext = simData.round_records[nextIdx];

    if (watchAutoContinue) {
        // 自動進行: 2秒後に次の局へ
        if (hasNext) {
            setTimeout(function() { if (!watchActive) return; watchLoadRound(nextIdx); }, 2000);
        } else {
            setTimeout(function() { if (!watchActive) return; watchShowFinalResult(); }, 2000);
        }
    } else {
        // 手動: 次の局ボタンを表示
        var el = document.getElementById('watch-round-result');
        if (el) {
            var btnHtml = '<div style="margin-top:8px;">';
            if (hasNext) {
                btnHtml += '<button onclick="watchLoadRound(' + nextIdx + ')" style="background:#26a;border:1px solid #49d;color:#fff;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:bold;">\u6b21\u306e\u5c40 \u25b6</button>';
            } else {
                btnHtml += '<button onclick="watchShowFinalResult()" style="background:#a64;border:1px solid #d96;color:#fff;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:bold;">\u6700\u7d42\u7d50\u679c</button>';
            }
            btnHtml += '</div>';
            el.innerHTML += btnHtml;
        }
    }
}

function watchToggleContinue() {
    watchAutoContinue = !watchAutoContinue;
    watchSaveSettings();
    var btn = document.getElementById('watch-btn-continue');
    if (btn) {
        btn.textContent = '\u5c40\u9593: ' + (watchAutoContinue ? '\u81ea\u52d5' : '\u624b\u52d5');
        btn.style.background = watchAutoContinue ? '#2a6a3f' : '#a64';
        btn.style.borderColor = watchAutoContinue ? '#4a9' : '#d96';
    }
}

function watchBuildRoundResultInfo() {
    var windNames = ['\u6771','\u5357','\u897f','\u5317'];
    var agents = vMetadata.agents || ['?','?','?','?'];
    var dealer = vMetadata.dealer || 0;
    var rw = vMetadata.round_wind || 0;
    var rn = (vMetadata.round_number || 0) + 1;
    var roundLabel = windNames[rw] + rn + '\u5c40';
    var info = { roundLabel: roundLabel };
    if (vResult.type === 'tsumo' || vResult.type === 'ron') {
        var wSeat = vResult.winner;
        var wWind = windNames[(wSeat - dealer + 4) % 4];
        info.type = vResult.type === 'tsumo' ? '\u30c4\u30e2' : '\u30ed\u30f3';
        info.winner = wWind + '\u5bb6 ' + agents[wSeat];
        if (vResult.type === 'ron' && vResult.from_player !== undefined) {
            var fWind = windNames[(vResult.from_player - dealer + 4) % 4];
            info.from = '\u2190 ' + fWind + '\u5bb6' + agents[vResult.from_player];
        }
        info.winningTile = vResult.winning_tile;
        // 手牌（ツモ牌分離）
        var handCopy = vHands[wSeat].slice();
        if (vResult.type === 'tsumo' && handCopy[vResult.winning_tile] > 0) {
            handCopy[vResult.winning_tile]--;
        }
        info.handTiles = handCopy;
        info.melds = vMelds[wSeat];
        var sc = vResult.score;
        if (sc) {
            info.yaku = sc.yaku.map(function(y) { return y[0]; }).join(', ');
            info.score = sc.payments.total + '\u70b9';
            var rk = '';
            if (sc.han >= 13) rk = '\u5f79\u6e80';
            else if (sc.han >= 11) rk = '\u4e09\u500d\u6e80';
            else if (sc.han >= 8) rk = '\u500d\u6e80';
            else if (sc.han >= 6) rk = '\u8df3\u6e80';
            else if (sc.han >= 5) rk = '\u6e80\u8cab';
            if (rk) info.rank = rk;
            info.hanfu = sc.han + '\u7ffb' + sc.fu + '\u7b26';
        }
    } else {
        info.type = '\u6d41\u5c40';
        info.winner = '';
        info.yaku = '';
        info.score = '';
    }
    return info;
}

function watchShowPrevResult(info) {
    var el = document.getElementById('watch-round-result');
    if (!el) return;
    var html = '<div class="watch-result-label">' + info.roundLabel + '</div>';
    html += '<div class="watch-result-type">' + info.type + '</div>';
    if (info.winner) html += '<div class="watch-result-winner">' + info.winner + '</div>';
    if (info.from) html += '<div style="font-size:10px;color:#f88;">' + info.from + '</div>';
    if (info.yaku) html += '<div class="watch-result-yaku">' + info.yaku + '</div>';
    if (info.rank) html += '<span class="watch-result-rank">' + info.rank + '</span> ';
    if (info.hanfu) html += '<span class="watch-result-hanfu">' + info.hanfu + '</span> ';
    if (info.score) html += '<div class="watch-result-score">' + info.score + '</div>';
    // 手牌表示（コンパクト）
    if (info.handTiles) {
        html += '<div style="display:flex;flex-wrap:wrap;gap:1px;margin-top:4px;align-items:flex-end;">';
        for (var t = 0; t < 34; t++) {
            for (var c = 0; c < info.handTiles[t]; c++) {
                html += '<img src="' + tileSvgUrl(t) + '" style="height:20px;border-radius:1px;background:#f5f0e0;border:1px solid #bba;">';
            }
        }
        if (info.winningTile !== undefined) {
            html += '<span style="margin-left:4px;"><img src="' + tileSvgUrl(info.winningTile) + '" style="height:20px;border-radius:1px;background:#fffbe6;border:2px solid #fd6;box-shadow:0 0 4px rgba(255,220,100,0.6);"></span>';
        }
        if (info.melds && info.melds.length > 0) {
            html += '<span style="margin-left:3px;border-left:1px solid #4a9;padding-left:3px;">';
            for (var mi = 0; mi < info.melds.length; mi++) {
                for (var mti = 0; mti < info.melds[mi].tiles.length; mti++) {
                    html += '<img src="' + tileSvgUrl(info.melds[mi].tiles[mti]) + '" style="height:20px;border-radius:1px;background:#e8e0d0;border:1px solid #a99;">';
                }
            }
            html += '</span>';
        }
        html += '</div>';
    }
    el.innerHTML = html;
    el.style.display = 'block';
}

function watchShowFinalResult() {
    var banner = document.getElementById('v-result-banner');
    if (!banner) return;
    var agents = simData.agents || ['?','?','?','?'];
    var rankings = simData.rankings || [0,1,2,3];
    var points = simData.points || [25000,25000,25000,25000];
    var windNames = ['\u6771','\u5357','\u897f','\u5317'];
    var html = '<div class="result-title" style="font-size:24px;">\u534a\u8358\u7d42\u4e86</div>';
    html += '<table style="width:auto;margin:16px auto 0;border-collapse:collapse;">';
    html += '<tr><th style="padding:8px 16px;border:1px solid #3a6;background:#1a3a2a;">\u9806\u4f4d</th>' +
        '<th style="padding:8px 16px;border:1px solid #3a6;background:#1a3a2a;">\u5e2d</th>' +
        '<th style="padding:8px 16px;border:1px solid #3a6;background:#1a3a2a;">\u30a8\u30fc\u30b8\u30a7\u30f3\u30c8</th>' +
        '<th style="padding:8px 16px;border:1px solid #3a6;background:#1a3a2a;">\u70b9\u6570</th></tr>';
    for (var rank = 0; rank < rankings.length; rank++) {
        var seat = rankings[rank];
        var color = rank === 0 ? '#fd6' : '#fff';
        html += '<tr><td style="padding:8px 16px;border:1px solid #3a6;color:' + color + ';font-weight:bold;">' + (rank+1) + '\u4f4d</td>' +
            '<td style="padding:8px 16px;border:1px solid #3a6;">' + windNames[seat] + '\u5bb6</td>' +
            '<td style="padding:8px 16px;border:1px solid #3a6;">' + agents[seat] + '</td>' +
            '<td style="padding:8px 16px;border:1px solid #3a6;color:#ff8;font-weight:bold;">' + points[seat] + '\u70b9</td></tr>';
    }
    html += '</table>';
    html += '<div style="margin-top:20px;"><button onclick="watchClose()" style="background:#a64;border:2px solid #d96;color:#fff;padding:10px 30px;border-radius:8px;cursor:pointer;font-size:16px;font-weight:bold;">\u9589\u3058\u308b</button></div>';
    banner.className = 'result-banner';
    banner.innerHTML = html;
    banner.style.display = 'block';
}

// Manual mode: click to advance
document.addEventListener('click', function(e) {
    if (!watchActive || !watchManualMode) return;
    if (e.target.closest('.controls') || e.target.closest('.watch-controls') ||
        e.target.closest('.watch-round-result') || e.target.closest('.result-banner') ||
        e.target.closest('.modal-close')) return;
    if (!document.getElementById('haipu-modal').classList.contains('show')) return;
    if (watchWaitingStart) return; // 開始待ちではクリック進行しない
    if (vStep < vActions.length - 1) {
        vResultPhase = 0; vShowingResult = false; vStep++; vRender();
    } else {
        watchOnRoundEnd();
    }
});

// Keyboard: Escape to close watch mode
document.addEventListener('keydown', function(e) {
    if (!watchActive) return;
    if (!document.getElementById('haipu-modal').classList.contains('show')) return;
    if (e.key === 'Escape') { watchClose(); e.preventDefault(); }
});
