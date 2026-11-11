// Shared storybook SVG drawing helpers for the Unmasked board game print art.
const C = {
  ink: '#2a1f2d', inkSoft: '#4a3a4a', parch: '#f3e6c8', parchD: '#dcc79c', parchDD: '#b89c6c',
  amber: '#f2a53a', amberL: '#ffd27a', amberD: '#c46f1c', teal: '#1d3b3f', tealM: '#2f5e5f',
  tealL: '#6fa3a0', tealLL: '#a9cfc6', violet: '#7b5ea7', violetL: '#b39ddb', red: '#b8352f',
  sage: '#8fa77a', moss: '#4f6b45', mossD: '#344a32', grass: '#2b4a3c', grassL: '#3c5e48',
  water: '#2c5a6b', waterL: '#4f8a95', stone: '#8d8a86', stoneD: '#5d5a58', brick: '#9a4b3a',
  cream: '#efe1c0', plum: '#5a3550', rose: '#d98a7a', pump: '#e8792b',
};
let _rid = 0;
const rnd = (() => { let s = 1234567; return () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; })();
const f = n => (Math.round(n * 100) / 100);
const pts = a => a.map(p => f(p[0]) + ',' + f(p[1])).join(' ');
const poly = (a, fill, extra = '') => `<polygon points="${pts(a)}" fill="${fill}" stroke="${C.ink}" stroke-width="1.1" stroke-linejoin="round" ${extra}/>`;
const rect = (x, y, w, h, fill, extra = '') => `<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" fill="${fill}" stroke="${C.ink}" stroke-width="1.1" ${extra}/>`;
const circ = (x, y, r, fill, extra = '') => `<circle cx="${f(x)}" cy="${f(y)}" r="${f(r)}" fill="${fill}" ${extra}/>`;
function shade(hex, k) { // k<1 darker, >1 lighter
  const n = parseInt(hex.slice(1), 16); let r = n >> 16, g = (n >> 8) & 255, b = n & 255;
  const m = v => Math.max(0, Math.min(255, Math.round(k < 1 ? v * k : v + (255 - v) * (k - 1))));
  return '#' + ((1 << 24) | (m(r) << 16) | (m(g) << 8) | m(b)).toString(16).slice(1);
}

// Windows grid on a front face.
function windows(x0, y0, w, h, cols, rows, lit, opts = {}) {
  let s = ''; const ww = w / (cols * 1.9 + 0.4), wh = h / (rows * 1.8 + 0.5);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    if (opts.skip && opts.skip(r, c)) continue;
    const x = x0 + w * (c + 0.5) / cols - ww / 2, y = y0 + h * (r + 0.5) / rows - wh / 2;
    const on = rnd() < lit; const col = on ? (rnd() < 0.15 ? '#9fd6c8' : C.amberL) : '#26363f';
    if (on) s += `<rect x="${f(x - ww * .5)}" y="${f(y - wh * .4)}" width="${f(ww * 2)}" height="${f(wh * 1.8)}" fill="${C.amber}" opacity=".18" rx="${f(ww)}"/>`;
    if (opts.arch) s += `<path d="M${f(x)},${f(y + wh)} V${f(y + ww / 2)} A${f(ww / 2)},${f(ww / 2)} 0 0 1 ${f(x + ww)},${f(y + ww / 2)} V${f(y + wh)} Z" fill="${col}" stroke="${C.ink}" stroke-width=".8"/>`;
    else s += `<rect x="${f(x)}" y="${f(y)}" width="${f(ww)}" height="${f(wh)}" fill="${col}" stroke="${C.ink}" stroke-width=".8"/>`;
    s += `<line x1="${f(x + ww / 2)}" y1="${f(y)}" x2="${f(x + ww / 2)}" y2="${f(y + wh)}" stroke="${C.ink}" stroke-width=".4" opacity=".6"/>`;
  }
  return s;
}
function door(x, y, w, h, col = C.plum) {
  return `<path d="M${f(x - w / 2)},${f(y)} V${f(y - h + w / 2)} A${f(w / 2)},${f(w / 2)} 0 0 1 ${f(x + w / 2)},${f(y - h + w / 2)} V${f(y)} Z" fill="${col}" stroke="${C.ink}" stroke-width=".9"/>` +
    circ(x + w * .25, y - h * .45, .7, C.amberL) + circ(x, y - h - 2, 1.6, C.amberL, `opacity=".9"`) + circ(x, y - h - 2, 5, C.amber, `opacity=".22"`);
}
function shadow(x, y, w) { return `<ellipse cx="${f(x + w * .12)}" cy="${f(y + 1.5)}" rx="${f(w * .62)}" ry="${f(w * .14)}" fill="#0d1a1c" opacity=".45"/>`; }

