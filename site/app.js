/* Unmasked site: theme, menu, the pinned-paper physics, the red string and the Suspect Board.
   The cases come from data/game.json, which Docs/tools/make_site_data.py exports from the game. */
(() => {
  "use strict";
  document.documentElement.classList.add("js");
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const motionQuery = matchMedia("(prefers-reduced-motion: reduce)");
  const still = () => motionQuery.matches;
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const listNames = (names) => names.length <= 1 ? names.join("") : names.slice(0, -1).join(", ") + " and " + names[names.length - 1];

  /* ---------------- Theme ---------------- */
  const themeBtn = $("[data-theme-toggle]");
  const systemDark = matchMedia("(prefers-color-scheme: dark)");
  const isDark = () => (document.documentElement.dataset.theme || (systemDark.matches ? "dark" : "light")) === "dark";
  function paintThemeButton() {
    const dark = isDark();
    themeBtn.setAttribute("aria-pressed", String(dark));
    themeBtn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    $(".theme-label", themeBtn).textContent = dark ? "Light" : "Dark";
  }
  themeBtn.addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("unmasked-theme", next); } catch (e) { /* private window: just don't remember */ }
    paintThemeButton();
  });
  systemDark.addEventListener("change", paintThemeButton);
  paintThemeButton();

  /* ---------------- Menu (narrow screens) ---------------- */
  const menuBtn = $(".menu-btn"), menu = $("#menu");
  const setMenu = (open) => { menu.classList.toggle("open", open); menuBtn.setAttribute("aria-expanded", String(open)); };
  menuBtn.addEventListener("click", () => setMenu(!menu.classList.contains("open")));
  menu.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && menu.classList.contains("open")) { setMenu(false); menuBtn.focus(); } });
  document.addEventListener("pointerdown", (e) => { if (!e.target.closest("nav")) setMenu(false); });

  /* ---------------- Swing: paper hanging from a pin ----------------
     Each card is a damped pendulum around its pin. Brushing past with the pointer gives it a push
     proportional to how fast you moved; it swings back and settles in about a second. */
  const Swing = (() => {
    const STIFF = 140, DAMP = 7.5, MAX_V = 70;
    const items = new Set();
    let raf = 0, last = 0;
    function tick(now) {
      const dt = Math.min(0.032, (now - last) / 1000);
      last = now;
      let busy = false;
      for (const s of items) {
        if (s.a === 0 && s.v === 0) continue;
        s.v += (-STIFF * s.a - DAMP * s.v) * dt;
        s.a += s.v * dt;
        if (Math.abs(s.a) < 0.03 && Math.abs(s.v) < 0.08) { s.a = 0; s.v = 0; } else busy = true;
        s.el.style.setProperty("--sway", s.a.toFixed(2) + "deg");
      }
      raf = busy ? requestAnimationFrame(tick) : 0;
    }
    return {
      add(el) { if (!el._swing) { el._swing = { el, a: 0, v: 0 }; items.add(el._swing); } },
      clear() { for (const s of items) if (!s.el.isConnected) items.delete(s); },
      push(el, v) {
        const s = el && el._swing;
        if (!s || still()) return;
        s.v = Math.max(-MAX_V, Math.min(MAX_V, s.v + v));
        if (!raf) { last = performance.now(); raf = requestAnimationFrame(tick); }
      },
    };
  })();

  /* Brushing: track the pointer over a board and push whatever it crosses. */
  function brushable(container, selector) {
    let lx = null, lt = 0, over = null;
    container.addEventListener("pointermove", (e) => {
      const now = performance.now();
      if (lx !== null && now > lt) {
        const vx = (e.clientX - lx) / (now - lt); // px per ms
        const card = e.target.closest(selector);
        if (card && card !== over) Swing.push(card, vx * 22); // entering a card: one push
        over = card;
      }
      lx = e.clientX; lt = now;
    });
    container.addEventListener("pointerleave", () => { lx = null; over = null; });
  }

  /* ---------------- The red string ----------------
     A path from pin to pin with a little sag, as real string has. Drawn with a quick ease-out so
     the eye follows it from the clue to the suspect. */
  function pinPoint(el, svgBox) {
    const pin = el.querySelector(".pin, .tag-hole") || el;
    const r = pin.getBoundingClientRect();
    return { x: r.left + r.width / 2 - svgBox.left, y: r.top + r.height / 2 - svgBox.top };
  }
  function string(svg, from, to, { delay = 0, draw = true, className = "" } = {}) {
    const box = svg.getBoundingClientRect();
    const a = pinPoint(from, box), b = pinPoint(to, box);
    const len = Math.hypot(b.x - a.x, b.y - a.y);
    const sag = Math.min(46, len * 0.12);
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M${a.x.toFixed(1)} ${a.y.toFixed(1)} Q${((a.x + b.x) / 2).toFixed(1)} ${(Math.max(a.y, b.y) + sag).toFixed(1)} ${b.x.toFixed(1)} ${b.y.toFixed(1)}`);
    if (className) path.setAttribute("class", className);
    svg.appendChild(path);
    if (draw && !still() && path.getTotalLength) {
      const L = path.getTotalLength();
      path.style.strokeDasharray = L;
      path.style.strokeDashoffset = L;
      path.animate([{ strokeDashoffset: L }, { strokeDashoffset: 0 }], { duration: 520, delay, easing: "cubic-bezier(.23,1,.32,1)", fill: "forwards" })
        .finished.then(() => { path.style.strokeDasharray = ""; path.style.strokeDashoffset = ""; }).catch(() => {});
    }
    return path;
  }

  /* ---------------- Hero: two clues, one suspect ---------------- */
  const hero = $("[data-hero]");
  if (hero) {
    const svg = $(".strings", hero);
    const byId = (id) => $(`[data-id="${id}"]`, hero);
    const links = [["c4", "s0"], ["c4", "s1"], ["c6", "s1"], ["c6", "s2"]];
    $$(".pinned", hero).forEach(Swing.add);
    brushable(hero, ".pinned");
    let played = false;
    const settle = () => {
      ["s0", "s2", "s3"].forEach((id) => byId(id).classList.add("out"));
      byId("s1").classList.add("left");
    };
    const drawAll = (animate) => {
      svg.replaceChildren();
      links.forEach(([c, s], i) => string(svg, byId(c), byId(s), { draw: animate, delay: i * 220 + (i > 1 ? 260 : 0) }));
    };
    const play = () => {
      if (played) return;
      played = true;
      drawAll(true);
      if (still()) settle();
      else setTimeout(() => { settle(); Swing.push(byId("s1"), 40); }, 1500);
    };
    document.fonts.ready.then(() => {
      const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { play(); io.disconnect(); } }, { threshold: 0.4 });
      io.observe(hero);
    });
    new ResizeObserver(() => { if (played) drawAll(false); }).observe(hero);
  }

  /* ---------------- Data ---------------- */
  let game = null;
  async function load() {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 10000);
    try {
      const res = await fetch("data/game.json", { signal: ctl.signal, cache: "no-cache" });
      if (!res.ok) throw new Error(`The server answered ${res.status}.`);
      return await res.json();
    } finally { clearTimeout(timer); }
  }

  /* ---------------- Suspect Board ---------------- */
  const file = $("[data-casefile]");
  const tabsEl = $("[data-cases]");
  const show = (state) => {
    $$("[data-state]", file).forEach((el) => { el.hidden = el.dataset.state !== state; });
    file.setAttribute("aria-busy", String(state === "loading"));
  };
  // Solved cases are remembered in this browser only, like the host's case book in the game.
  const SOLVED_KEY = "unmasked-solved";
  const solved = new Set((() => { try { return JSON.parse(localStorage.getItem(SOLVED_KEY)) || []; } catch (e) { return []; } })());
  const saveSolved = () => { try { localStorage.setItem(SOLVED_KEY, JSON.stringify([...solved])); } catch (e) { /* private window */ } };
  const bookEl = $("[data-casebook]");
  function paintCaseBook() {
    const n = order.filter((c) => solved.has(c.id)).length;
    bookEl.hidden = n === 0;
    $("[data-casebook-text]", bookEl).textContent = n === order.length
      ? `Your case book is full: all ${n} cases solved.`
      : `Your case book: ${n} of ${order.length} cases solved.`;
  }
  $("[data-casebook-clear]", bookEl).addEventListener("click", () => {
    solved.clear();
    saveSolved();
    $$(".case-tab", tabsEl).forEach((t) => t.classList.remove("solved"));
    paintCaseBook();
    say("Case book cleared. Every case is unsolved again.");
    $$(".case-tab", tabsEl)[current]?.focus(); // the button just hid itself, so don't strand focus
  });
  let order = [], current = 0, S = null;

  const maskName = (legend) => legend.name.startsWith("The ") ? "the " + legend.name.slice(4) + " mask" : legend.name + "'s mask";

  function buildTabs() {
    tabsEl.replaceChildren(...order.map((c, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "case-tab";
      b.id = "case-tab-" + i;
      b.setAttribute("role", "tab");
      b.setAttribute("aria-controls", "play-file");
      b.innerHTML = `<b>${esc(c.name)}</b><span>${esc(c.houseName)}${c.visit > 1 ? ", return visit" : ""}</span>`;
      b.addEventListener("click", () => select(i));
      return b;
    }));
    file.id = "play-file";
    paintCaseBook();
    file.setAttribute("role", "tabpanel");
  }
  tabsEl.addEventListener("keydown", (e) => {
    const map = { ArrowRight: 1, ArrowLeft: -1, Home: -Infinity, End: Infinity };
    if (!(e.key in map)) return;
    e.preventDefault();
    let i = map[e.key] === -Infinity ? 0 : map[e.key] === Infinity ? order.length - 1 : (current + map[e.key] + order.length) % order.length;
    select(i, true);
  });

  function select(i, focus = false) {
    current = i;
    $$(".case-tab", tabsEl).forEach((t, k) => {
      const on = k === i;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      t.classList.toggle("solved", solved.has(order[k].id));
      if (on) {
        if (focus) t.focus();
        // Bring the tab into view inside the strip only; never scroll the page.
        const l = t.offsetLeft - tabsEl.offsetLeft, r = l + t.offsetWidth;
        if (l < tabsEl.scrollLeft || r > tabsEl.scrollLeft + tabsEl.clientWidth)
          tabsEl.scrollTo({ left: Math.max(0, l - 16), behavior: still() ? "auto" : "smooth" });
        file.setAttribute("aria-labelledby", t.id);
      }
    });
    start(order[i]);
  }

  function start(c) {
    const legend = game.legends[Math.floor(Math.random() * game.legends.length)];
    S = {
      c, legend,
      culprit: Math.floor(Math.random() * 4),
      found: [], out: new Set(), alibis: new Map(),
      searches: 3, checks: 2, tries: 2, over: false,
    };
    $("[data-case-name]", file).textContent = c.name;
    $("[data-case-house]", file).textContent = c.visit > 1 ? `${c.houseName}, calling again` : c.houseName;
    $("[data-premise]", file).innerHTML = `${esc(c.premise)} Tonight someone is wearing <em>${esc(maskName(legend))}</em>.`;
    $("[data-verdict]", file).hidden = true;
    $("[data-log]", file).textContent = "";
    $("[data-tags]", file).replaceChildren();
    renderSuspects();
    refresh();
  }

  function renderSuspects() {
    const list = $("[data-suspects]", file);
    const tilt = [-1.6, 1.2, -0.8, 1.8];
    list.replaceChildren(...S.c.suspects.map((s, i) => {
      const li = document.createElement("li");
      li.className = "suspect";
      li.dataset.i = i;
      li.style.setProperty("--r", tilt[i] + "deg");
      li.innerHTML = `<span class="pin"></span>
        <h4><span class="name">${esc(s.name)}</span></h4>
        <p class="job">${esc(s.job)}</p>
        <p class="bio">${esc(s.bio)}</p>
        <p class="alibi"><strong>Alibi:</strong> ${esc(s.alibi)} <span data-alibi></span></p>
        <p class="fits" data-fits></p>
        <p class="reveal" data-reveal></p>
        <p class="row">
          <button type="button" class="mini" data-act="out" aria-pressed="false">Cross off</button>
          <button type="button" class="mini" data-act="alibi">Check alibi</button>
          <button type="button" class="mini accuse" data-act="accuse">Accuse</button>
        </p>`;
      Swing.add(li);
      return li;
    }));
    Swing.clear();
  }

  function fitsFor(i) {
    return S.found.filter((t) => S.c.suspects[i].traits.includes(t));
  }

  function refresh() {
    const c = S.c;
    $$(".suspect", file).forEach((li, i) => {
      const out = S.out.has(i);
      li.classList.toggle("out", out);
      const outBtn = $('[data-act="out"]', li);
      outBtn.textContent = out ? "Put back" : "Cross off";
      outBtn.setAttribute("aria-pressed", String(out));
      outBtn.setAttribute("aria-label", `${out ? "Put back" : "Cross off"} ${c.suspects[i].name}`);
      const alibiBtn = $('[data-act="alibi"]', li);
      alibiBtn.disabled = S.over || S.checks === 0 || S.alibis.has(i);
      alibiBtn.setAttribute("aria-label", `Check ${c.suspects[i].name}'s alibi`);
      const acc = $('[data-act="accuse"]', li);
      acc.disabled = S.over || out;
      acc.setAttribute("aria-label", `Accuse ${c.suspects[i].name}`);
      outBtn.disabled = S.over;
      const verdict = S.alibis.get(i);
      $("[data-alibi]", li).innerHTML = verdict === undefined ? "" : verdict
        ? `<span class="holds">It holds.</span>` : `<span class="broken">Nobody saw them there.</span>`;
      const fits = fitsFor(i);
      $("[data-fits]", li).textContent = S.found.length === 0 ? "" : fits.length === 0 ? "Fits none of the clues"
        : `Fits ${fits.length === S.found.length && S.found.length > 1 ? "every clue" : listNames(fits.map((t) => c.clues[t].name.toLowerCase()))}`;
    });
    const empty = $("[data-empty]", file);
    empty.hidden = S.found.length > 0;
    const search = $("[data-search]", file);
    search.disabled = S.over || S.searches === 0;
    search.textContent = S.searches === 0 && !S.over ? "Nothing left to find" : "Search the house";
    const plural = (n, one, many) => `<b>${n}</b> ${n === 1 ? one : many}`;
    $("[data-counts]", file).innerHTML = S.over ? "Case over." :
      `${plural(S.searches, "search", "searches")}, ${plural(S.checks, "alibi check", "alibi checks")} and ${plural(S.tries, "accusation", "accusations")} left`;
    drawStrings(false);
  }

  function drawStrings(animateLast) {
    const board = $("[data-board]", file);
    const svg = $(".strings", board);
    svg.replaceChildren();
    if (getComputedStyle(svg).display === "none") return;
    const tags = $$(".tag", board);
    S.found.forEach((t, k) => {
      const tag = tags[k];
      S.c.suspects.forEach((s, i) => {
        if (!s.traits.includes(t)) return;
        const li = $(`.suspect[data-i="${i}"]`, board);
        string(svg, tag, li, { draw: animateLast && k === S.found.length - 1, delay: i * 90, className: S.out.has(i) ? "ghosted" : "" });
      });
    });
  }

  function say(html) { $("[data-log]", file).innerHTML = html; }

  function search() {
    if (S.over || S.searches === 0) return;
    const left = S.c.suspects[S.culprit].traits.filter((t) => !S.found.includes(t));
    const t = left[Math.floor(Math.random() * left.length)];
    S.found.push(t);
    S.searches--;
    const clue = S.c.clues[t];
    const li = document.createElement("li");
    li.className = "tag new";
    li.innerHTML = `<span class="tag-hole"></span><b>${esc(clue.name)}</b>${esc(clue.description)}`;
    $("[data-tags]", file).appendChild(li);
    const who = S.c.suspects.filter((s) => s.traits.includes(t)).map((s) => s.name);
    say(`Found <strong>${esc(clue.name.toLowerCase())}</strong>. It fits ${esc(listNames(who))}.` +
      (S.found.length === 2 ? " That's two clues: only one person fits both." : ""));
    refresh();
    // Draw once the tag has landed so the string starts from where it ends up.
    requestAnimationFrame(() => drawStrings(true));
    S.c.suspects.forEach((s, i) => { if (s.traits.includes(t)) Swing.push($(`.suspect[data-i="${i}"]`, file), 26 * (i % 2 ? -1 : 1)); });
  }

  function act(i, what) {
    if (S.over) return;
    const s = S.c.suspects[i];
    const li = $(`.suspect[data-i="${i}"]`, file);
    if (what === "out") {
      S.out.has(i) ? S.out.delete(i) : S.out.add(i);
      Swing.push(li, 30);
      say(S.out.has(i) ? `Crossed off ${esc(s.name)}.` : `${esc(s.name)} is back on the board.`);
    } else if (what === "alibi") {
      if (S.checks === 0 || S.alibis.has(i)) return;
      S.checks--;
      const holds = i !== S.culprit;
      S.alibis.set(i, holds);
      say(holds ? `${esc(s.name)}'s alibi holds. Someone saw them where they said they'd be (${esc(s.alibiRoom)}).`
        : `Nobody saw ${esc(s.name)} where they said they'd be (${esc(s.alibiRoom)}). That alibi is broken.`);
    } else if (what === "accuse") {
      S.tries--;
      if (i === S.culprit) return finish(true);
      S.out.add(i);
      li.classList.remove("shake"); void li.offsetWidth; li.classList.add("shake");
      if (S.tries === 0) return finish(false);
      say(`Not ${esc(s.name)}. The Haunter is getting braver. One accusation left.`);
    }
    refresh();
  }

  function finish(won) {
    S.over = true;
    const c = S.c, s = c.suspects[S.culprit];
    const line = `${s.name} wore ${maskName(S.legend)} ${s.motive}.`;
    const li = $(`.suspect[data-i="${S.culprit}"]`, file);
    li.classList.add("unmasked");
    $("[data-reveal]", li).textContent = line;
    if (won) { solved.add(c.id); saveSolved(); paintCaseBook(); }
    $("[data-verdict-title]", file).textContent = won ? "Case closed." : "The Haunter got away.";
    $("[data-verdict-body]", file).textContent = won ? `${line} ${c.recovered}` : `It was ${line}`;
    const v = $("[data-verdict]", file);
    v.hidden = false;
    say("");
    refresh();
    Swing.push(li, 50);
    $$(".case-tab", tabsEl)[current].classList.toggle("solved", solved.has(c.id));
    v.focus({ preventScroll: true });
    v.scrollIntoView({ block: "nearest", behavior: still() ? "auto" : "smooth" });
  }

  file.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.matches("[data-search]")) search();
    else if (b.matches("[data-restart], [data-again]")) start(S.c);
    else if (b.matches("[data-next]")) select((current + 1) % order.length, true);
    else if (b.matches("[data-retry]")) init();
    else if (b.dataset.act) act(+b.closest(".suspect").dataset.i, b.dataset.act);
  });
  brushable($("[data-board]", file), ".suspect");
  new ResizeObserver(() => { if (S) drawStrings(false); }).observe($("[data-board]", file));

  /* ---------------- Houses, legends, progress ---------------- */
  function renderHouses() {
    const tilt = [-1.2, 0.9, -0.6, 1.4, -1];
    $("[data-houses]").innerHTML = game.houses.map((h, i) => {
      const cases = game.cases.filter((c) => c.house === h.id).map((c) => c.name);
      return `<li class="photo">
        <div class="print" style="--r:${tilt[i % tilt.length]}deg"><img src="img/${esc(h.id)}.jpg" width="960" height="465" loading="lazy" decoding="async" alt="${esc(h.name)} at night, rendered from the game's level files"></div>
        <h3>${esc(h.name)}</h3>
        <p class="where">${esc(h.street || "")}${h.size ? ` · ${esc(h.size)}` : ""}${h.floors ? `, ${h.floors} ${h.floors === 1 ? "floor" : "floors"}` : ""}</p>
        ${h.blurb ? `<p>${esc(h.blurb)}</p>` : ""}
        <p class="calls">Cases here: <b>${esc(listNames(cases))}</b></p>
      </li>`;
    }).join("");
  }

  // Atkinson's zero is slashed for legibility, which reads oddly in years: set numbers in Fraunces.
  const nums = (html) => html.replace(/\d[\d.,]*/g, (m) => `<span class="num">${m}</span>`);

  function renderLegends() {
    const tilt = [-2, 1.5, -1, 2.2];
    $("[data-legends]").innerHTML = game.legends.map((l, i) => `<li>
      <div class="print mug" style="--r:${tilt[i % tilt.length]}deg"><span class="pin"></span><img src="img/legend-${esc(l.id)}.jpg" width="450" height="480" loading="lazy" decoding="async" alt="${esc(l.name)} costume, rendered from the game's costume files"></div>
      <div class="legend-text">
      <h3>${esc(l.name)}</h3>
      <p class="origin">${nums(esc(l.origin))}</p>
      <p>${esc(l.legend)}</p>
      <p class="power">${esc(l.power)}: <span>${esc(l.powerBlurb)}</span></p>
      </div>
    </li>`).join("");
  }

  function renderProgress() {
    const ms = game.milestones;
    const done = ms.reduce((a, m) => a + m.done, 0), total = ms.reduce((a, m) => a + m.total, 0);
    const pct = Math.round((done / total) * 100);
    const list = $("[data-milestones]");
    list.innerHTML = ms.map((m, i) => `<li class="${m.done === m.total ? "done" : ""}">
      <span class="m-name">${esc(m.name.replace(/^Milestone \d+:\s*/, ""))}</span>
      <span class="m-count">${m.done} of ${m.total}</span>
      <span class="bar" role="img" aria-label="${m.done} of ${m.total} tasks done"><i style="--f:${(m.done / m.total).toFixed(3)};--d:${Math.min(i, 12) * 40}ms"></i></span>
    </li>`).join("");
    $("[data-total-sub]").textContent = `of planned tasks done (${done} of ${total})`;
    const num = $("[data-total]");
    const count = () => {
      if (still()) { num.textContent = pct + "%"; return; }
      const t0 = performance.now();
      const step = (now) => {
        const k = Math.min(1, (now - t0) / 900), e = 1 - Math.pow(1 - k, 4);
        num.textContent = Math.round(pct * e) + "%";
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    num.textContent = pct + "%";
    const io = new IntersectionObserver((es) => {
      if (es.some((e) => e.isIntersecting)) { list.classList.add("seen"); count(); io.disconnect(); }
    }, { threshold: 0.2 });
    io.observe(list);

    const rounds = game.rounds.map((r, i) => ({ ...r, n: i + 1 })).reverse();
    const ol = $("[data-rounds]");
    const draw = (all) => {
      const shown = all ? rounds : rounds.slice(0, 6);
      ol.innerHTML = shown.map((r) => `<li value="${r.n}"><b>Round ${r.n}: ${esc(r.title)}</b><span>${esc(r.line)}</span></li>`).join("") +
        (all ? "" : `<li class="rounds-more"><button class="link-btn" type="button" data-all>Show all ${rounds.length} rounds</button></li>`);
      const more = $("[data-all]", ol);
      if (more) more.addEventListener("click", () => { draw(true); $$("li", ol)[6].querySelector("b").setAttribute("tabindex", "-1"); $$("li", ol)[6].querySelector("b").focus(); });
    };
    draw(false);
  }

  /* ---------------- Copy buttons ---------------- */
  $$("[data-copy]").forEach((btn) => btn.addEventListener("click", async () => {
    const code = btn.parentElement.querySelector("code");
    try {
      await navigator.clipboard.writeText(code.textContent);
      btn.textContent = "Copied";
    } catch (e) {
      getSelection().selectAllChildren(code);
      btn.textContent = "Press Ctrl+C";
    }
    clearTimeout(btn._t);
    btn._t = setTimeout(() => { btn.textContent = "Copy"; }, 1800);
  }));

  /* ---------------- Start ---------------- */
  async function init() {
    show("loading");
    try {
      game = await load();
      const difficulty = Object.fromEntries(game.houses.map((h) => [h.id, h.difficulty ?? 9]));
      order = [...game.cases].sort((a, b) => a.visit - b.visit || difficulty[a.house] - difficulty[b.house]);
      buildTabs();
      show("ready");
      select(0);
      renderHouses();
      renderLegends();
      renderProgress();
    } catch (err) {
      const onDisk = location.protocol === "file:";
      $("[data-error-text]", file).innerHTML = onDisk
        ? "Browsers won't read the case files straight from your disk. Run <code>unmasked site</code> in a terminal and open the address it prints."
        : err.name === "AbortError" ? "It took too long to load. Check your connection and try again."
        : `The cases didn't load. ${esc(err.message || "")} Try again in a moment.`;
      show("error");
      const later = "<li class=\"later\">This part loads with the case files.</li>";
      ["[data-houses]", "[data-legends]", "[data-milestones]"].forEach((sel) => { $(sel).innerHTML = later; });
    }
  }
  init();
})();
