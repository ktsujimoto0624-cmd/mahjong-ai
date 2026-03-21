"""ビューアのCSS定義"""


def get_css():
    return """
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
    font-family: 'Meiryo', 'Yu Gothic', sans-serif;
    background: #1a472a; color: #fff; padding: 10px;
    height: 100vh; overflow: hidden;
}
h1 { text-align: center; margin-bottom: 4px; font-size: 18px; }
.meta { text-align: center; color: #aaa; margin-bottom: 6px; font-size: 12px; }

.controls { text-align: center; margin: 6px 0; }
.controls button {
    background: #2d6a3f; border: 1px solid #4a9; color: #fff;
    padding: 4px 12px; margin: 0 2px; cursor: pointer; border-radius: 4px; font-size: 12px;
}
.controls button:hover { background: #3a8a5f; }
.controls button:disabled { opacity: 0.4; cursor: default; }
.controls .step-info { display: inline-block; min-width: 130px; font-size: 13px; }

/* === 麻雀卓レイアウト === */
.mahjong-table {
    max-width: 1000px; margin: 0 auto;
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    height: calc(100vh - 100px);
}

/* 手牌エリア共通 */
.hand-area {
    background: #0d2818; border: 1px solid #2a5; border-radius: 6px;
    padding: 4px 8px; position: relative;
}
.hand-area.active { border-color: #ff0; box-shadow: 0 0 8px rgba(255,255,0,0.3); }
.hand-area.winner { border-color: #f44; box-shadow: 0 0 12px rgba(255,80,80,0.5); }

.hand-label {
    font-size: 13px; font-weight: bold; margin-bottom: 4px;
    display: flex; justify-content: space-between;
}
.hand-label .agent { color: #8c8; font-size: 11px; font-weight: normal; }

/* 上下の手牌: 横1列 */
.hand-top, .hand-bottom {
    display: flex; flex-direction: column; width: 100%;
}
.hand-tiles {
    display: flex; flex-wrap: nowrap; gap: 2px; align-items: flex-end;
}
.hand-top .hand-tiles { justify-content: center; transform: rotate(180deg); }
.hand-bottom .hand-tiles { justify-content: center; }

/* 左右の手牌: 回転して中心向き */
.hand-left, .hand-right {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-width: 56px; max-width: 62px;
}
.hand-left .hand-tiles, .hand-right .hand-tiles {
    display: flex; flex-direction: column; gap: 0; align-items: center;
}
.hand-left .tile-vert, .hand-left .tile-river-vert {
    transform: rotate(90deg);
    margin: -8px 0;
}
.hand-right .tile-vert, .hand-right .tile-river-vert {
    transform: rotate(-90deg);
    margin: -8px 0;
}
.hand-left .hand-label, .hand-right .hand-label {
    flex-direction: column; align-items: center; gap: 0;
}
.hand-left .hand-label .agent, .hand-right .hand-label .agent { display: none; }

/* 中段 */
.middle-row {
    display: flex; align-items: stretch; gap: 6px; width: 100%; flex: 1; min-height: 0;
}

/* 河テーブル（中央） */
.river-table {
    flex: 1; background: #0f3320; border: 2px solid #2a5; border-radius: 8px;
    padding: 8px; display: flex; flex-direction: column; gap: 4px;
    min-height: 0;
}
.river-middle {
    display: flex; align-items: center; gap: 8px; flex: 1;
}

/* 河エリア: 6牌ずつ並べる */
.river-area { gap: 1px; }
.river-top, .river-bottom {
    display: grid; grid-template-columns: repeat(6, auto);
    justify-content: center; min-height: 36px;
}
.river-top { transform: rotate(180deg); }
/* 南家河: 下→上に6牌、次の列は右へ */
.river-right {
    display: flex; flex-direction: column-reverse; flex-wrap: wrap;
    align-content: flex-start;
    max-height: 166px; min-width: 36px; overflow: hidden;
}
.river-right .tile-river-vert { transform: rotate(-90deg); margin: -5px 0; }
/* 北家河: 上→下に6牌、次の列は左へ */
.river-left {
    display: flex; flex-direction: column; flex-wrap: wrap-reverse;
    align-content: flex-end;
    max-height: 166px; min-width: 36px; overflow: hidden;
}
.river-left .tile-river-vert { transform: rotate(90deg); margin: -5px 0; }

/* 中央情報 */
.center-info {
    flex: 1; text-align: center; padding: 10px;
    background: #0a1f10; border-radius: 6px; border: 1px solid #2a5;
}

/* 牌画像 */
.tile-img {
    height: 40px; width: auto; border-radius: 3px;
    background: #f5f0e0; padding: 1px; border: 1px solid #bba;
    transition: transform 0.1s;
}
.tile-img:hover { transform: translateY(-2px); }
.tile-img.draw-highlight {
    background: #fffbe6; box-shadow: 0 0 8px 2px #ffe066;
    border: 2px solid #ffcc00;
}
.tile-img.discard-last {
    background: #ffe0e0; box-shadow: 0 0 6px 2px #ff6666;
    border: 2px solid #ff4444;
}

/* 河の牌（小さめ） */
.tile-river {
    height: 32px; width: auto; border-radius: 2px;
    background: #e8e0d0; padding: 1px; border: 1px solid #a99;
}
.tile-river.discard-last {
    background: #ffe0e0; box-shadow: 0 0 5px 1px #ff6666;
    border: 2px solid #ff4444;
}

/* 縦の牌（左右プレイヤー） */
.tile-vert {
    height: auto; width: 36px; border-radius: 3px;
    background: #f5f0e0; padding: 1px; border: 1px solid #bba;
}
.tile-vert.draw-highlight {
    background: #fffbe6; box-shadow: 0 0 8px 2px #ffe066;
    border: 2px solid #ffcc00;
}

.tile-river-vert {
    height: auto; width: 28px; border-radius: 2px;
    background: #e8e0d0; padding: 1px; border: 1px solid #a99;
}
.tile-river-vert.discard-last {
    background: #ffe0e0; box-shadow: 0 0 5px 1px #ff6666;
    border: 2px solid #ff4444;
}

/* リーチ牌（横向き） */
.tile-river.riichi-tile {
    transform: rotate(90deg);
    margin: 4px 8px;
}
.river-right .tile-river-vert.riichi-tile {
    transform: rotate(0deg);
    margin: 2px 4px;
}
.river-left .tile-river-vert.riichi-tile {
    transform: rotate(180deg);
    margin: 2px 4px;
}

/* リーチマーク */
.riichi-mark {
    color: #f44; font-weight: bold; font-size: 11px;
    margin-left: 4px;
}

/* === 副露エリア（4人が90度ずつ回転した点対称） === */
.melds-area {
    display: flex; gap: 4px;
}
.meld-group {
    display: flex; gap: 1px; padding: 2px 3px;
    background: rgba(0,0,0,0.2); border-radius: 3px;
}
.tile-meld {
    height: 36px; width: auto; border-radius: 2px;
    background: #e8e0d0; padding: 1px; border: 1px solid #a99;
}
.tile-meld-vert {
    height: auto; width: 32px; border-radius: 2px;
    background: #e8e0d0; padding: 1px; border: 1px solid #a99;
}

/* 東家(下): 右端から左へ配置 */
.hand-bottom .melds-area {
    flex-direction: row-reverse; margin-left: auto;
    align-items: flex-end;
}

/* 西家(上): 180度回転内なのでrow-reverseで左端から右へ見える */
.hand-top .melds-area {
    flex-direction: row-reverse; margin-left: auto;
    align-items: flex-end;
}
.hand-top .meld-group { flex-direction: row-reverse; }

/* 北家(左): 下端から上へ配置、グループ内は縦並び */
.hand-left .melds-area {
    flex-direction: column-reverse; margin-left: 0; margin-top: auto;
    border-top: 2px solid #4a9; padding-top: 6px;
}
.hand-left .meld-group {
    flex-direction: column; gap: 0;
}
.hand-left .tile-meld-vert { transform: rotate(90deg); margin: -6px 0; }

/* 南家(右): 上端から下へ配置、グループ内は縦並び */
.hand-right .melds-area {
    flex-direction: column; margin-left: 0; order: -1;
    border-bottom: 2px solid #4a9; padding-bottom: 6px;
}
.hand-right .meld-group {
    flex-direction: column-reverse; gap: 0;
}
.hand-right .tile-meld-vert { transform: rotate(-90deg); margin: -6px 0; }

/* 横向き牌（鳴いた牌を示す） */
.tile-meld.tile-sideways {
    transform: rotate(90deg);
    margin: 6px -4px;
}
.hand-left .tile-meld-vert.tile-sideways {
    transform: rotate(180deg);
    margin: 0 0;
}
.hand-right .tile-meld-vert.tile-sideways {
    transform: rotate(0deg);
    margin: 0 0;
}

/* 暗槓の裏向き牌 */
.meld-facedown {
    background: #4a6a8a;
    border: 1px solid #6a8aaa;
    filter: saturate(0.3) brightness(0.7);
}

/* 加槓・大明槓の重ね表示 */
.kakan-stack {
    position: relative;
    display: inline-flex;
}
.tile-meld.tile-stacked {
    position: absolute;
    bottom: 100%; left: 50%;
    transform: translateX(-50%) rotate(90deg);
    margin: 0; height: 32px;
}
.hand-left .kakan-stack, .hand-right .kakan-stack {
    display: flex; flex-direction: row;
}
.hand-left .tile-meld-vert.tile-stacked {
    position: absolute;
    transform: rotate(180deg);
    margin: 0; width: 28px;
    top: 50%; left: auto; right: 100%;
    transform: rotate(180deg) translateY(-50%);
}
.hand-right .tile-meld-vert.tile-stacked {
    position: absolute;
    transform: rotate(0deg);
    margin: 0; width: 28px;
    top: 50%; left: 100%;
    transform: rotate(0deg) translateY(-50%);
}

.result-banner {
    text-align: center; margin: 4px auto; padding: 8px;
    background: #0d2818; border: 2px solid #f84; border-radius: 8px;
    font-size: 14px; display: none; max-width: 1000px;
}
"""