// Generic building in oblique view: front face + side face + roof.
function building(o) {
  const { x, y, w, h } = o; const d = o.d ?? w * .32, dy = d * .5, rh = o.rh ?? h * .7;
  const wall = o.wall || C.cream, side = shade(wall, .72), roofc = o.roof || C.plum;
  const L = x - w / 2, R = x + w / 2, T = y - h; let s = shadow(x + d * .4, y, w + d);
  s += poly([[R, y], [R + d, y - dy], [R + d, T - dy], [R, T]], side);
  s += rect(L, T, w, h, wall);
  // texture lines
  if (o.siding) for (let yy = T + 3; yy < y; yy += 3) s += `<line x1="${f(L)}" y1="${f(yy)}" x2="${f(R)}" y2="${f(yy)}" stroke="${C.ink}" stroke-width=".25" opacity=".35"/>`;
  if (o.bricks) for (let yy = T + 2.5; yy < y; yy += 2.5) s += `<line x1="${f(L)}" y1="${f(yy)}" x2="${f(R)}" y2="${f(yy)}" stroke="${shade(wall, .6)}" stroke-width=".35" opacity=".6"/>`;
  const kind = o.kind || 'gable';
  if (kind === 'gable') {
    s += poly([[x, T - rh], [x + d, T - rh - dy], [R + d + 2, T - dy], [R + 2, T]], shade(roofc, .82));
    s += poly([[L - 2, T], [x, T - rh], [R + 2, T]], roofc);
    s += poly([[L + w * .22, T - 1], [x, T - rh + rh * .3], [R - w * .22, T - 1]], wall);
    if (o.gableWin !== false) s += circ(x, T - rh * .35, Math.min(w, rh) * .09, rnd() < .6 ? C.amberL : '#26363f', `stroke="${C.ink}" stroke-width=".7"`);
  } else if (kind === 'side') { // ridge parallel to front
    s += poly([[L - 2, T], [L + w * .12, T - rh], [R - w * .12 + d, T - rh - dy], [R + d + 2, T - dy], [R + 2, T]], roofc);
    s += poly([[L - 2, T], [L + w * .12, T - rh], [R - w * .12, T - rh], [R + 2, T]], roofc);
    s += `<line x1="${f(L + w * .12)}" y1="${f(T - rh)}" x2="${f(R - w * .12)}" y2="${f(T - rh)}" stroke="${shade(roofc, 1.3)}" stroke-width="1"/>`;
    for (let i = 1; i < 4; i++) s += `<line x1="${f(L + w * i * .06)}" y1="${f(T - rh * i / 4)}" x2="${f(R - w * i * .06 + 0)}" y2="${f(T - rh * i / 4)}" stroke="${C.ink}" stroke-width=".35" opacity=".5"/>`;
  } else if (kind === 'flat') {
    s += poly([[L - 1, T], [L - 1 + d, T - dy], [R + d + 1, T - dy], [R + 1, T]], shade(wall, .55));
    s += rect(L - 1.5, T - 3, w + 3, 3.5, o.trim || shade(wall, .8));
  } else if (kind === 'mansard') {
    s += poly([[L - 2, T], [L + 3, T - rh], [R - 3 + d, T - rh - dy], [R + d + 2, T - dy], [R + 2, T]], shade(roofc, .82));
    s += poly([[L - 2, T], [L + 3, T - rh], [R - 3, T - rh], [R + 2, T]], roofc);
    for (let i = 0; i < 3; i++) { const cx = L + w * (i + .5) / 3; s += rect(cx - 2.2, T - rh * .8, 4.4, rh * .6, rnd() < .6 ? C.amberL : '#26363f', `stroke-width=".7"`); }
  } else if (kind === 'gambrel') { // barn
    s += poly([[L - 2, T], [L + w * .08, T - rh * .55], [x, T - rh], [x + d, T - rh - dy], [R - w * .08 + d, T - rh * .55 - dy], [R + d + 2, T - dy], [R + 2, T]], shade(roofc, .8));
    s += poly([[L - 2, T], [L + w * .08, T - rh * .55], [x, T - rh], [R - w * .08, T - rh * .55], [R + 2, T]], roofc);
    s += `<path d="M${f(x - w * .2)},${f(y)} V${f(y - h * .6)} H${f(x + w * .2)} V${f(y)}" fill="${shade(wall, .7)}" stroke="${C.ink}" stroke-width=".9"/>`;
    s += `<path d="M${f(x - w * .2)},${f(y - h * .6)} L${f(x + w * .2)},${f(y)} M${f(x + w * .2)},${f(y - h * .6)} L${f(x - w * .2)},${f(y)}" stroke="${C.cream}" stroke-width="1.2"/>`;
  }
  if (o.chimney) { const cx = x + w * .28; s += rect(cx, T - rh * .75, w * .1, rh * .55, C.brick); s += `<path d="M${f(cx + w * .05)},${f(T - rh * .8)} q-3,-5 1,-9 q4,-4 0,-9" stroke="${C.tealLL}" stroke-width="1.2" fill="none" opacity=".35"/>`; }
  const wy = T + h * .1, wh = h * (o.door === false ? .85 : .62);
  s += windows(L + w * .06, wy, w * .88, wh, o.cols ?? 3, o.rows ?? 1, o.lit ?? .7, { arch: o.arch, skip: o.door !== false ? (r, c) => r === (o.rows ?? 1) - 1 && c === Math.floor((o.cols ?? 3) / 2) && (o.cols ?? 3) % 2 === 1 : null });
  if (o.door !== false) s += door(x, y, Math.max(4, w * .14), Math.max(7, h * .42), o.doorc);
  if (o.porch) { s += poly([[L + w * .25, y - h * .5], [R - w * .25, y - h * .5], [R - w * .2, y - h * .58], [L + w * .2, y - h * .58]], shade(roofc, 1.1)); }
  if (o.sign) s += signboard(x, T + h * .02 - 1, o.sign, o.signc);
  if (o.awning) { const n = 6, aw = w * .9 / n; for (let i = 0; i < n; i++) s += poly([[L + w * .05 + i * aw, y - h * .52], [L + w * .05 + (i + 1) * aw, y - h * .52], [L + w * .05 + (i + 1) * aw, y - h * .42], [L + w * .05 + i * aw, y - h * .42]], i % 2 ? C.cream : o.awning, `stroke-width=".5"`); }
  if (o.pumpkins) s += pumpkin(L + 3, y - 1, 2.4) + pumpkin(R - 4, y - 1, 2);
  return s;
}
function signboard(x, y, text, col = C.red) {
  const w = text.length * 2.6 + 6;
  return `<rect x="${f(x - w / 2)}" y="${f(y - 5)}" width="${f(w)}" height="7" rx="1.5" fill="${col}" stroke="${C.ink}" stroke-width=".7"/><text x="${f(x)}" y="${f(y + .4)}" font-family="Atkinson" font-weight="700" font-size="4.6" fill="${C.parch}" text-anchor="middle">${text}</text>`;
}
function pumpkin(x, y, r) {
  return `<ellipse cx="${f(x)}" cy="${f(y - r * .8)}" rx="${f(r * 1.25)}" ry="${f(r)}" fill="${C.pump}" stroke="${C.ink}" stroke-width=".6"/>` +
    `<path d="M${f(x - r * .4)},${f(y - r * .9)} l${f(r * .2)},-${f(r * .3)} l${f(r * .2)},${f(r * .3)} M${f(x + r * .1)},${f(y - r * .9)} l${f(r * .2)},-${f(r * .3)} l${f(r * .2)},${f(r * .3)}" fill="${C.amberL}" stroke="none"/>` +
    `<path d="M${f(x)},${f(y - r * 1.75)} v-${f(r * .4)}" stroke="${C.moss}" stroke-width="${f(r * .3)}"/>` + circ(x, y - r * .8, r * 3, C.amber, `opacity=".12"`);
}
function tree(x, y, r, kind = 'round') {
  let s = `<ellipse cx="${f(x + r * .3)}" cy="${f(y + 1)}" rx="${f(r * 1.1)}" ry="${f(r * .35)}" fill="#0d1a1c" opacity=".4"/>`;
  if (kind === 'pine') {
    s += `<rect x="${f(x - r * .12)}" y="${f(y - r * .5)}" width="${f(r * .24)}" height="${f(r * .5)}" fill="#4a3426"/>`;
    for (let i = 0; i < 3; i++) { const yy = y - r * .4 - i * r * .7, ww = r * (1 - i * .25); s += poly([[x - ww, yy], [x, yy - r * 1.1], [x + ww, yy]], i % 2 ? C.mossD : '#2e4a36', `stroke-width=".7"`); }
  } else if (kind === 'bare') {
    s += `<path d="M${f(x)},${f(y)} V${f(y - r * 1.6)} M${f(x)},${f(y - r)} l-${f(r * .7)},-${f(r * .7)} M${f(x)},${f(y - r * 1.3)} l${f(r * .6)},-${f(r * .6)} M${f(x - r * .4)},${f(y - r * 1.4)} l-${f(r * .2)},-${f(r * .4)}" stroke="#3a2a28" stroke-width="${f(r * .18)}" stroke-linecap="round" fill="none"/>`;
  } else {
    const col = kind === 'orange' ? '#b8692e' : kind === 'gold' ? '#c79a3a' : '#3b5e44';
    s += `<rect x="${f(x - r * .14)}" y="${f(y - r * .9)}" width="${f(r * .28)}" height="${f(r * .9)}" fill="#4a3426" stroke="${C.ink}" stroke-width=".5"/>`;
    s += circ(x, y - r * 1.4, r, col, `stroke="${C.ink}" stroke-width=".8"`) + circ(x - r * .45, y - r * 1.15, r * .6, col, `stroke="${C.ink}" stroke-width=".8"`) + circ(x + r * .45, y - r * 1.1, r * .6, col, `stroke="${C.ink}" stroke-width=".8"`);
    s += circ(x - r * .25, y - r * 1.7, r * .35, shade(col, 1.25), `opacity=".7"`);
  }
  return s;
}
function lamp(x, y, s = 1) {
  return circ(x, y - 7 * s, 9 * s, C.amber, `opacity=".16"`) + `<line x1="${f(x)}" y1="${f(y)}" x2="${f(x)}" y2="${f(y - 7 * s)}" stroke="${C.ink}" stroke-width="${f(.9 * s)}"/>` + circ(x, y - 7.5 * s, 1.6 * s, C.amberL, `stroke="${C.ink}" stroke-width=".5"`);
}
function grave(x, y, s = 1) { return `<path d="M${f(x - 2.5 * s)},${f(y)} V${f(y - 4 * s)} A${f(2.5 * s)},${f(2.5 * s)} 0 0 1 ${f(x + 2.5 * s)},${f(y - 4 * s)} V${f(y)} Z" fill="${C.stone}" stroke="${C.ink}" stroke-width=".6"/>`; }
function label(x, y, text, size = 7, sub) {
  const w = text.length * size * .52 + 10; let s = `<g>`;
  s += `<path d="M${f(x - w / 2 - 5)},${f(y - size * .1)} l4,-${f(size * .55)} v${f(size * 1.25)} Z M${f(x + w / 2 + 5)},${f(y - size * .1)} l-4,-${f(size * .55)} v${f(size * 1.25)} Z" fill="${C.parchDD}" stroke="${C.ink}" stroke-width=".6"/>`;
  s += `<rect x="${f(x - w / 2)}" y="${f(y - size * .85)}" width="${f(w)}" height="${f(size * 1.35)}" rx="1" fill="${C.parch}" stroke="${C.ink}" stroke-width=".7"/>`;
  s += `<text x="${f(x)}" y="${f(y + size * .2)}" font-family="Fraunces" font-weight="700" font-size="${size}" fill="${C.ink}" text-anchor="middle">${text}</text>`;
  if (sub) s += `<text x="${f(x)}" y="${f(y + size * 1.25)}" font-family="Atkinson" font-style="italic" font-size="${f(size * .55)}" fill="${C.parch}" text-anchor="middle" stroke="${C.teal}" stroke-width="1.6" paint-order="stroke">${sub}</text>`;
  return s + '</g>';
}

