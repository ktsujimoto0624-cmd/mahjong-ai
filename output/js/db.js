/**
 * SimMahjong IndexedDB ストレージ
 *
 * データ構造:
 *   simulations ストア: 半荘単位のレコード
 *   {
 *     id: auto-increment,
 *     created_at: ISO日時文字列（対局開始時刻）,
 *     mode: "tonnansen" | "tonpusen",
 *     agents: [{name, type, version}, ...] x4,
 *     rankings: [seat, ...],
 *     final_points: [int, ...] x4,
 *     rounds_played: int,
 *     round_results: [{round_label, type, winner, score, ...}, ...],
 *     round_records: [{metadata, initial_hands, actions, result}, ...],
 *     stats: {
 *       per_agent: [{
 *         seat: int,
 *         name: string,
 *         type: string,
 *         final_rank: int,
 *         final_points: int,
 *         win_count: int,
 *         tsumo_count: int,
 *         ron_count: int,
 *         deal_in_count: int,  // 放銃回数
 *         riichi_count: int,
 *         meld_count: int,     // 副露回数
 *         total_win_score: int, // 和了合計点
 *         yaku_list: [{name, count}, ...],
 *       }, ...],
 *       total_rounds: int,
 *       ryukyoku_count: int,
 *     }
 *   }
 */

const DB_NAME = 'SimMahjongDB';
const DB_VERSION = 1;
const STORE_NAME = 'simulations';

function openDB() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                const store = db.createObjectStore(STORE_NAME, {
                    keyPath: 'id',
                    autoIncrement: true,
                });
                store.createIndex('created_at', 'created_at', { unique: false });
                store.createIndex('mode', 'mode', { unique: false });
            }
        };
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

/**
 * シミュレーション結果からstatsを算出
 */
function calcStats(data) {
    const agents = data.agents || [];
    const perAgent = agents.map((name, seat) => ({
        seat,
        name,
        type: (data.agent_types && data.agent_types[seat]) || '',
        version: (data.agent_versions && data.agent_versions[seat]) || '',
        final_rank: data.rankings.indexOf(seat) + 1,
        final_points: data.final_points[seat],
        win_count: 0,
        tsumo_count: 0,
        ron_count: 0,
        deal_in_count: 0,
        riichi_count: 0,
        meld_count: 0,
        total_win_score: 0,
        total_win_han: 0,
        yaku_map: {},
    }));

    let ryukyoku_count = 0;

    for (const rr of data.round_results) {
        if (rr.type === 'ryukyoku') {
            ryukyoku_count++;
            continue;
        }
        const winner = rr.winner;
        if (winner === null || winner === undefined) continue;

        perAgent[winner].win_count++;
        if (rr.type === 'tsumo') perAgent[winner].tsumo_count++;
        if (rr.type === 'ron') {
            perAgent[winner].ron_count++;
            if (rr.from_player !== undefined && rr.from_player !== null) {
                perAgent[rr.from_player].deal_in_count++;
            }
        }
        if (rr.score && rr.score.payments) {
            perAgent[winner].total_win_score += rr.score.payments.total;
            perAgent[winner].total_win_han += rr.score.han || 0;
        }
        if (rr.score && rr.score.yaku) {
            for (const [yakuName] of rr.score.yaku) {
                perAgent[winner].yaku_map[yakuName] =
                    (perAgent[winner].yaku_map[yakuName] || 0) + 1;
            }
        }
    }

    // round_records からリーチ・副露回数を集計
    if (data.round_records) {
        for (const rec of data.round_records) {
            if (!rec || !rec.actions) continue;
            for (const a of rec.actions) {
                if (a.type === 'riichi') {
                    perAgent[a.seat].riichi_count++;
                } else if (a.type === 'meld') {
                    perAgent[a.seat].meld_count++;
                }
            }
        }
    }

    // yaku_map → yaku_list に変換
    for (const pa of perAgent) {
        pa.yaku_list = Object.entries(pa.yaku_map)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count);
        delete pa.yaku_map;
    }

    return {
        per_agent: perAgent,
        total_rounds: data.round_results.length,
        ryukyoku_count,
    };
}

/**
 * シミュレーション結果を保存
 */
async function saveSimulation(simResult) {
    const db = await openDB();
    const record = {
        created_at: new Date().toISOString(),
        mode: simResult.mode,
        agents: simResult.agents,
        agent_types: simResult.agent_types || [],
        agent_versions: simResult.agent_versions || [],
        rankings: simResult.rankings,
        final_points: simResult.points,
        rounds_played: simResult.rounds_played,
        round_results: simResult.round_results,
        round_records: simResult.round_records || [],
        stats: calcStats({
            ...simResult,
            final_points: simResult.points,
        }),
    };

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const req = store.add(record);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

/**
 * 全シミュレーションを取得（新しい順）
 */
async function getAllSimulations() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.getAll();
        req.onsuccess = () => {
            const results = req.result.sort(
                (a, b) => new Date(b.created_at) - new Date(a.created_at)
            );
            resolve(results);
        };
        req.onerror = () => reject(req.error);
    });
}

