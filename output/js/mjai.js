/**
 * mjai形式エクスポート
 *
 * IndexedDBの牌譜をmjai形式のJSON Lines (.mjson) としてダウンロードする。
 */

// SimMahjong牌ID → mjai牌表記
const MJAI_TILE_NAMES = [
    '1m','2m','3m','4m','5m','6m','7m','8m','9m',
    '1p','2p','3p','4p','5p','6p','7p','8p','9p',
    '1s','2s','3s','4s','5s','6s','7s','8s','9s',
    'E','S','W','N','P','F','C'
];

const MJAI_WIND = {0: 'E', 1: 'S', 2: 'W', 3: 'N'};

/**
 * カウント配列を牌名リストに変換
 */
function handCountsToMjaiList(counts) {
    const result = [];
    for (let i = 0; i < counts.length; i++) {
        for (let j = 0; j < counts[i]; j++) {
            result.push(MJAI_TILE_NAMES[i]);
        }
    }
    return result;
}

/**
 * 1局のrecordをmjaiイベントリストに変換
 */
function recordToMjaiEvents(rec) {
    const meta = rec.metadata || {};
    const events = [];

    // start_kyoku
    const bakaze = MJAI_WIND[meta.round_wind || 0] || 'E';
    const dealer = meta.dealer || 0;
    const kyoku = meta.round_number || 1;
    const honba = meta.honba || 0;
    const kyotaku = meta.riichi_pool || 0;
    const doraIndicators = meta.dora_indicators || [];
    const doraMarker = doraIndicators.length > 0
        ? MJAI_TILE_NAMES[doraIndicators[0]]
        : '1m';

    const tehais = (rec.initial_hands || []).map(handCountsToMjaiList);

    events.push({
        type: 'start_kyoku',
        bakaze: bakaze,
        dora_marker: doraMarker,
        kyoku: kyoku,
        honba: honba,
        kyotaku: kyotaku,
        oya: dealer,
        tehais: tehais,
    });

    // アクション
    for (const action of (rec.actions || [])) {
        const seat = action.seat;

        if (action.type === 'draw') {
            events.push({
                type: 'tsumo',
                actor: seat,
                pai: MJAI_TILE_NAMES[action.tile],
            });
        } else if (action.type === 'riichi') {
            events.push({
                type: 'reach',
                actor: seat,
            });
        } else if (action.type === 'discard') {
            events.push({
                type: 'dahai',
                actor: seat,
                pai: MJAI_TILE_NAMES[action.tile],
                tsumogiri: false,
            });
        } else if (action.type === 'meld') {
            const meldType = action.meld_type;
            const tiles = action.tiles;
            const fromSeat = action.from_seat;
            const takenTile = action.taken_tile;

            if (meldType === 'chi' || meldType === 'pon' || meldType === 'daiminkan') {
                const consumed = tiles
                    .filter(t => t !== takenTile)
                    .map(t => MJAI_TILE_NAMES[t]);
                events.push({
                    type: meldType,
                    actor: seat,
                    target: fromSeat,
                    pai: MJAI_TILE_NAMES[takenTile],
                    consumed: consumed,
                });
            } else if (meldType === 'ankan') {
                events.push({
                    type: 'ankan',
                    actor: seat,
                    consumed: tiles.map(t => MJAI_TILE_NAMES[t]),
                });
            } else if (meldType === 'kakan') {
                const consumed = tiles
                    .filter(t => t !== takenTile)
                    .map(t => MJAI_TILE_NAMES[t]);
                events.push({
                    type: 'kakan',
                    actor: seat,
                    pai: MJAI_TILE_NAMES[takenTile],
                    consumed: consumed,
                });
            }
        }
    }

    // 結果
    const result = rec.result;
    if (result) {
        if (result.type === 'tsumo' || result.type === 'ron') {
            const horaEvent = {
                type: 'hora',
                actor: result.winner,
                pai: MJAI_TILE_NAMES[result.winning_tile],
                uradora_markers: [],
                who: result.winner,
                target: result.type === 'ron' ? result.from_player : result.winner,
            };
            if (result.score) {
                if (result.score.yaku) {
                    horaEvent.yakus = result.score.yaku.map(y =>
                        Array.isArray(y) ? y[0] : y
                    );
                }
                if (result.score.payments) {
                    horaEvent.ten = result.score.payments.total;
                }
            }
            events.push(horaEvent);
        } else if (result.type === 'ryukyoku') {
            events.push({type: 'ryukyoku'});
        }
    }

    events.push({type: 'end_kyoku'});
    return events;
}

/**
 * 半荘データ全体をmjai JSON Lines文字列に変換
 */
function simulationToMjai(sim) {
    const lines = [];
    const agents = sim.agents || ['player0', 'player1', 'player2', 'player3'];

    // start_game
    lines.push(JSON.stringify({type: 'start_game', names: agents}));

    // 各局
    const records = sim.round_records || [];
    for (const rec of records) {
        if (!rec) continue;
        const events = recordToMjaiEvents(rec);
        for (const ev of events) {
            lines.push(JSON.stringify(ev));
        }
    }

    // end_game
    lines.push(JSON.stringify({type: 'end_game'}));

    return lines.join('\n');
}

/**
 * mjai形式で.mjsonファイルをダウンロード
 */
async function downloadMjai(simId) {
    try {
        let sim;
        if (simId !== undefined && simId !== null) {
            sim = await getSimulation(simId);
        } else if (typeof simData !== 'undefined' && simData) {
            sim = simData;
            // simDataにはround_recordsが含まれている
        }

        if (!sim) {
            alert('牌譜データが見つかりません');
            return;
        }

        // round_recordsが無い場合
        if (!sim.round_records || sim.round_records.length === 0) {
            alert('この対局には牌譜データがありません');
            return;
        }

        const mjaiText = simulationToMjai(sim);
        const blob = new Blob([mjaiText], {type: 'application/x-ndjson'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const dateStr = sim.created_at
            ? new Date(sim.created_at).toISOString().replace(/[:.]/g, '-').slice(0, 19)
            : new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        a.href = url;
        a.download = 'simmahjong_' + dateStr + '.mjson';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('mjai export failed:', e);
        alert('mjai形式のエクスポートに失敗しました: ' + e.message);
    }
}