// ---------- Cute storybook portrait (bust) for cards and the box ----------
// p: {skin, hair, hairStyle, outfit, outfit2, acc, eyes, mood, beard, glasses, hat, hatc}
function portrait(p, cx = 100, cy = 120, k = 1) {
  const sk = p.skin || '#f1c9a5', hr = p.hair || '#5a3a2a', of = p.outfit || C.sage, of2 = p.outfit2 || shade(of, .75);
  const S = v => f(v * k), X = v => f(cx + v * k), Y = v => f(cy + v * k);
  let s = '';
  // shoulders / outfit
  s += `<path d="M${X(-62)},${Y(110)} C${X(-60)},${Y(55)} ${X(-30)},${Y(40)} ${X(0)},${Y(40)} C${X(30)},${Y(40)} ${X(60)},${Y(55)} ${X(62)},${Y(110)} Z" fill="${of}" stroke="${C.ink}" stroke-width="${S(2.2)}"/>`;
  if (p.collar === 'cape') s += `<path d="M${X(-58)},${Y(80)} C${X(-50)},${Y(48)} ${X(-25)},${Y(40)} ${X(0)},${Y(44)} C${X(25)},${Y(40)} ${X(50)},${Y(48)} ${X(58)},${Y(80)} C${X(30)},${Y(70)} ${X(-30)},${Y(70)} ${X(-58)},${Y(80)} Z" fill="${of2}" stroke="${C.ink}" stroke-width="${S(2)}"/>`;
  else if (p.collar === 'apron') s += `<path d="M${X(-24)},${Y(110)} V${Y(58)} H${X(24)} V${Y(110)}" fill="${C.parch}" stroke="${C.ink}" stroke-width="${S(2)}"/>`;
  else if (p.collar === 'tie') s += `<path d="M${X(-14)},${Y(42)} L${X(0)},${Y(56)} L${X(14)},${Y(42)}" fill="#fff" stroke="${C.ink}" stroke-width="${S(1.8)}"/><path d="M${X(0)},${Y(54)} l${S(-5)},${S(8)} l${S(5)},${S(30)} l${S(5)},${S(-30)} Z" fill="${p.tie || C.red}" stroke="${C.ink}" stroke-width="${S(1.6)}"/>`;
  else if (p.collar === 'overall') s += `<path d="M${X(-28)},${Y(110)} V${Y(62)} H${X(28)} V${Y(110)} M${X(-22)},${Y(62)} L${X(-34)},${Y(42)} M${X(22)},${Y(62)} L${X(34)},${Y(42)}" fill="${of2}" stroke="${C.ink}" stroke-width="${S(2)}"/>`;
  else s += `<path d="M${X(-18)},${Y(42)} Q${X(0)},${Y(58)} ${X(18)},${Y(42)}" fill="${shade(of, 1.3)}" stroke="${C.ink}" stroke-width="${S(1.8)}"/>`;
  if (p.scarf) s += `<path d="M${X(-24)},${Y(40)} Q${X(0)},${Y(54)} ${X(24)},${Y(40)} L${X(22)},${Y(50)} Q${X(0)},${Y(62)} ${X(-22)},${Y(50)} Z M${X(10)},${Y(52)} l${S(4)},${S(26)} l${S(9)},${S(-2)} l${S(-5)},${S(-26)}" fill="${p.scarf}" stroke="${C.ink}" stroke-width="${S(1.8)}"/>`;
  // neck
  s += `<rect x="${X(-10)}" y="${Y(22)}" width="${S(20)}" height="${S(22)}" fill="${shade(sk, .88)}" stroke="${C.ink}" stroke-width="${S(1.8)}"/>`;
  // back hair
  if (p.hairStyle === 'long' || p.hairStyle === 'bob') s += `<path d="M${X(-46)},${Y(-20)} C${X(-54)},${Y(p.hairStyle === 'long' ? 50 : 20)} ${X(-30)},${Y(p.hairStyle === 'long' ? 58 : 30)} ${X(0)},${Y(p.hairStyle === 'long' ? 52 : 24)} C${X(30)},${Y(p.hairStyle === 'long' ? 58 : 30)} ${X(54)},${Y(p.hairStyle === 'long' ? 50 : 20)} ${X(46)},${Y(-20)} Z" fill="${shade(hr, .85)}" stroke="${C.ink}" stroke-width="${S(2)}"/>`;
  if (p.hairStyle === 'bun') s += circ(cx, cy - 58 * k, 16 * k, hr, `stroke="${C.ink}" stroke-width="${S(2)}"`);
  // ears + head
  s += circ(cx - 44 * k, cy - 4 * k, 8 * k, sk, `stroke="${C.ink}" stroke-width="${S(2)}"`) + circ(cx + 44 * k, cy - 4 * k, 8 * k, sk, `stroke="${C.ink}" stroke-width="${S(2)}"`);
  s += `<ellipse cx="${X(0)}" cy="${Y(-8)}" rx="${S(45)}" ry="${S(43)}" fill="${sk}" stroke="${C.ink}" stroke-width="${S(2.2)}"/>`;
  // cheeks
  s += `<ellipse cx="${X(-26)}" cy="${Y(8)}" rx="${S(8)}" ry="${S(5)}" fill="${C.rose}" opacity=".55"/><ellipse cx="${X(26)}" cy="${Y(8)}" rx="${S(8)}" ry="${S(5)}" fill="${C.rose}" opacity=".55"/>`;
  // eyes
  const ey = -4, ex = 16, eye = p.eyes || '#3b2a20';
  for (const sx of [-1, 1]) {
    s += `<ellipse cx="${X(sx * ex)}" cy="${Y(ey)}" rx="${S(7.5)}" ry="${S(9)}" fill="#fff" stroke="${C.ink}" stroke-width="${S(1.4)}"/>`;
    s += `<ellipse cx="${X(sx * ex + .5)}" cy="${Y(ey + 1.5)}" rx="${S(5.3)}" ry="${S(6.8)}" fill="${eye}"/>` + circ(cx + (sx * ex + .5) * k, cy + (ey + 2) * k, 2.6 * k, '#140c0a');
    s += circ(cx + (sx * ex + 2.5) * k, cy + (ey - 1.5) * k, 2 * k, '#fff') + circ(cx + (sx * ex - 1.5) * k, cy + (ey + 4) * k, 1 * k, '#fff');
    // brows
    const bt = p.mood === 'cross' ? sx * 3 : p.mood === 'worried' ? -sx * 3 : 0;
    s += `<path d="M${X(sx * ex - 8)},${Y(ey - 14 - bt)} Q${X(sx * ex)},${Y(ey - 18)} ${X(sx * ex + 8)},${Y(ey - 14 + bt)}" stroke="${shade(hr, .7)}" stroke-width="${S(3)}" fill="none" stroke-linecap="round"/>`;
  }
  // nose + mouth
  s += `<path d="M${X(-2)},${Y(8)} Q${X(0)},${Y(11)} ${X(3)},${Y(8)}" stroke="${shade(sk, .6)}" stroke-width="${S(2)}" fill="none" stroke-linecap="round"/>`;
  if (p.mood === 'worried') s += `<path d="M${X(-7)},${Y(22)} Q${X(0)},${Y(17)} ${X(7)},${Y(22)}" stroke="${C.ink}" stroke-width="${S(2.2)}" fill="none" stroke-linecap="round"/>`;
  else if (p.mood === 'smug') s += `<path d="M${X(-8)},${Y(18)} Q${X(2)},${Y(22)} ${X(10)},${Y(15)}" stroke="${C.ink}" stroke-width="${S(2.2)}" fill="none" stroke-linecap="round"/>`;
  else if (p.mood === 'open') s += `<path d="M${X(-9)},${Y(16)} Q${X(0)},${Y(30)} ${X(9)},${Y(16)} Z" fill="#7a2f2f" stroke="${C.ink}" stroke-width="${S(2)}"/><path d="M${X(-5)},${Y(23)} Q${X(0)},${Y(27)} ${X(5)},${Y(23)}" fill="${C.rose}"/>`;
  else s += `<path d="M${X(-9)},${Y(17)} Q${X(0)},${Y(25)} ${X(9)},${Y(17)}" stroke="${C.ink}" stroke-width="${S(2.2)}" fill="none" stroke-linecap="round"/>`;
  if (p.beard) s += `<path d="M${X(-38)},${Y(4)} C${X(-36)},${Y(44)} ${X(36)},${Y(44)} ${X(38)},${Y(4)} C${X(24)},${Y(22)} ${X(-24)},${Y(22)} ${X(-38)},${Y(4)} Z" fill="${p.beard}" stroke="${C.ink}" stroke-width="${S(2)}"/><path d="M${X(-9)},${Y(17)} Q${X(0)},${Y(23)} ${X(9)},${Y(17)}" stroke="${C.ink}" stroke-width="${S(2)}" fill="none"/>`;
  if (p.mustache) s += `<path d="M${X(-16)},${Y(15)} Q${X(-8)},${Y(8)} ${X(0)},${Y(13)} Q${X(8)},${Y(8)} ${X(16)},${Y(15)} Q${X(8)},${Y(17)} ${X(0)},${Y(15)} Q${X(-8)},${Y(17)} ${X(-16)},${Y(15)} Z" fill="${p.mustache}" stroke="${C.ink}" stroke-width="${S(1.5)}"/>`;
  if (p.freckles) for (const [a, b] of [[-28, 4], [-23, 7], [-31, 9], [28, 4], [23, 7], [31, 9]]) s += circ(cx + a * k, cy + b * k, 1.2 * k, shade(sk, .7));
  // front hair
  const hs = p.hairStyle || 'short';
  if (hs === 'bald') s += `<path d="M${X(-44)},${Y(-10)} Q${X(-46)},${Y(-26)} ${X(-36)},${Y(-30)} M${X(44)},${Y(-10)} Q${X(46)},${Y(-26)} ${X(36)},${Y(-30)}" stroke="${hr}" stroke-width="${S(7)}" fill="none" stroke-linecap="round"/>`;
  else if (hs === 'spiky') s += `<path d="M${X(-46)},${Y(-12)} L${X(-50)},${Y(-40)} L${X(-34)},${Y(-44)} L${X(-30)},${Y(-62)} L${X(-12)},${Y(-52)} L${X(0)},${Y(-68)} L${X(12)},${Y(-52)} L${X(30)},${Y(-62)} L${X(34)},${Y(-44)} L${X(50)},${Y(-40)} L${X(46)},${Y(-12)} C${X(30)},${Y(-34)} ${X(-30)},${Y(-34)} ${X(-46)},${Y(-12)} Z" fill="${hr}" stroke="${C.ink}" stroke-width="${S(2)}" stroke-linejoin="round"/>`;
  else if (hs === 'curly') { for (let i = 0; i < 9; i++) { const a = Math.PI * (1.05 + i * .1); s += circ(cx + Math.cos(a) * 42 * k, cy - 14 * k + Math.sin(a) * 38 * k, 13 * k, hr, `stroke="${C.ink}" stroke-width="${S(1.8)}"`); } s += `<path d="M${X(-40)},${Y(-20)} Q${X(0)},${Y(-40)} ${X(40)},${Y(-20)} L${X(40)},${Y(-40)} L${X(-40)},${Y(-40)} Z" fill="${hr}"/>`; }
  else s += `<path d="M${X(-47)},${Y(-2)} C${X(-52)},${Y(-50)} ${X(-10)},${Y(-62)} ${X(6)},${Y(-56)} C${X(40)},${Y(-56)} ${X(54)},${Y(-36)} ${X(47)},${Y(-2)} C${X(40)},${Y(-22)} ${X(24)},${Y(-30)} ${X(hs === 'part' ? 4 : 10)},${Y(-36)} C${X(-6)},${Y(-24)} ${X(-30)},${Y(-26)} ${X(-47)},${Y(-2)} Z" fill="${hr}" stroke="${C.ink}" stroke-width="${S(2)}" stroke-linejoin="round"/>` +
    `<path d="M${X(-20)},${Y(-46)} Q${X(0)},${Y(-54)} ${X(18)},${Y(-48)}" stroke="${shade(hr, 1.35)}" stroke-width="${S(3)}" fill="none" stroke-linecap="round" opacity=".7"/>`;
  if (p.glasses) for (const sx of [-1, 1]) s += circ(cx + sx * 16 * k, cy - 3 * k, 11 * k, 'none', `stroke="${p.glasses}" stroke-width="${S(2.4)}"`) + (sx < 0 ? `<line x1="${X(-5)}" y1="${Y(-4)}" x2="${X(5)}" y2="${Y(-4)}" stroke="${p.glasses}" stroke-width="${S(2.4)}"/>` : '');
  // hats & accessories
  const hc = p.hatc || C.plum;
  if (p.hat === 'bobble') s += `<path d="M${X(-46)},${Y(-22)} C${X(-46)},${Y(-74)} ${X(46)},${Y(-74)} ${X(46)},${Y(-22)} Z" fill="${hc}" stroke="${C.ink}" stroke-width="${S(2)}"/><rect x="${X(-49)}" y="${Y(-30)}" width="${S(98)}" height="${S(13)}" rx="${S(6)}" fill="${shade(hc, 1.3)}" stroke="${C.ink}" stroke-width="${S(2)}"/>` + circ(cx, cy - 72 * k, 11 * k, C.parch, `stroke="${C.ink}" stroke-width="${S(2)}"`);
  if (p.hat === 'deerstalker' || p.hat === 'cap') s += `<path d="M${X(-46)},${Y(-24)} C${X(-46)},${Y(-70)} ${X(46)},${Y(-70)} ${X(46)},${Y(-24)} Z" fill="${hc}" stroke="${C.ink}" stroke-width="${S(2)}"/><path d="M${X(-30)},${Y(-26)} Q${X(-62)},${Y(-22)} ${X(-60)},${Y(-14)} Q${X(-40)},${Y(-18)} ${X(-20)},${Y(-24)} Z" fill="${shade(hc, .8)}" stroke="${C.ink}" stroke-width="${S(2)}"/>` + (p.hat === 'deerstalker' ? `<path d="M${X(-30)},${Y(-60)} Q${X(0)},${Y(-40)} ${X(30)},${Y(-60)}" stroke="${C.ink}" stroke-width="${S(1.2)}" fill="none" stroke-dasharray="${S(3)},${S(3)}"/>` : '');
  if (p.hat === 'top') s += `<rect x="${X(-30)}" y="${Y(-92)}" width="${S(60)}" height="${S(52)}" fill="${hc}" stroke="${C.ink}" stroke-width="${S(2)}"/><rect x="${X(-30)}" y="${Y(-52)}" width="${S(60)}" height="${S(9)}" fill="${C.red}" stroke="${C.ink}" stroke-width="${S(1.6)}"/><ellipse cx="${X(0)}" cy="${Y(-40)}" rx="${S(50)}" ry="${S(9)}" fill="${hc}" stroke="${C.ink}" stroke-width="${S(2)}"/>`;
  if (p.hat === 'crown') s += `<path d="M${X(-28)},${Y(-44)} L${X(-30)},${Y(-74)} L${X(-14)},${Y(-58)} L${X(0)},${Y(-80)} L${X(14)},${Y(-58)} L${X(30)},${Y(-74)} L${X(28)},${Y(-44)} Z" fill="${C.amber}" stroke="${C.ink}" stroke-width="${S(2)}" stroke-linejoin="round"/>` + circ(cx, cy - 56 * k, 4 * k, C.red, `stroke="${C.ink}" stroke-width="${S(1.2)}"`);
  if (p.hat === 'straw') s += `<ellipse cx="${X(0)}" cy="${Y(-38)}" rx="${S(64)}" ry="${S(12)}" fill="#d9b25f" stroke="${C.ink}" stroke-width="${S(2)}"/><path d="M${X(-32)},${Y(-40)} C${X(-32)},${Y(-78)} ${X(32)},${Y(-78)} ${X(32)},${Y(-40)} Z" fill="#e2c072" stroke="${C.ink}" stroke-width="${S(2)}"/><rect x="${X(-32)}" y="${Y(-50)}" width="${S(64)}" height="${S(7)}" fill="${C.red}"/>`;
  if (p.hat === 'chef') s += `<path d="M${X(-30)},${Y(-40)} V${Y(-58)} C${X(-50)},${Y(-60)} ${X(-44)},${Y(-92)} ${X(-20)},${Y(-84)} C${X(-14)},${Y(-104)} ${X(14)},${Y(-104)} ${X(20)},${Y(-84)} C${X(44)},${Y(-92)} ${X(50)},${Y(-60)} ${X(30)},${Y(-58)} V${Y(-40)} Z" fill="#fbf6ea" stroke="${C.ink}" stroke-width="${S(2)}"/>`;
  if (p.hat === 'flower') s += [[-30, -40], [-22, -48]].map(([a, b], i) => circ(cx + a * k, cy + b * k, 7 * k, i ? C.amberL : C.rose, `stroke="${C.ink}" stroke-width="${S(1.4)}"`)).join('');
  if (p.headphones) s += `<path d="M${X(-48)},${Y(-6)} C${X(-52)},${Y(-70)} ${X(52)},${Y(-70)} ${X(48)},${Y(-6)}" stroke="${C.ink}" stroke-width="${S(6)}" fill="none"/><rect x="${X(-58)}" y="${Y(-20)}" width="${S(16)}" height="${S(28)}" rx="${S(6)}" fill="${p.headphones}" stroke="${C.ink}" stroke-width="${S(2)}"/><rect x="${X(42)}" y="${Y(-20)}" width="${S(16)}" height="${S(28)}" rx="${S(6)}" fill="${p.headphones}" stroke="${C.ink}" stroke-width="${S(2)}"/><path d="M${X(50)},${Y(-20)} L${X(60)},${Y(-60)}" stroke="${C.ink}" stroke-width="${S(2)}"/>` + circ(cx + 60 * k, cy - 62 * k, 4 * k, C.red, `stroke="${C.ink}" stroke-width="${S(1.4)}"`);
  if (p.earring) s += circ(cx - 44 * k, cy + 6 * k, 3.5 * k, C.amber, `stroke="${C.ink}" stroke-width="${S(1)}"`);
  if (p.locket) s += `<path d="M${X(-16)},${Y(42)} Q${X(0)},${Y(68)} ${X(16)},${Y(42)}" stroke="${C.amber}" stroke-width="${S(1.6)}" fill="none"/>` + circ(cx, cy + 66 * k, 5 * k, C.amber, `stroke="${C.ink}" stroke-width="${S(1.4)}"`);
  if (p.pencil) s += `<path d="M${X(40)},${Y(-30)} l${S(14)},${S(-14)}" stroke="#e2b23c" stroke-width="${S(5)}" stroke-linecap="round"/>`;
  return s;
}

