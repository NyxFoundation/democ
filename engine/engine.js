/* 再生エンジン。シーンの中身は engine/scenes/*.js が持つ。
   対象の指定はどのヘルパも同じで、裸の id ("tcT")・セレクタ(".cl.bad")・Element を取る。 */
const D = (() => {
  const q = t => t instanceof Element ? t
        : typeof t === 'string' ? document.querySelector(/^[\w-]+$/.test(t) ? '#' + t : t) : null;
  const qa = s => [...document.querySelectorAll(s)];
  const stage = document.getElementById('stage');

  if (new URLSearchParams(location.search).has('rec')) document.body.classList.add('rec');
  const wrap = document.querySelector('.stage-wrap');
  const scale = () => wrap.getBoundingClientRect().width / 1600;
  const fit = () => { stage.style.transform = `scale(${scale()})`; };
  addEventListener('resize', fit); fit();

  /* ---- タイマーは全部取り消せるようにする。シーンを撮り直せる条件 ---- */
  let timers = [];
  const later = (fn, ms) => timers.push(setTimeout(fn, ms));
  const clear = () => { timers.forEach(clearTimeout); timers = []; };
  const sleep = ms => new Promise(r => later(r, ms));

  const text = (t, s) => { const el = q(t); if (el) el.textContent = s; return el; };
  const html = (t, s) => { const el = q(t); if (el) el.innerHTML = s; return el; };
  const cls = (t, name, on = true) => { const el = q(t); if (el) el.classList.toggle(name, on); return el; };
  const show = (t, on = true) => { const el = q(t); if (el) el.style.display = on ? '' : 'none'; return el; };

  /* 数は一気に出さない。必ず動かして着地させる */
  function count(t, to, fmt = v => v.toLocaleString()) {
    const el = q(t); let v = 0;
    const step = () => { v = Math.min(to, v + Math.max(1, Math.round(to / 90)));
                         el.textContent = fmt(v); if (v < to) later(step, 16); };
    step();
  }

  /* ---- 読む速さから保持時間を決める ----
     日本語字幕の実務値（4 CPS 基準・最大 7・1 枚 6 秒まで）を内側に取る。
     文字を増やせば自動的に長く出る。縮めたいなら文を短くするのが先。 */
  let R = { cps: 5.5, lead: 0.9, min: 2.4, max: 5.6 };
  const plain = h => String(h ?? '').replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, '');
  const read = (h, mul = 1) => {
    const n = plain(h).length;
    return Math.round(Math.min(R.max, Math.max(R.min, R.lead + n / R.cps)) * 1000 * mul);
  };

  /* 文字数が変わってもはみ出さないよう、入る大きさまで落とす */
  function autofit(t, max = 52, min = 24, maxH = 360) {
    const el = q(t); if (!el) return;
    let s = max; el.style.fontSize = s + 'px';
    while (s > min && el.getBoundingClientRect().height / scale() > maxH) {
      s -= 2; el.style.fontSize = s + 'px';
    }
  }

  /* ---- ステージ座標での矩形。stage は scale されているので割り戻す ---- */
  function box(el) {
    const sr = stage.getBoundingClientRect(), s = scale(), r = q(el).getBoundingClientRect();
    return { left: (r.left - sr.left) / s, right: (r.right - sr.left) / s,
             top: (r.top - sr.top) / s, h: r.height / s, w: r.width / s };
  }

  /* ---- シーン登録 ---- */
  const Scenes = {};
  const register = (name, def) => { Scenes[name] = def; };

  /* ---- 走らせる ---- */
  let stages = [], resetFn = () => {}, SPEC = null;
  function define(list, reset) {
    stages = list; resetFn = reset || (() => {});
    const boxEl = document.getElementById('steps');
    if (boxEl) {
      boxEl.innerHTML = '';
      list.forEach((s, i) => {
        const b = document.createElement('button');
        b.textContent = `${i} ${s.name}`; b.dataset.step = i; b.onclick = () => go(i); boxEl.appendChild(b);
      });
      const r = document.createElement('button'); r.textContent = '↻ replay'; r.onclick = replay;
      boxEl.appendChild(r);
    }
    addEventListener('keydown', e => {
      if (e.key === 'r') replay();
      if (/^[0-9]$/.test(e.key) && +e.key < list.length) go(+e.key);
    });
    const tickEl = document.getElementById('tick'), t0 = performance.now();
    if (tickEl) setInterval(() => { tickEl.textContent = ((performance.now() - t0) / 1000).toFixed(1) + 's'; }, 100);
  }
  const mark = n => qa('#steps button').forEach(b =>
    b.setAttribute('aria-current', b.dataset.step == n ? 'step' : ''));
  async function go(n) {
    clear(); mark(n); resetFn(); delete document.body.dataset.done;
    for (let i = 0; i <= n; i++) { if (i > 0) await sleep(stages[i].gap ?? 420); await stages[i].run(); }
    document.body.dataset.done = '1';          /* 録画はこれを見て止まる */
  }
  const replay = () => go(stages.length - 1);

  /* 1 場面だけ頭から流す。録画をシーンごとに分けるのに使う。
     終わったら data-done が立つので、外から終わりが分かる。 */
  async function playScene(i) {
    clear(); mark(i); resetFn();
    delete document.body.dataset.done;
    const s = SPEC.scenes[i];
    await Scenes[s.type].play(s);
    document.body.dataset.done = '1';
  }

  /* ---- 仕様書から組み立てる ---- */
  function boot(spec) {
    SPEC = spec;
    Object.assign(R, spec.reading || {});
    if (spec.accent) document.documentElement.style.setProperty('--accent', spec.accent);
    const host = document.getElementById('scenes');
    const used = [...new Set(spec.scenes.map(s => s.type))];
    used.forEach(t => {
      const def = Scenes[t];
      if (!def) throw new Error(`知らないシーン種別: ${t}`);
      if (def.mount) host.insertAdjacentHTML('beforeend', def.mount());
    });
    const resetAll = () => { stage.className = 'stage'; used.forEach(t => Scenes[t].reset?.()); };
    define(spec.scenes.map((s, i) => ({
      name: s.name || `${i} ${s.type}`,
      gap: (s.gap ?? 0.42) * 1000,
      run: () => Scenes[s.type].play(s),
    })), resetAll);
    replay();
  }

  return { q, qa, stage, scale, box, sleep, later, clear, text, html, cls, show, count,
           read, plain, autofit, define, go, replay, playScene, register, Scenes, boot,
           get reading() { return R; }, get spec() { return SPEC; } };
})();