/**
 * IDで1件取得
 */
async function getSimulation(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.get(id);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
    });
}

/**
 * IDで1件削除
 */
async function deleteSimulation(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const req = store.delete(id);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
    });
}

/**
 * 全エージェントの統計を集計（複数半荘をまたいだ通算成績）
 */
async function getAgentStats(filterFn) {
    const all = await getAllSimulations();
    const filtered = filterFn ? all.filter(filterFn) : all;
    const agentMap = {};

    for (const sim of filtered) {
        if (!sim.stats || !sim.stats.per_agent) continue;

        // この半荘のポイント計算（ワンツー 10-20, 25000持ち/30000返し）
        const returnPt = 30000;
        const uma = [20, 10, -10, -20];
        let simPts = [0, 0, 0, 0];
        if (sim.rankings && sim.final_points) {
            // 2位以下の素点を四捨五入
            for (let r = 1; r < 4; r++) {
                const seat = sim.rankings[r];
                simPts[seat] = Math.round((sim.final_points[seat] - returnPt) / 1000) + uma[r];
            }
            // 1位はプラマイゼロ調整
            const seat0 = sim.rankings[0];
            simPts[seat0] = -(simPts[sim.rankings[1]] + simPts[sim.rankings[2]] + simPts[sim.rankings[3]]);
        }

        for (const pa of sim.stats.per_agent) {
            const agentType = pa.type || pa.name || 'unknown';
            const key = agentType;
            const typeNames = {hiyoko:'ひよこ',shanta:'しゃんた',random:'乱子',dev:'作成中',defense:'守備型',offense:'攻撃型',naki:'鳴き重視'};
            if (!agentMap[key]) {
                agentMap[key] = {
                    name: typeNames[agentType] || agentType,
                    type: agentType,
                    games: 0,
                    total_rank: 0,
                    rank_counts: [0, 0, 0, 0],
                    total_points: 0,
                    total_pt: 0,
                    win_count: 0,
                    tsumo_count: 0,
                    ron_count: 0,
                    deal_in_count: 0,
                    riichi_count: 0,
                    meld_count: 0,
                    total_rounds: 0,
                    total_win_score: 0,
                    total_win_han: 0,
                    yaku_map: {},
                };
            }
            const a = agentMap[key];
            a.games++;
            a.total_rank += pa.final_rank;
            a.rank_counts[pa.final_rank - 1]++;
            a.total_points += pa.final_points;
            a.total_pt += simPts[pa.seat] || 0;
            a.win_count += pa.win_count;
            a.tsumo_count += pa.tsumo_count;
            a.ron_count += pa.ron_count;
            a.deal_in_count += pa.deal_in_count;
            a.riichi_count += pa.riichi_count;
            a.meld_count += pa.meld_count;
            a.total_rounds += sim.stats.total_rounds;
            a.total_win_score += pa.total_win_score;
            a.total_win_han += pa.total_win_han || 0;
            for (const y of pa.yaku_list) {
                a.yaku_map[y.name] = (a.yaku_map[y.name] || 0) + y.count;
            }
        }
    }

    // 集計値を計算
    return Object.values(agentMap).map(a => ({
        ...a,
        avg_rank: a.games > 0 ? (a.total_rank / a.games).toFixed(2) : '-',
        avg_points: a.games > 0 ? Math.round(a.total_points / a.games) : 0,
        sum_pt: a.total_pt,
        avg_pt: a.games > 0 ? (a.total_pt / a.games).toFixed(1) : '-',
        win_rate: a.total_rounds > 0
            ? (a.win_count / a.total_rounds * 100).toFixed(1) + '%' : '-',
        deal_in_rate: a.total_rounds > 0
            ? (a.deal_in_count / a.total_rounds * 100).toFixed(1) + '%' : '-',
        riichi_rate: a.total_rounds > 0
            ? (a.riichi_count / a.total_rounds * 100).toFixed(1) + '%' : '-',
        meld_rate: a.total_rounds > 0
            ? (a.meld_count / a.total_rounds * 100).toFixed(1) + '%' : '-',
        avg_win_score: a.win_count > 0
            ? Math.round(a.total_win_score / a.win_count) : 0,
        avg_win_han: a.win_count > 0
            ? (a.total_win_han / a.win_count).toFixed(1) : '-',
        tsumo_rate: a.total_rounds > 0
            ? (a.tsumo_count / a.total_rounds * 100).toFixed(1) + '%' : '-',
        ron_rate: a.total_rounds > 0
            ? (a.ron_count / a.total_rounds * 100).toFixed(1) + '%' : '-',
        rank_rates: a.games > 0
            ? a.rank_counts.map(c => (c / a.games * 100).toFixed(1))
            : [0, 0, 0, 0],
        yaku_list: Object.entries(a.yaku_map)
            .map(([name, count]) => ({ name, count }))
            .sort((b, c) => c.count - b.count),
    }));
}