// Folklore Haunter faces (the masks), drawn as cute-spooky icons.
function haunter(kind, cx, cy, k = 1) {
  const X = v => f(cx + v * k), Y = v => f(cy + v * k), S = v => f(v * k);
  let s = circ(cx, cy, 70 * k, C.violet, `opacity=".22"`);
  // cloak
  s += `<path d="M${X(-50)},${Y(90)} C${X(-60)},${Y(10)} ${X(-44)},${Y(-60)} ${X(0)},${Y(-64)} C${X(44)},${Y(-60)} ${X(60)},${Y(10)} ${X(50)},${Y(90)} Q${X(34)},${Y(78)} ${X(25)},${Y(92)} Q${X(12)},${Y(78)} ${X(0)},${Y(92)} Q${X(-12)},${Y(78)} ${X(-25)},${Y(92)} Q${X(-34)},${Y(78)} ${X(-50)},${Y(90)} Z" fill="#3b2c52" stroke="${C.ink}" stroke-width="${S(2.2)}"/>`;
  if (kind === 'jack') {
    s += `<ellipse cx="${X(0)}" cy="${Y(-14)}" rx="${S(40)}" ry="${S(34)}" fill="${C.pump}" stroke="${C.ink}" stroke-width="${S(2.2)}"/><path d="M${X(-14)},${Y(-46)} Q${X(0)},${Y(-30)} ${X(14)},${Y(-46)} M${X(-28)},${Y(-40)} Q${X(-36)},${Y(-10)} ${X(-26)},${Y(16)} M${X(28)},${Y(-40)} Q${X(36)},${Y(-10)} ${X(26)},${Y(16)}" stroke="${C.amberD}" stroke-width="${S(1.6)}" fill="none"/><rect x="${X(-4)}" y="${Y(-58)}" width="${S(8)}" height="${S(12)}" fill="${C.moss}" stroke="${C.ink}" stroke-width="${S(1.4)}"/>`;
    s += `<path d="M${X(-22)},${Y(-20)} l${S(8)},${S(-12)} l${S(8)},${S(12)} Z M${X(6)},${Y(-20)} l${S(8)},${S(-12)} l${S(8)},${S(12)} Z M${X(-20)},${Y(0)} Q${X(0)},${Y(18)} ${X(20)},${Y(0)} l${S(-6)},${S(4)} l${S(-4)},${S(-4)} l${S(-5)},${S(5)} l${S(-5)},${S(-5)} l${S(-4)},${S(4)} Z" fill="${C.amberL}" stroke="${C.ink}" stroke-width="${S(1.2)}"/>`;
  } else if (kind === 'banshee') {
    s += `<path d="M${X(-38)},${Y(30)} C${X(-50)},${Y(-40)} ${X(-20)},${Y(-62)} ${X(0)},${Y(-62)} C${X(20)},${Y(-62)} ${X(50)},${Y(-40)} ${X(38)},${Y(30)} Z" fill="#cfd8e8" stroke="${C.ink}" stroke-width="${S(2)}"/><ellipse cx="${X(0)}" cy="${Y(-14)}" rx="${S(26)}" ry="${S(32)}" fill="#eef2f8" stroke="${C.ink}" stroke-width="${S(2)}"/>`;
    s += `<ellipse cx="${X(-10)}" cy="${Y(-18)}" rx="${S(5)}" ry="${S(8)}" fill="${C.ink}"/><ellipse cx="${X(10)}" cy="${Y(-18)}" rx="${S(5)}" ry="${S(8)}" fill="${C.ink}"/><ellipse cx="${X(0)}" cy="${Y(4)}" rx="${S(6)}" ry="${S(9)}" fill="${C.plum}"/>`;
  } else if (kind === 'horseman') {
    s += `<path d="M${X(-30)},${Y(-30)} L${X(30)},${Y(-30)} L${X(36)},${Y(10)} L${X(-36)},${Y(10)} Z" fill="#2a2234" stroke="${C.ink}" stroke-width="${S(2)}"/><path d="M${X(-36)},${Y(10)} L${X(0)},${Y(30)} L${X(36)},${Y(10)}" fill="${C.red}" stroke="${C.ink}" stroke-width="${S(2)}"/>` + `<g transform="translate(${X(30)},${Y(40)})">` + `<ellipse cx="0" cy="0" rx="${S(20)}" ry="${S(16)}" fill="${C.pump}" stroke="${C.ink}" stroke-width="${S(1.8)}"/><path d="M${S(-10)},${S(-4)} l${S(5)},${S(-6)} l${S(5)},${S(6)} Z M${S(2)},${S(-4)} l${S(5)},${S(-6)} l${S(5)},${S(6)} Z M${S(-10)},${S(5)} Q0,${S(12)} ${S(10)},${S(5)} Z" fill="${C.amberL}"/></g>`;
  } else if (kind === 'baba') {
    s += `<path d="M${X(-50)},${Y(-20)} L${X(0)},${Y(-110)} L${X(50)},${Y(-20)} Z" fill="#33283f" stroke="${C.ink}" stroke-width="${S(2)}"/><ellipse cx="${X(0)}" cy="${Y(-20)}" rx="${S(58)}" ry="${S(10)}" fill="#33283f" stroke="${C.ink}" stroke-width="${S(2)}"/><ellipse cx="${X(0)}" cy="${Y(0)}" rx="${S(26)}" ry="${S(24)}" fill="#a9b98a" stroke="${C.ink}" stroke-width="${S(2)}"/>` + circ(cx - 9 * k, cy - 4 * k, 4 * k, C.amberL, `stroke="${C.ink}" stroke-width="${S(1.2)}"`) + circ(cx + 9 * k, cy - 4 * k, 4 * k, C.amberL, `stroke="${C.ink}" stroke-width="${S(1.2)}"`) + `<path d="M${X(0)},${Y(0)} q${S(8)},${S(8)} ${S(2)},${S(12)}" fill="#93a676" stroke="${C.ink}" stroke-width="${S(1.4)}"/><path d="M${X(-8)},${Y(14)} q${S(8)},${S(4)} ${S(16)},0" stroke="${C.ink}" stroke-width="${S(1.6)}" fill="none"/>`;
  }
  return s;
}

