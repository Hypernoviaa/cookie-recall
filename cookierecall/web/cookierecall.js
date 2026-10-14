/* Cookie Recall — front-end for Anki's webviews.
 *
 * One script, three modes chosen by the Python side through window.COOKIERECALL_BOOT:
 *   "bakery"  full shop on the deck list (home screen)
 *   "hud"     small overlay on the review screen
 *   "mini"    one-line strip on the deck overview / congrats screen
 *
 * Everything lives in a CLOSED shadow root: user card templates cannot style or
 * script it, and our CSS cannot touch their cards. Python is the single source
 * of truth; the UI only renders snapshots and sends intents through pycmd().
 */
(function () {
  "use strict";
  if (window.__cookierecallLoaded) return;
  window.__cookierecallLoaded = true;
  // Anki puts add-on scripts at the top of <body>: wait for the page content.
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", main, { once: true });
  else main();

  function main() {

  const BOOT = window.COOKIERECALL_BOOT || {};
  const BASE = BOOT.base || "";
  const IMG = (n) => `${BASE}/img/${n}.svg`;
  const MODE = BOOT.mode || "hud";
  let S = BOOT.snap || null; // latest snapshot from Python
  let CFG = BOOT.cfg || {};
  const RM = () => !!CFG.reduced_motion || matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------------------------------------------------------------- utils
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // ---------------------------------------------------------------- i18n
  const LANG = BOOT.lang === "fr" ? "fr" : "en";
  const ALL = window.COOKIERECALL_STRINGS || {};
  const STR = ALL[LANG] || ALL.fr || {};
  const t = (key, vars) => String(STR[key] ?? (ALL.fr || {})[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => (vars && k in vars ? vars[k] : ""));
  const isOne = (n) => (LANG === "fr" ? Math.abs(n) < 2 : Math.abs(n) === 1);
  const FR = LANG === "fr";
  const LOCALE = FR ? "fr-FR" : "en-US";
  const DEC = FR ? "," : ".";
  const NAMES = FR ? ["M", "Md", "Bn", "Bd", "Tn", "Td", "Qn", "Qd", "Qt", "Qtd", "Sx", "Sxd"] : ["M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc", "Ud", "Dd"];
  const LONG = FR
    ? ["million", "milliard", "billion", "billiard", "trillion", "trilliard", "quadrillion", "quadrilliard", "quintillion", "quintilliard", "sextillion", "sextilliard"]
    : ["million", "billion", "trillion", "quadrillion", "quintillion", "sextillion", "septillion", "octillion", "nonillion", "decillion", "undecillion", "duodecillion"];
  function fmt(x, long) {
    x = Number(x) || 0;
    if (x < 0) return "-" + fmt(-x, long);
    if (x < 10 && x !== Math.floor(x)) return x.toFixed(1).replace(/\.0$/, "").replace(".", DEC);
    if (x < 1e6) return Math.floor(x).toLocaleString(LOCALE).replace(/\s/g, " ");
    const e = Math.floor(Math.log10(x) / 3) - 2;
    if (e >= NAMES.length) return x.toExponential(2).replace(".", DEC);
    const v = x / Math.pow(10, (e + 2) * 3);
    const s = (v < 100 ? v.toPrecision(3) : v.toFixed(0)).replace(".", DEC);
    if (!long) return FR ? `${s} ${NAMES[e]}` : `${s}${NAMES[e]}`;
    return `${s} ${LONG[e]}${FR && v >= 2 ? "s" : ""}`;
  }
  const mult = (m) => "×" + (Math.round(m * 100) / 100).toLocaleString(LOCALE);
  const pct = (p) => Math.round(p * 100);
  // "3 jours" / "3 days": key is the base of a _one/_many pair in strings.js
  const pl = (n, key) => `${fmt(n)} ${t(key + (isOne(n) ? "_one" : "_many"))}`;
  const plt = (n, key) => t(key + (isOne(n) ? "_one" : "_many"), { n: fmt(n) });

  function send(action, data) {
    return new Promise((resolve) => {
      if (typeof window.pycmd !== "function") return resolve({ ok: false });
      try {
        window.pycmd("cookierecall:" + JSON.stringify(Object.assign({ a: action }, data || {})), (r) => {
          try { resolve(typeof r === "string" ? JSON.parse(r) : r || { ok: false }); } catch (e) { resolve({ ok: false }); }
        });
      } catch (e) { resolve({ ok: false }); }
    });
  }

  // ---------------------------------------------------------------- sound
  let actx = null;
  function tone(freqs, dur, type, vol, gap) {
    if (!CFG.sound) return;
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      const v = (CFG.volume ?? 0.4) * (vol ?? 0.25);
      freqs.forEach((f, i) => {
        const t0 = actx.currentTime + i * (gap ?? 0.07);
        const o = actx.createOscillator(), g = actx.createGain();
        o.type = type || "sine";
        o.frequency.setValueAtTime(f, t0);
        o.frequency.exponentialRampToValueAtTime(f * 1.25, t0 + dur);
        g.gain.setValueAtTime(0.0001, t0);
        g.gain.exponentialRampToValueAtTime(v, t0 + 0.012);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
        o.connect(g).connect(actx.destination);
        o.start(t0); o.stop(t0 + dur + 0.02);
      });
    } catch (e) { /* audio is a nicety */ }
  }
  const SFX = {
    pop: () => tone([620], 0.09, "sine", 0.18),
    combo: (n) => tone([520 + Math.min(n, 60) * 9], 0.08, "triangle", 0.16),
    buy: () => tone([440, 660], 0.09, "triangle", 0.22, 0.06),
    golden: () => tone([880, 1175, 1568], 0.16, "sine", 0.22, 0.06),
    win: () => tone([523, 659, 784, 1046], 0.22, "triangle", 0.25, 0.1),
    no: () => tone([220], 0.12, "square", 0.08),
  };

  // ---------------------------------------------------------------- shadow host
  (function injectFont() {
    if (document.getElementById("cookierecall-font")) return;
    const st = document.createElement("style");
    st.id = "cookierecall-font";
    st.textContent = `@font-face{font-family:"CookieRecallFredoka";src:url("${BASE}/fonts/fredoka-latin-wght-normal.woff2") format("woff2");font-weight:300 700;font-display:swap;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"CookieRecallFredoka";src:url("${BASE}/fonts/fredoka-latin-ext-wght-normal.woff2") format("woff2");font-weight:300 700;font-display:swap;unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}`;
    document.head.appendChild(st);
  })();

  let host = document.getElementById("cookierecall-root");
  if (!host) {
    host = document.createElement("div");
    host.id = "cookierecall-root";
    document.body.appendChild(host);
  }
  function applyPalette(vars) {
    Object.entries(vars || {}).forEach(([k, v]) => host.style.setProperty(k, v));
  }
  applyPalette(CFG.palette_vars);
  const root = host.attachShadow({ mode: "closed" });
  root.innerHTML = `<link rel="stylesheet" href="${BASE}/cookierecall.css"><div id="app"></div><div class="tip" role="tooltip"></div><div class="toasts" aria-live="polite"></div>`;
  const app = root.getElementById("app");
  const tipEl = root.querySelector(".tip");
  let toastBox = root.querySelector(".toasts");
  const $ = (sel) => root.querySelector(sel);

  // ---------------------------------------------------------------- tooltip
  root.addEventListener("mouseover", (e) => {
    const t = e.target.closest && e.target.closest("[data-tip]");
    if (!t) return tipEl.classList.remove("on");
    tipEl.innerHTML = t.getAttribute("data-tip");
    tipEl.classList.add("on");
    const r = t.getBoundingClientRect(), tw = tipEl.offsetWidth, th = tipEl.offsetHeight;
    let x = Math.min(Math.max(8, r.left + r.width / 2 - tw / 2), innerWidth - tw - 8);
    let y = r.top - th - 10;
    if (y < 8) y = r.bottom + 10;
    tipEl.style.left = x + "px";
    tipEl.style.top = y + "px";
  });
  root.addEventListener("mouseout", (e) => {
    if (!e.relatedTarget || !(e.relatedTarget.closest && e.relatedTarget.closest("[data-tip]"))) tipEl.classList.remove("on");
  });
  addEventListener("scroll", () => tipEl.classList.remove("on"), { passive: true });

  // ---------------------------------------------------------------- toasts & fx
  function toast(icon, title, body, kind, ms) {
    if (!toastBox) return;
    const el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.innerHTML = `<img src="${IMG(icon)}" alt=""><div><b>${esc(title)}</b>${body || ""}</div>`;
    toastBox.appendChild(el);
    while (toastBox.children.length > 4) toastBox.firstChild.remove();
    setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 400); }, ms || 4200);
  }

  function floatText(x, y, text, cls) {
    const el = document.createElement("div");
    el.className = "plus " + (cls || "");
    el.textContent = text;
    el.style.left = x + "px";
    el.style.top = y + "px";
    root.appendChild(el);
    setTimeout(() => el.remove(), 1200);
  }

  function crumbs(x, y, n) {
    if (RM()) return;
    for (let i = 0; i < n; i++) {
      const c = document.createElement("i");
      c.className = "crumb" + (i % 3 === 0 ? " choc" : "");
      const a = Math.random() * Math.PI * 2, d = 26 + Math.random() * 46;
      c.style.left = x + "px";
      c.style.top = y + "px";
      c.style.setProperty("--dx", Math.cos(a) * d + "px");
      c.style.setProperty("--dy", Math.sin(a) * d + 18 + "px");
      root.appendChild(c);
      setTimeout(() => c.remove(), 900);
    }
  }

  function rain(n, icon) {
    if (RM()) return;
    const box = document.createElement("div");
    box.className = "rain";
    for (let i = 0; i < n; i++) {
      const im = document.createElement("img");
      im.src = IMG(icon || "cookie");
      im.style.left = Math.random() * 100 + "vw";
      im.style.animationDuration = 1.6 + Math.random() * 1.6 + "s";
      im.style.animationDelay = Math.random() * 0.8 + "s";
      im.style.setProperty("--rot", (Math.random() * 720 - 360).toFixed(0) + "deg");
      const s = 28 + Math.random() * 28;
      im.style.width = im.style.height = s + "px";
      box.appendChild(im);
    }
    root.appendChild(box);
    setTimeout(() => box.remove(), 4000);
  }

  function celebrate(icon, title, gainText, body, cookieIcon) {
    const wrap = document.createElement("div");
    wrap.className = "celebrate";
    wrap.innerHTML = `<div class="card" role="dialog" aria-label="${esc(title)}"><img src="${IMG(icon)}" alt=""><h2>${esc(title)}</h2>
      ${gainText ? `<div class="gain">${esc(gainText)}</div>` : ""}<p>${body || ""}</p><button class="btn">${t("nice")}</button></div>`;
    root.appendChild(wrap);
    rain(26, cookieIcon || "cookie");
    SFX.win();
    const close = () => wrap.remove();
    wrap.querySelector("button").addEventListener("click", close);
    wrap.querySelector("button").focus({ preventScroll: true });
    setTimeout(close, 7000);
  }

  // number count-up
  const tweens = new WeakMap();
  function countTo(el, from, to, ms) {
    if (!el) return;
    if (RM() || from === to) { el.textContent = fmt(to); return; }
    const t0 = performance.now();
    const id = {};
    tweens.set(el, id);
    (function step(t) {
      if (tweens.get(el) !== id) return;
      const k = Math.min(1, (t - t0) / (ms || 650));
      const e = 1 - Math.pow(1 - k, 3);
      el.textContent = fmt(from + (to - from) * e);
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }

  // ---------------------------------------------------------------- events from Python
  function handleEvents(events, opts) {
    (events || []).forEach((e) => {
      switch (e.type) {
        case "achievement":
          toast(e.icon, t("ach_title", { name: e.name }), `${esc(e.desc)}<br><span class="g">${t("ach_bonus")}</span>`);
          SFX.golden();
          break;
        case "quest":
          toast("a_scroll", t("quest_done"), `${esc(e.text)} <span class="g">+${fmt(e.gain)}</span>`);
          SFX.buy();
          break;
        case "golden_spawn":
          if (MODE === "hud") spawnGolden(e.token, e.life);
          break;
        case "frenzy_end":
          toast("golden", t("frenzy_end_t"), t("frenzy_end_b"), "soft", 2600);
          break;
        case "jackpot":
          celebrate("a_check", t("jackpot_t"), "+" + fmt(e.gain, true) + " " + t("cookies"),
            t("jackpot_b", { reviews: pl(e.reviews, "review"), streak: pl(e.streak, "day") }));
          break;
        case "freeze_used":
          toast("a_freeze", t("freeze_used_t"), t("freeze_used_b", { n: pl(e.count, "missed") }), "", 6000);
          break;
        case "streak_lost":
          toast("a_calendar", t("streak_lost_t"), t("streak_lost_b", { n: pl(e.count, "day") }), "bad", 7000);
          break;
        case "graduated":
          celebrate("a_diploma", t("grad_t"), "+" + pl(e.diplomas, "diploma"), t("grad_b"), "golden");
          break;
      }
    });
  }

  // =================================================================== HUD
  let golden = null;
  function spawnGolden(token, life) {
    if (golden && golden._tok === token) return;
    if (golden) golden.remove();
    const b = document.createElement("button");
    b.className = "golden";
    b.setAttribute("aria-label", t("golden_aria"));
    b.innerHTML = `<img src="${IMG("golden")}" alt="">`;
    // keep it in the outer band of the screen so it never covers the card text
    const pos = CFG.hud_position || "top-right";
    const right = pos.endsWith("right"), top = pos.startsWith("top");
    // between the HUD column (about 300 px wide) and the centre of the card
    const span = Math.max(40, Math.min(200, innerWidth * 0.18));
    const x = right ? innerWidth - 330 - 70 - Math.random() * span : 330 + Math.random() * span;
    const y = top ? 70 + Math.random() * 150 : innerHeight - 140 - Math.random() * 150;
    b.style.left = Math.max(8, x) + "px";
    b.style.top = Math.max(8, y) + "px";
    b._tok = token;
    root.appendChild(b);
    golden = b;
    SFX.golden();
    const fadeAt = setTimeout(() => b.classList.add("fading"), Math.max(0, (life - 2.5) * 1000));
    const gone = setTimeout(() => { if (golden === b) golden = null; b.remove(); }, life * 1000);
    b.addEventListener("click", async () => {
      clearTimeout(fadeAt); clearTimeout(gone);
      const r = b.getBoundingClientRect();
      b.remove(); golden = null;
      const res = await send("golden", { token });
      if (!res.ok) return;
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      crumbs(cx, cy, 22);
      if (res.kind === "lucky") { floatText(cx, cy, t("lucky") + " +" + fmt(res.gain), "big"); toast("golden", t("lucky"), `<span class="g">+${fmt(res.gain)} ${t("cookies")}</span>`, "", 3000); }
      else if (res.kind === "frenzy") { floatText(cx, cy, `${t("frenzy")} ×${res.mult}`, "big"); toast("golden", t("frenzy"), t("frenzy_b", { n: res.reviews, m: res.mult }), "", 4000); }
      else { floatText(cx, cy, t("rain") + " +" + fmt(res.gain), "big"); rain(30, "cookie"); }
      SFX.win();
      if (res.snap) updateHud(res.snap, false);
      handleEvents(res.events);
    });
  }

  let hudBuilt = false, ringRAF = 0;
  function buildHud() {
    const pos = CFG.hud_position || "top-right";
    app.innerHTML = `<div class="hud ${esc(pos)}${RM() ? " calm" : ""}">
      <div class="pill${CFG.hud_tiny ? " tiny" : ""}" data-tip="${esc(t("hud_tip"))}">
        <div class="ico"><svg viewBox="0 0 46 46" width="46" height="46"><circle class="track" cx="23" cy="23" r="20"/><circle class="ring" cx="23" cy="23" r="20" stroke-dasharray="125.7" stroke-dashoffset="125.7"/></svg><img src="${IMG("cookie")}" alt=""></div>
        <div class="txt"><div class="cnt num">0</div><div class="sub"><span class="per">+0</span> ${t("per_review")}</div></div>
      </div>
      <div class="tag combo" hidden></div>
      <div class="tag fz" hidden></div>
      <div class="tag warn" hidden></div>
      <div class="hgoal" hidden><div class="l"><b class="gn"></b><span class="gr"></span></div><div class="bar"><i></i></div></div>
      <div class="toasts"></div>
    </div>`;
    toastBox = app.querySelector(".toasts");
    app.querySelector(".pill").addEventListener("click", () => {
      CFG.hud_tiny = !CFG.hud_tiny;
      app.querySelector(".pill").classList.toggle("tiny", CFG.hud_tiny);
      send("setting", { key: "hud_tiny", value: CFG.hud_tiny });
    });
    hudBuilt = true;
  }

  let comboDeadline = 0, comboWindow = 120;
  function ringLoop() {
    cancelAnimationFrame(ringRAF);
    const ring = app.querySelector(".ring");
    if (!ring) return;
    const step = () => {
      const left = Math.max(0, comboDeadline - performance.now() / 1000);
      ring.style.strokeDashoffset = String(125.7 * (1 - left / comboWindow));
      if (left <= 0) {
        const c = app.querySelector(".combo");
        if (c) c.hidden = true;
        return;
      }
      ringRAF = requestAnimationFrame(step);
    };
    step();
  }

  function updateHud(snap, animate) {
    const prev = S;
    S = snap;
    if (!hudBuilt) buildHud();
    const hud = app.querySelector(".hud");
    const cnt = app.querySelector(".cnt");
    countTo(cnt, prev && animate ? prev.cookies : snap.cookies, snap.cookies, 700);
    app.querySelector(".per").textContent = "+" + fmt(snap.per_review);
    // combo
    const c = app.querySelector(".combo");
    comboWindow = snap.combo.window || 120;
    comboDeadline = performance.now() / 1000 + (snap.combo.remaining || 0);
    if (snap.combo.count >= 2) {
      c.hidden = false;
      const capped = snap.combo.count >= snap.combo.cap;
      c.innerHTML = `Combo <b>${snap.combo.count}</b> · ${mult(snap.combo.mult)}${capped ? " · max" : ""}`;
      c.setAttribute("data-tip", t("combo_tip", { min: Math.round(comboWindow / 60), step: Math.round(snap.combo.step * 100), cap: snap.combo.cap }));
    } else c.hidden = true;
    ringLoop();
    // frenzy
    const fz = app.querySelector(".fz");
    if (snap.frenzy.left > 0) { fz.hidden = false; fz.textContent = t("frenzy_tag", { m: snap.frenzy.mult, n: snap.frenzy.left }); hud.classList.add("frenzy"); }
    else { fz.hidden = true; hud.classList.remove("frenzy"); }
    // goal
    const g = app.querySelector(".hgoal");
    if (snap.goal && CFG.hud_goal !== false) {
      g.hidden = false;
      g.classList.toggle("ready", snap.goal.progress >= 1);
      app.querySelector(".gn").textContent = snap.goal.name;
      app.querySelector(".gr").textContent = snap.goal.progress >= 1 ? t("ready") : t("to_go", { n: pl(snap.goal.reviews, "review") });
      app.querySelector(".hgoal .bar > i").style.width = pct(snap.goal.progress) + "%";
      g.setAttribute("data-tip", t("goal_tip", { name: esc(snap.goal.name), cost: fmt(snap.goal.cost) }));
    } else g.hidden = true;
    // golden cookie still alive after a page reload / gone on the Python side
    if (snap.golden && !golden && snap.golden.remaining > 1.5) spawnGolden(snap.golden.token, snap.golden.remaining);
    else if (!snap.golden && golden && animate) { golden.remove(); golden = null; }
  }

  const WARN = { too_fast: t("warn_too_fast"), repeat: t("warn_repeat"), new_cap: t("warn_new_cap"), preview: t("warn_preview") };
  let warnTimer = 0;
  function hudReward(p) {
    updateHud(p.snap, true);
    const pill = app.querySelector(".pill");
    pill.classList.remove("bump"); void pill.offsetWidth; pill.classList.add("bump");
    const r = app.querySelector(".ico").getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    // "+N" springs out beside the pill, on the side facing the card, away from the tags
    const onRight = (CFG.hud_position || "top-right").endsWith("right");
    const pr = app.querySelector(".pill").getBoundingClientRect();
    floatText(onRight ? pr.left - 34 : pr.right + 34, cy, "+" + fmt(p.gain), p.factor < 0.6 ? "dim" : p.snap.frenzy.left > 0 ? "big" : "");
    if (p.factor >= 0.6) crumbs(cx, cy, 7 + Math.min(10, Math.floor((p.combo || 0) / 10)));
    if (p.combo >= 2) SFX.combo(p.combo); else SFX.pop();
    const w = app.querySelector(".warn");
    if (p.reason && WARN[p.reason] && p.factor < 0.6) {
      w.hidden = false; w.textContent = WARN[p.reason];
      clearTimeout(warnTimer); warnTimer = setTimeout(() => (w.hidden = true), 2600);
    }
    handleEvents(p.events);
  }

  // =================================================================== MINI
  function renderMini() {
    if (!S) return;
    const d = S.day;
    const sub = d.cleared ? t("mini_cleared", { n: pl(S.streak.count, "day") }) : t("mini_sub", { per: fmt(S.per_review_base), today: fmt(d.baked) });
    app.innerHTML = `<div class="mini"><img src="${IMG("cookie")}" alt=""><div class="grow"><div class="cnt num">${fmt(S.cookies)} ${t("cookies")}</div><div class="sub">${esc(sub)}</div></div>
      <button class="btn" data-go>${t("bakery")}</button></div>`;
    app.querySelector("[data-go]").addEventListener("click", () => send("open_bakery"));
  }

  // =================================================================== BAKERY
  let tab = "shop", qty = 1, confirmOpen = false;
  try { tab = sessionStorage.getItem("cookierecall-tab") || "shop"; qty = Number(sessionStorage.getItem("cookierecall-qty")) || 1; } catch (e) { /* storage may be unavailable */ }
  const TIER = ["#a5714e", "#c9c9d4", "#f5c542", "#8dbf6a", "#7fc8e8", "#b48cff", "#e2475b", "#ffffff"];

  function chip(icon, label, value, tip) {
    return `<span class="chip" data-tip="${esc(tip)}"><img src="${IMG(icon)}" alt="">${label} <b>${value}</b></span>`;
  }

  function renderHero() {
    const m = S.mult;
    const mamies = (S.buildings.find((b) => b.id === "mamie") || {}).owned || 0;
    const orbitN = Math.min(mamies, 18);
    let orbit = "";
    for (let i = 0; i < orbitN; i++) {
      const a = (i / Math.max(orbitN, 1)) * 360;
      orbit += `<img src="${IMG("b_mamie")}" alt="" style="transform: rotate(${a}deg) translate(105px) rotate(${-a}deg)">`;
    }
    const goal = S.goal;
    const chips = [
      chip("a_calendar", t("chip_streak"), `${pl(S.streak.count, "day")} ${mult(m.streak)}`,
        t("chip_streak_tip", { step: Math.round(S.streak.step * 100), max: S.streak.max_days, best: pl(S.streak.best, "day") })),
      chip("a_sapling", t("chip_savoir"), `${t("chip_savoir_val", { n: fmt(S.mature) })} ${mult(m.savoir)}`, t("chip_savoir_tip")),
      chip("a_star", t("chip_ach"), `${S.achievements_count} ${mult(m.achievements)}`, t("chip_ach_tip")),
    ];
    if (S.prestige.diplomas > 0) chips.push(chip("a_diploma", t("chip_dip"), `${S.prestige.diplomas} ${mult(m.diplomas)}`, t("chip_dip_tip")));
    if (m.upgrades > 1) chips.push(chip("u_brain", t("chip_method"), mult(m.upgrades), t("chip_method_tip")));
    return `<section class="hero">
      <div class="stage" aria-hidden="true"><div class="glow"></div><div class="plate"></div><div class="orbit">${orbit}</div><img class="big-cookie" src="${IMG(S.frenzy.left > 0 ? "golden" : "cookie")}" alt=""></div>
      <div class="numbers">
        <div class="count num" id="count">${fmt(S.cookies)}</div>
        <div class="unit">${t("unit_line", { n: fmt(S.baked_run) })}</div>
        <div class="rate">${t("rate", { n: fmt(S.per_review_base) })}</div>
        <div class="chips">${chips.join("")}</div>
        ${goal ? `<div class="goal"><div class="goal-top"><span>${t("next_buy", { name: esc(goal.name) })}</span><span>${goal.progress >= 1 ? t("available") : t("to_go", { n: pl(goal.reviews, "review") })}</span></div><div class="bar"><i style="width:${pct(goal.progress)}%"></i></div></div>` : ""}
      </div></section>`;
  }

  function renderToday() {
    const d = S.day, st = S.streak;
    const oven = d.cleared
      ? `<div class="oven done"><img src="${IMG("a_check")}" alt=""><div><h3>${t("oven_done_h")}</h3><p>${t("oven_done_p", { n: pl(st.count, "day") })}</p></div></div>`
      : `<div class="oven"><img src="${IMG("b_four")}" alt=""><div><h3>${t("oven_h")}</h3><p>${t("oven_p", { n: fmt(d.jackpot_preview) })}</p>
         <div class="freezes">${st.freezes > 0 ? plt(st.freezes, "freezes") : t("freezes_none")}</div></div></div>`;
    const tickets = d.quests.map((q, i) => {
      const r = [-1.5, 1, -0.6][i] || 0;
      return `<div class="ticket ${q.done ? "done" : ""}" style="--r:${r}deg">${q.done ? `<span class="stamp">${t("stamp")}</span>` : ""}
        <div class="t">${esc(q.text)}</div><div class="bar"><i style="width:${pct(q.progress / q.n)}%"></i></div>
        <div class="p"><span>${fmt(q.progress)} / ${fmt(q.n)}</span><span>≈ ${fmt(q.reward * S.per_review_base)} ${t("cookies")}</span></div></div>`;
    }).join("");
    return `<section class="today">${oven}<div><div class="tickets">${tickets}</div></div></section>`;
  }

  function renderTabs() {
    const affordable = S.upgrades.some((u) => u.cost <= S.cookies) || S.buildings.some((b) => !b.locked && b.cost1 <= S.cookies);
    const perkDot = S.perks.some((p) => !p.owned && p.available && p.cost <= S.prestige.available) || S.prestige.pending > 0;
    const tb = (id, label, extra) => `<button class="tab" role="tab" aria-selected="${tab === id}" data-tab="${id}">${label}${extra || ""}</button>`;
    return `<nav class="tabs" role="tablist">
      ${tb("shop", t("tab_shop"), affordable ? `<span class="dot" title="${esc(t("can_buy"))}"></span>` : "")}
      ${tb("ach", t("tab_ach"), `<span class="n">${S.achievements_count}/${S.achievements.length}</span>`)}
      ${tb("dip", t("tab_dip"), perkDot ? '<span class="dot"></span>' : "")}
      ${tb("stats", t("tab_stats"))}</nav>`;
  }

  function upgradeTip(u) {
    const can = u.cost <= S.cookies;
    return `<b>${esc(u.name)}</b>${esc(u.desc)}<div class="c ${can ? "" : "no"}">${fmt(u.cost)} ${t("cookies")}${can ? "" : t("missing", { n: fmt(u.cost - S.cookies) })}</div>`;
  }

  function costOf(b) {
    if (qty === "max") return b.max > 0 ? null : b.cost1;
    return qty === 10 ? b.cost10 : qty === 100 ? b.cost100 : b.cost1;
  }

  function renderShop() {
    const owned = S.buildings.filter((b) => b.owned > 0);
    const shelves = owned.length
      ? owned.map((b) => {
          const n = Math.min(b.owned, 24);
          let imgs = "";
          for (let i = 0; i < n; i++) imgs += `<img src="${IMG("b_" + b.id)}" alt="">`;
          return `<div class="shelf" data-shelf="${b.id}" data-tip="<b>${esc(b.plural)} : ${fmt(b.owned)}</b>${esc(b.desc)}<div class='c'>${t("shelf_tip", { each: fmt(b.each), share: pct(b.share) })}</div>">
            <div class="label"><b>${fmt(b.owned)}</b>${esc(b.owned > 1 ? b.plural : b.name)}</div>
            <div class="items">${imgs}</div>${b.owned > n ? `<span class="more">+${fmt(b.owned - n)}</span>` : ""}</div>`;
        }).join("")
      : `<div class="empty">${t("empty_shelf")}</div>`;

    const ups = S.upgrades.length
      ? `<div class="ugrid">${S.upgrades.map((u) => `<button class="upg ${u.cost <= S.cookies ? "can" : "poor"}" style="--tier:${TIER[u.tier] || TIER[0]}" data-buy-upgrade="${u.id}" data-tip="${esc(upgradeTip(u))}" aria-label="${esc(u.name)}"><img src="${IMG(u.icon)}" alt=""></button>`).join("")}</div>`
      : "";

    const blist = S.buildings.map((b) => {
      if (b.locked) {
        return `<div class="bld locked" data-tip="<b>???</b>${esc(b.desc)}"><img src="${IMG("b_" + b.id)}" alt=""><div><div class="nm">???</div><div class="pr"><img src="${IMG("cookie")}" alt="">${fmt(b.cost1)}</div></div><div class="own"></div></div>`;
      }
      const c = costOf(b);
      const can = qty === "max" ? b.max > 0 : c <= S.cookies;
      const label = qty === "max" ? (b.max > 0 ? `×${b.max} · ${fmt(maxCost(b))}` : fmt(b.cost1)) : fmt(c);
      return `<button class="bld ${can ? "can" : "poor"}" data-buy="${b.id}" data-tip="<b>${esc(b.name)}</b>${esc(b.desc)}<div class='c'>${t("bld_tip", { n: fmt(b.each) })}</div>">
        <img src="${IMG("b_" + b.id)}" alt=""><div><div class="nm">${esc(b.name)}</div><div class="pr"><img src="${IMG("cookie")}" alt="">${label}</div></div><div class="own num">${b.owned || ""}</div></button>`;
    }).join("");

    const st = S.streak;
    const freezeCan = st.freezes < st.cap && st.freeze_cost <= S.cookies;
    const freeze = `<div class="special"><div class="col-title">${t("for_streak")}</div>
      <button class="bld ${freezeCan ? "can" : "poor"}" data-freeze ${st.freezes >= st.cap ? "disabled" : ""} data-tip="${esc(t("freeze_tip", { cap: st.cap }))}">
        <img src="${IMG("u_freeze")}" alt=""><div><div class="nm">${t("freeze_name")}</div><div class="pr"><img src="${IMG("cookie")}" alt="">${st.freezes >= st.cap ? t("stock_full") : fmt(st.freeze_cost)}</div></div><div class="own num">${st.freezes}/${st.cap}</div></button></div>`;

    const q = (v, l) => `<button aria-pressed="${qty === v}" data-qty="${v}">${l}</button>`;
    return `<div class="shop">
      <div><div class="col-title">${t("display")} <small>${t("buildings_n", { n: fmt(S.buildings.reduce((a, b) => a + b.owned, 0)) })}</small></div>${shelves}</div>
      <div>${ups ? `<div class="col-title">${t("upgrades")} <small>${t("available_n", { n: S.upgrades.length })}</small></div>${ups}` : ""}
        <div class="col-title">${t("buildings")} <span class="qty">${q(1, "×1")}${q(10, "×10")}${q(100, "×100")}${q("max", t("max"))}</span></div>
        <div class="blist">${blist}</div>${freeze}</div></div>`;
  }

  function maxCost(b) {
    // geometric sum for b.max units, same formula as the engine (display only)
    const r = 1.15;
    return b.cost1 * (Math.pow(r, b.max) - 1) / (r - 1);
  }

  function renderAch() {
    const owned = S.achievements.filter((a) => a.owned).length;
    const grid = S.achievements.map((a) => {
      if (!a.owned && a.name === "???") return `<div class="ach secret" data-tip="<b>???</b>${esc(a.desc)}">?</div>`;
      return `<div class="ach ${a.owned ? "" : "off"}" data-tip="<b>${esc(a.name)}</b>${esc(a.desc)}${a.owned ? `<div class='c'>${t("unlocked")}</div>` : ""}"><img src="${IMG(a.icon)}" alt="${esc(a.name)}"></div>`;
    }).join("");
    const ups = S.owned_upgrades.length
      ? `<div class="col-title" style="margin-top:22px">${t("bought_upgrades")} <small>${S.owned_upgrades.length}</small></div><div class="ugrid">${S.owned_upgrades.map((u) => `<div class="upg" style="--tier:${TIER[u.tier] || TIER[0]}" data-tip="<b>${esc(u.name)}</b>${esc(u.desc)}"><img src="${IMG(u.icon)}" alt=""></div>`).join("")}</div>`
      : "";
    return `<div class="ach-sum"><div><b>${owned} / ${S.achievements.length}</b>${t("ach_word")}</div><div><b>${mult(S.mult.achievements)}</b>${t("ach_bonus_label")}</div></div><div class="agrid">${grid}</div>${ups}`;
  }

  function renderDip() {
    const p = S.prestige;
    const ready = p.pending > 0;
    const perks = S.perks.map((k) => {
      const can = !k.owned && k.available && k.cost <= p.available;
      const cls = k.owned ? "owned" : !k.available ? "locked" : can ? "can" : "";
      return `<button class="perk ${cls}" data-perk="${k.id}" ${k.owned || !can ? 'aria-disabled="true"' : ""}><h4>${esc(k.name)}${k.owned ? `<span class="got">${t("owned_perk")}</span>` : `<span class="cost">${t("dipl_cost", { n: k.cost })}</span>`}</h4><p>${esc(k.desc)}${!k.available ? ` <em>${t("requires", { x: esc(k.requires) })}</em>` : ""}</p></button>`;
    }).join("");
    return `<div class="prestige">
      <div class="cap-card"><img src="${IMG("a_diploma")}" alt="">
        <div class="big num">${ready ? "+" + p.pending : p.diplomas}</div>
        <p>${ready ? plt(p.pending, "dip_pending") + t("dip_pending_b") : t("dip_have", { n: pl(p.diplomas, "diploma"), next: fmt(p.next_at, true), now: fmt(p.baked_total) })}</p>
        <button class="btn" data-graduate ${ready ? "" : "disabled"}>${t("grad_btn")}</button>
        <p>${t("dip_each", { n: p.available })}</p></div>
      <div><div class="col-title">${t("legacy")} <small>${t("legacy_sub")}</small></div><div class="perks">${perks}</div></div></div>`;
  }

  function renderStats() {
    const st = S.stats;
    const row = (k, v) => `<div class="stat"><span>${k}</span><b class="num">${v}</b></div>`;
    const tog = (key, label) => `<button class="toggle" data-setting="${key}" aria-pressed="${!!CFG[key]}"><i></i>${label}</button>`;
    return `<div class="stats">
      ${row(t("st_reviews_total"), fmt(st.reviews_total))}
      ${row(t("st_reviews_today"), fmt(S.day.reviews))}
      ${row(t("st_day_best"), fmt(st.day_reviews_best))}
      ${row(t("st_baked_today"), fmt(S.day.baked))}
      ${row(t("st_baked_run"), fmt(S.baked_run))}
      ${row(t("st_baked_total"), fmt(S.baked_total))}
      ${row(t("st_max_combo"), fmt(st.max_combo))}
      ${row(t("st_golden"), fmt(st.golden_clicked))}
      ${row(t("st_jackpots"), fmt(st.jackpots))}
      ${row(t("st_best_streak"), pl(S.streak.best, "day"))}
      ${row(t("st_quests"), fmt(st.quests_done))}
      ${row(t("st_mult"), mult(S.mult.total))}
    </div>
    <div class="settings" id="settings"><h3>${t("settings")}</h3>
      <div class="swatches"><span>${t("set_palette")}</span>${(CFG.palettes || []).map((p) => `<button class="sw" data-palette="${p.id}" aria-pressed="${(CFG.palette || "pistachio") === p.id}" title="${esc(p.name)}" aria-label="${esc(p.name)}"><i style="background:${p.board}"></i><i style="background:${p.accent}"></i></button>`).join("")}</div>
      ${tog("sound", t("set_sound"))}${tog("hud", t("set_hud"))}${tog("reduced_motion", t("set_motion"))}${tog("theme", t("set_theme"))}
      <button class="toggle" data-cycle-pos aria-pressed="true"><i></i>${t("set_pos", { x: t({ "top-right": "pos_tr", "top-left": "pos_tl", "bottom-right": "pos_br", "bottom-left": "pos_bl" }[CFG.hud_position || "top-right"]) })}</button>
      <button class="toggle" data-cycle-lang aria-pressed="true"><i></i>${t("set_lang", { x: t("lang_" + (CFG.language || "auto")) })}</button>
    </div>
    <p class="note">${esc(t("note", { n: CFG.new_cards_full_reward_per_day ?? 50 }))}</p>`;
  }

  function renderBakery() {
    if (!S) return;
    const collapsed = !!CFG.bakery_collapsed;
    const head = `<header class="awning"><div class="stripes"></div><div class="scallops"></div>
      <div class="sign"><img src="${IMG("cookie")}" alt="">Cookie Recall</div>
      ${collapsed ? "" : `<button class="paint" data-paint>${t("paint")}</button>`}
      <button class="collapse" data-collapse>${collapsed ? t("open") : t("collapse")}</button></header>`;
    if (collapsed) {
      app.innerHTML = `<div class="board ${RM() ? "calm" : ""}">${head}<div class="strip"><img src="${IMG("cookie")}" alt=""><div><div class="count num">${fmt(S.cookies)}</div><div class="unit">${t("strip_unit", { n: fmt(S.per_review_base) })}</div></div>
        ${S.day.cleared ? `<span class="chip"><img src="${IMG("a_check")}" alt="">${t("oven_cleared_chip")}</span>` : ""}</div></div>`;
      return;
    }
    let body = "";
    if (tab === "ach") body = renderAch();
    else if (tab === "dip") body = renderDip();
    else if (tab === "stats") body = renderStats();
    else body = renderShop();
    app.innerHTML = `<div class="board ${S.frenzy.left > 0 ? "frenzy-on" : ""} ${RM() ? "calm" : ""}">${head}${renderHero()}${renderToday()}${renderTabs()}<div class="panel" role="tabpanel">${body}</div></div>`;
  }

  function updateBakery(snap) {
    const prev = S ? S.cookies : snap.cookies;
    S = snap;
    renderBakery();
    const c = $("#count");
    if (c && prev !== snap.cookies) countTo(c, prev, snap.cookies, 500);
  }

  function confirmBox(icon, title, text, okLabel) {
    return new Promise((resolve) => {
      confirmOpen = true;
      const bg = document.createElement("div");
      bg.className = "modal-bg";
      bg.innerHTML = `<div class="modal" role="dialog" aria-modal="true"><img src="${IMG(icon)}" alt=""><h3>${esc(title)}</h3><p>${text}</p>
        <div class="row"><button class="btn ghost" data-no>${t("cancel")}</button><button class="btn" data-yes>${esc(okLabel)}</button></div></div>`;
      root.appendChild(bg);
      const done = (v) => { bg.remove(); confirmOpen = false; resolve(v); };
      bg.querySelector("[data-no]").addEventListener("click", () => done(false));
      bg.querySelector("[data-yes]").addEventListener("click", () => done(true));
      bg.addEventListener("click", (e) => { if (e.target === bg) done(false); });
      bg.querySelector("[data-yes]").focus();
    });
  }

  async function act(action, data, origin) {
    const res = await send(action, data);
    if (!res || !res.ok) {
      SFX.no();
      if (origin) { origin.animate?.([{ transform: "translateX(0)" }, { transform: "translateX(-5px)" }, { transform: "translateX(5px)" }, { transform: "translateX(0)" }], { duration: 220 }); }
      if (res && res.snap) updateBakery(res.snap);
      return res;
    }
    if (res.cfg) CFG = res.cfg;
    if (res.snap) updateBakery(res.snap);
    handleEvents(res.events);
    return res;
  }

  function wireBakery() {
    root.addEventListener("click", async (e) => {
      if (confirmOpen) return;
      const el = e.target.closest && e.target.closest("button, [data-shelf]");
      if (!el) return;
      const d = el.dataset;
      if (d.tab) { tab = d.tab; try { sessionStorage.setItem("cookierecall-tab", tab); } catch (x) {} renderBakery(); return; }
      if (d.qty) { qty = d.qty === "max" ? "max" : Number(d.qty); try { sessionStorage.setItem("cookierecall-qty", String(qty)); } catch (x) {} renderBakery(); return; }
      if ("collapse" in d) { await act("setting", { key: "bakery_collapsed", value: !CFG.bakery_collapsed }); return; }
      if (d.buy) {
        const r = el.getBoundingClientRect();
        const res = await act("buy", { id: d.buy, qty: qty }, el);
        if (res && res.ok) {
          SFX.buy();
          crumbs(r.left + 24, r.top + r.height / 2, 10);
          const shelf = $(`[data-shelf="${d.buy}"]`);
          if (shelf) shelf.classList.add("pop");
        }
        return;
      }
      if (d.buyUpgrade) {
        const r = el.getBoundingClientRect();
        const res = await act("upgrade", { id: d.buyUpgrade }, el);
        if (res && res.ok) { SFX.golden(); crumbs(r.left + r.width / 2, r.top + r.height / 2, 14); tipEl.classList.remove("on"); }
        return;
      }
      if ("freeze" in d) { const res = await act("freeze", {}, el); if (res && res.ok) { SFX.buy(); toast("u_freeze", t("freeze_bought"), t("freeze_bought_b")); } return; }
      if (d.perk) { if (el.getAttribute("aria-disabled") === "true") return; const res = await act("perk", { id: d.perk }, el); if (res && res.ok) SFX.win(); return; }
      if ("graduate" in d) {
        const ok = await confirmBox("a_diploma", t("grad_q"), t("grad_q_b", { n: pl(S.prestige.pending, "diploma") }), t("receive"));
        if (ok) await act("graduate", {});
        return;
      }
      if (d.setting) { await act("setting", { key: d.setting, value: !CFG[d.setting] }); return; }
      if (d.palette) {
        const res = await act("setting", { key: "palette", value: d.palette });
        if (res && res.ok) { applyPalette(CFG.palette_vars); renderBakery(); }
        return;
      }
      if ("paint" in d) {
        tab = "stats"; try { sessionStorage.setItem("cookierecall-tab", tab); } catch (x) {}
        renderBakery();
        const el2 = $("#settings"); if (el2) el2.scrollIntoView({ behavior: RM() ? "auto" : "smooth", block: "center" });
        return;
      }
      if ("cycleLang" in d) {
        const order = ["auto", "fr", "en"];
        const next = order[(order.indexOf(CFG.language || "auto") + 1) % order.length];
        await act("setting", { key: "language", value: next });
        return;
      }
      if ("cyclePos" in d) {
        const order = ["top-right", "bottom-right", "bottom-left", "top-left"];
        const next = order[(order.indexOf(CFG.hud_position || "top-right") + 1) % order.length];
        await act("setting", { key: "hud_position", value: next });
      }
    });
  }


  // =================================================================== DECK LIST: one-click study
  function enhanceDeckList() {
    const table = document.querySelector("table:has(tr.deck)") || (document.querySelector("tr.deck") || {}).closest?.("table");
    if (!table || table.dataset.crDone) return;
    table.dataset.crDone = "1";
    const css = document.createElement("style");
    css.id = "cr-decklist";
    css.textContent = `
      .cr-study { font: 600 13px/1 "CookieRecallFredoka", ui-rounded, system-ui, sans-serif; border: 0; cursor: pointer; border-radius: 999px;
        padding: 7px 13px 7px 11px; margin: 0 2px; color: #fff; background: var(--cr-btn, #1e3b34); white-space: nowrap;
        box-shadow: 0 2px 0 rgba(0,0,0,.18); transition: transform .12s, filter .12s; }
      .cr-study:hover { transform: translateY(-1px); filter: brightness(1.12); }
      .cr-study:active { transform: translateY(1px); box-shadow: none; }
      .cr-study:focus-visible { outline: 3px solid #f5c542; outline-offset: 2px; }
      .cr-done { font: 600 12px/1 "CookieRecallFredoka", ui-rounded, system-ui, sans-serif; color: var(--fg-faint, #999); padding: 0 10px; white-space: nowrap; }
      td.cr-cell { text-align: end; padding-inline: 6px !important; }
      .cr-cta { display: flex; align-items: center; gap: 14px; max-width: 520px; margin: 18px auto 14px; padding: 10px 10px 10px 18px;
        border-radius: 18px; background: var(--canvas-elevated, #fff); border: 1px solid var(--border-subtle, #e5e5e5);
        box-shadow: 0 10px 24px -18px rgba(0,0,0,.45); text-align: start; font-family: "CookieRecallFredoka", ui-rounded, system-ui, sans-serif; }
      .cr-cta .t { flex: 1; min-width: 0; }
      .cr-cta b { display: block; font-size: 17px; font-weight: 650; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .cr-cta small { color: var(--fg-subtle, #777); font-size: 13px; }
      .cr-cta .cr-study { font-size: 16px; padding: 12px 20px 12px 16px; }
      .cr-cta kbd { font: inherit; font-size: 11px; padding: 1px 5px; border-radius: 5px; border: 1px solid var(--border, #ccc); margin-left: 4px; }`;
    document.head.appendChild(css);
    document.documentElement.style.setProperty("--cr-btn", (CFG.palette_vars || {})["--board"] || "#1e3b34");

    const headRow = table.querySelector("tr:first-child");
    const optsTh = headRow && headRow.querySelector("th.optscol");
    if (optsTh) { const th = document.createElement("th"); optsTh.before(th); }
    let best = null, current = null;
    table.querySelectorAll("tr.deck").forEach((tr) => {
      const did = Number(tr.id);
      const counts = [...tr.querySelectorAll(".new-count, .learn-count, .review-count")].map((e) => Number(e.textContent) || 0);
      const due = counts.reduce((a, b) => a + b, 0);
      const name = (tr.querySelector("a.deck") || {}).textContent || "";
      const td = document.createElement("td");
      td.className = "cr-cell";
      td.innerHTML = due > 0
        ? `<button class="cr-study" data-did="${did}" title="${esc(t("study_tip"))}">▶ ${t("study")}</button>`
        : `<span class="cr-done">✓ ${t("up_to_date")}</span>`;
      const opts = tr.querySelector("td.opts");
      if (opts) opts.before(td); else tr.appendChild(td);
      const info = { did, due, name };
      if (tr.classList.contains("current")) current = info;
      if (due > 0 && (!best || due > best.due)) best = info;
    });
    table.addEventListener("click", (e) => {
      const b = e.target.closest && e.target.closest(".cr-study");
      if (!b) return;
      e.preventDefault(); e.stopPropagation();
      send("study", { did: Number(b.dataset.did) });
    });

    // big call to action above the deck list
    const target = current && current.due > 0 ? current : best;
    const cta = document.createElement("div");
    cta.className = "cr-cta";
    cta.innerHTML = target
      ? `<div class="t"><b>${esc(target.name)}</b><small>${esc(plt(target.due, "cards_due"))} · <kbd>S</kbd></small></div><button class="cr-study" data-did="${target.did}">▶ ${t("study_now")}</button>`
      : `<div class="t"><b>${t("all_done")}</b><small>${t("all_done_sub")}</small></div>`;
    const anchor = table.closest("center") || table;
    anchor.parentNode.insertBefore(cta, anchor);
    cta.addEventListener("click", (e) => {
      const b = e.target.closest && e.target.closest(".cr-study");
      if (b) send("study", { did: Number(b.dataset.did) });
    });
    if (target) {
      document.addEventListener("keydown", (e) => {
        if (e.key !== "s" && e.key !== "S") return;
        if (e.metaKey || e.ctrlKey || e.altKey) return;
        const tag = (document.activeElement && document.activeElement.tagName) || "";
        if (/INPUT|TEXTAREA|SELECT/.test(tag)) return;
        e.preventDefault();
        send("study", { did: target.did });
      });
    }
  }

  // =================================================================== REVIEW SCREEN: card style
  function cardStyle() {
    if (!CFG.card_style) return;
    const v = CFG.card_vars || {};
    const st = document.createElement("style");
    st.id = "cr-card";
    st.textContent = `
      html.cr-card { ${Object.entries(v).map(([k, x]) => `${k}:${x}`).join(";")} }
      html.cr-card, html.cr-card body.card { background: var(--cr-desk) !important; }
      html.cr-card body.card { color: var(--cr-ink) !important; margin: 0 !important; padding: 26px 18px 48px !important; }
      html.cr-card #qa { position: relative; max-width: 720px; margin: 16px auto 0; padding: 40px 44px 44px; border-radius: 24px;
        background: var(--cr-paper); line-height: 1.55; min-height: 96px;
        box-shadow: 0 0 0 1px var(--cr-line), 0 18px 40px -24px rgba(60, 40, 20, .45); }
      html.cr-card #qa::before { content: ""; position: absolute; left: 32px; right: 32px; top: 0; height: 6px; border-radius: 0 0 8px 8px;
        background: repeating-linear-gradient(90deg, var(--cr-accent) 0 16px, transparent 16px 32px); opacity: .95; }
      html.cr-card #qa hr#answer, html.cr-card #qa hr { border: 0; height: 0; background: none; border-top: 2px dashed var(--cr-line); margin: 28px -10px; }
      html.cr-card #qa img { border-radius: 12px; }
      html.cr-card #typeans { border-radius: 12px; border: 1.5px solid var(--cr-line); padding: 10px 14px; background: var(--cr-desk); color: inherit; }
      html.cr-card .replay-button svg circle { fill: var(--cr-accent); stroke: transparent; }
      html.cr-card .replay-button svg path { fill: #fff; }
      html.cr-card body.card.nightMode, html.cr-card.night-mode body.card { background: var(--cr-desk-dark) !important; color: var(--cr-ink-dark) !important; }
      html.cr-card.night-mode { background: var(--cr-desk-dark) !important; }
      html.cr-card.night-mode #qa, html.cr-card body.nightMode #qa { background: var(--cr-paper-dark); box-shadow: 0 0 0 1px var(--cr-line-dark), 0 18px 40px -24px rgba(0,0,0,.7); }
      html.cr-card.night-mode #qa hr, html.cr-card body.nightMode #qa hr { border-top-color: var(--cr-line-dark); }
      html.cr-font body.card { font-family: "CookieRecallFredoka", ui-rounded, "Segoe UI", system-ui, sans-serif !important; font-size: 22px; }
      @media (max-width: 640px) { html.cr-card #qa { padding: 30px 20px 32px; border-radius: 18px; } }`;
    document.head.appendChild(st);
    const html = document.documentElement;
    const probe = document.createElement("div");
    probe.style.cssText = "position:absolute;visibility:hidden;background:var(--canvas)";
    function check() {
      // look at the note type's own styling, without ours
      html.classList.remove("cr-card", "cr-font");
      const cs = getComputedStyle(document.body);
      document.body.appendChild(probe);
      const canvas = getComputedStyle(probe).backgroundColor;
      probe.remove();
      const bg = cs.backgroundColor;
      const plainBg = cs.backgroundImage === "none" && ["rgb(255, 255, 255)", "rgba(0, 0, 0, 0)", "transparent", canvas].includes(bg);
      const fg = cs.color;
      const plainFg = ["rgb(0, 0, 0)", "rgb(2, 2, 2)"].includes(fg) || document.body.classList.contains("nightMode");
      const font = cs.fontFamily.toLowerCase().replace(/["']/g, "").trim();
      const plainFont = font === "arial" || font.startsWith("arial,") || font === "";
      if (plainBg && plainFg) html.classList.add("cr-card");
      if (plainBg && plainFg && plainFont) html.classList.add("cr-font");
    }
    const qa = document.getElementById("qa");
    if (qa) new MutationObserver(check).observe(qa, { childList: true });
    new MutationObserver(check).observe(document.body, { attributes: true, attributeFilter: ["class"] });
    check();
  }

  // =================================================================== public API
  window.CookieRecall = {
    reward(p) { try { if (MODE === "hud" && CFG.hud !== false) hudReward(p); else S = p.snap; } catch (e) { console.error("Cookie Recall", e); } },
    update(snap) {
      try {
        if (MODE === "bakery") updateBakery(snap);
        else if (MODE === "hud" && CFG.hud !== false) updateHud(snap, false);
        else if (MODE === "mini") { S = snap; renderMini(); }
      } catch (e) { console.error("Cookie Recall", e); }
    },
    events(list) { try { handleEvents(list); } catch (e) { console.error("Cookie Recall", e); } },
    scrollIntoView() { host.scrollIntoView({ behavior: RM() ? "auto" : "smooth", block: "start" }); },
  };

  try {
    if (MODE === "hud" || MODE === "card") cardStyle();
    if (MODE === "bakery") { enhanceDeckList(); wireBakery(); renderBakery(); if (BOOT.scroll) setTimeout(() => window.CookieRecall.scrollIntoView(), 60); }
    else if (MODE === "mini") renderMini();
    else if (MODE === "hud" && CFG.hud !== false && S) updateHud(S, false);
    if (BOOT.events && BOOT.events.length) setTimeout(() => handleEvents(BOOT.events), 350);
  } catch (e) { console.error("Cookie Recall", e); }
  }
})();