// Icons for traits / clue tokens
const ICON = {
  sawdust: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><path d="M-14,8 Q0,-6 14,8 Z" fill="#d9b46a" stroke="${C.ink}" stroke-width="1.6"/>${[-8, -2, 5, 9].map((a, i) => `<circle cx="${a}" cy="${-4 - i % 2 * 4}" r="1.5" fill="#d9b46a" stroke="${C.ink}" stroke-width=".8"/>`).join('')}</g>`,
  glitter: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})">${[[0, 0, 9], [-9, 6, 5], [9, -7, 5]].map(([a, b, r]) => `<path d="M${a},${b - r} Q${a},${b} ${a + r},${b} Q${a},${b} ${a},${b + r} Q${a},${b} ${a - r},${b} Q${a},${b} ${a},${b - r} Z" fill="#f29ac0" stroke="${C.ink}" stroke-width="1.2"/>`).join('')}</g>`,
  pomade: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><rect x="-11" y="-6" width="22" height="13" rx="3" fill="#9fcf8a" stroke="${C.ink}" stroke-width="1.6"/><rect x="-12" y="-10" width="24" height="5" rx="2" fill="${C.amber}" stroke="${C.ink}" stroke-width="1.4"/></g>`,
  icing: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><path d="M-10,10 L-8,-2 H8 L10,10 Z" fill="${C.rose}" stroke="${C.ink}" stroke-width="1.5"/><path d="M-10,-2 Q-10,-12 0,-12 Q10,-12 10,-2 Z" fill="#fff" stroke="${C.ink}" stroke-width="1.5"/>${circ(0, -14, 3, C.red, `stroke="${C.ink}" stroke-width="1"`)}</g>`,
  key: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><circle cx="-7" cy="0" r="6" fill="none" stroke="${C.amberD}" stroke-width="3.4"/><path d="M-1,0 H13 M8,0 V5 M12,0 V4" stroke="${C.amberD}" stroke-width="3.4" stroke-linecap="round"/></g>`,
  soil: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><path d="M-10,10 L-12,-4 H12 L10,10 Z" fill="${C.brick}" stroke="${C.ink}" stroke-width="1.5"/><path d="M0,-4 Q-2,-14 -8,-14 Q-4,-8 0,-4 Q2,-14 8,-15 Q4,-8 0,-4" fill="${C.sage}" stroke="${C.ink}" stroke-width="1.2"/></g>`,
  locket: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><path d="M-8,-14 Q0,-4 8,-14" stroke="${C.amber}" stroke-width="1.6" fill="none"/><path d="M0,10 C-14,0 -10,-12 0,-6 C10,-12 14,0 0,10 Z" fill="${C.amber}" stroke="${C.ink}" stroke-width="1.5"/></g>`,
  tea: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><path d="M-10,-4 H8 V4 Q8,10 -1,10 Q-10,10 -10,4 Z" fill="${C.cream}" stroke="${C.ink}" stroke-width="1.5"/><path d="M8,-1 Q14,-1 13,4 Q12,7 8,6" fill="none" stroke="${C.ink}" stroke-width="1.5"/><path d="M-5,-8 q-3,-4 0,-7 M1,-8 q-3,-4 0,-7" stroke="${C.tealL}" stroke-width="1.4" fill="none"/></g>`,
  ghost: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><path d="M-10,10 V-2 Q-10,-13 0,-13 Q10,-13 10,-2 V10 L6,7 L3,10 L0,7 L-3,10 L-6,7 Z" fill="#efeaf7" stroke="${C.ink}" stroke-width="1.5"/><circle cx="-4" cy="-3" r="1.8" fill="${C.ink}"/><circle cx="4" cy="-3" r="1.8" fill="${C.ink}"/></g>`,
  lantern: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><circle cx="0" cy="2" r="14" fill="${C.amber}" opacity=".3"/><path d="M-4,-12 Q0,-17 4,-12" stroke="${C.ink}" stroke-width="1.4" fill="none"/><rect x="-7" y="-11" width="14" height="4" fill="${C.ink}"/><path d="M-7,-7 Q-10,2 -6,10 H6 Q10,2 7,-7 Z" fill="${C.amberL}" stroke="${C.ink}" stroke-width="1.5"/><rect x="-7" y="9" width="14" height="3" fill="${C.ink}"/></g>`,
  magnifier: (x, y, k) => `<g transform="translate(${x},${y}) scale(${k})"><circle cx="-3" cy="-3" r="8" fill="${C.tealLL}" stroke="${C.ink}" stroke-width="2.2"/><path d="M3,3 L11,11" stroke="${C.ink}" stroke-width="4" stroke-linecap="round"/></g>`,
};
const TRAIT_ICON = ['sawdust', 'glitter', 'pomade', 'icing', 'key', 'soil', 'locket', 'tea'];
const TRAIT_NAME = ['Sawdust', 'Glitter', 'Hair pomade', 'Icing sugar', 'Spare key', 'Potting soil', 'Gold locket', 'Chamomile tea'];
const SLOT_TRAITS = [[0, 4, 5], [1, 4, 6], [2, 6, 7], [3, 7, 5]];

// Paper grain filter + defs used by every page
const DEFS = `<defs>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="4"/><feColorMatrix values="0 0 0 0 .3  0 0 0 0 .22  0 0 0 0 .15  0 0 0 .22 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<filter id="mottle" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="4" seed="9"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 .05  0 0 0 0 .04  0 0 0 .55 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<radialGradient id="vig" cx="50%" cy="50%" r="70%"><stop offset="60%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity=".45"/></radialGradient>
<radialGradient id="moon" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#fff7da"/><stop offset="60%" stop-color="#f6e7b4"/><stop offset="100%" stop-color="#f6e7b4" stop-opacity="0"/></radialGradient>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14263a"/><stop offset=".6" stop-color="#25475a"/><stop offset="1" stop-color="#3c6467"/></linearGradient>
</defs>`;
const FONTS = `<style>
@font-face{font-family:Fraunces;src:url(fonts/Fraunces-Title.ttf);font-weight:700}
@font-face{font-family:FrauncesD;src:url(fonts/Fraunces-Display.ttf)}
@font-face{font-family:Atkinson;src:url(fonts/Atkinson-Regular.ttf)}
@font-face{font-family:Atkinson;src:url(fonts/Atkinson-Bold.ttf);font-weight:700}
html,body{margin:0;padding:0;background:transparent}</style>`;
if (typeof module !== 'undefined') module.exports = {};
