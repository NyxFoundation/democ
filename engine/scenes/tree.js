D.register('tree', {
  mount: () => `
  <div class="sc tree" id="tree">
    <div class="dh" id="treeH">$ <b></b></div>
    <div class="ddone" id="treeDone">&nbsp;</div>
    <div class="dnet" id="dnet"><svg class="dw" id="dwire" width="1600" height="560" viewBox="0 0 1600 560"></svg></div>
    <div class="chk" id="chk">
      <div class="ch" id="chkH"></div>
      <div class="cg" id="chkGA"></div>
      <pre id="chkA">&nbsp;</pre>
      <div class="eq" id="chkEq">≟</div>
      <div class="cg" id="chkGB"></div>
      <pre class="b" id="chkB">&nbsp;</pre>
      <div class="vv" id="chkV">&nbsp;</div>
    </div>
    <div class="dcount" id="dcount"><b id="dcN">0</b> <span id="dcU">件</span></div>
    <div class="band" id="treeBand">&nbsp;</div>
  </div>`,

  reset() {
    D.cls('#tree', 'on', false); D.cls('#tree', 'dim', false); D.cls('#tree', 'chk', false);
    D.cls('#treeDone', 'on', false); D.cls('#dcount', 'on', false); D.cls('#treeBand', 'on', false);
    D.cls('#chk', 'on', false);
  },

  async play(s) {
    const net = D.q('#dnet'), svg = D.q('#dwire'), NS = 'http://www.w3.org/2000/svg';
    net.querySelectorAll('.dn').forEach(e => e.remove());
    svg.innerHTML = '';
    const nodes = [], lines = [], axLines = [];

    const node = (txt, x, y, cls) => {
      const d = document.createElement('div');
      d.className = 'dn' + (cls ? ' ' + cls : '');
      d.style.left = x + 'px'; d.style.top = y + 'px';
      if (txt) d.textContent = txt;
      net.appendChild(d); nodes.push({ el: d, x, y });
      return nodes.length - 1;
    };
    const link = (a, b, cls) => {
      const A = nodes[a], B = nodes[b], l = document.createElementNS(NS, 'line');
      l.setAttribute('x1', A.x); l.setAttribute('y1', A.y);
      l.setAttribute('x2', B.x); l.setAttribute('y2', B.y);
      if (cls) l.classList.add(cls);
      svg.appendChild(l); (cls === 'ax' ? axLines : lines).push(l);
    };
    /* 件数が変わっても端が切れないよう、幅から割り付ける */
    const spread = (n, margin) => i => margin + (1600 - 2 * margin) * (n === 1 ? .5 : (i + .5) / n);

    const L1 = s.levels.l1 || [], L2 = s.levels.l2 || [], AX = s.axioms || [];
    const nDots = s.levels.dots ?? 0;
    const root = node(s.root, 800, 36, 'root');
    const xs1 = spread(L1.length, 148);
    const l1 = L1.map((n, i) => node(n, xs1(i), 150, ''));
    l1.forEach(i => link(root, i));
    const xs2 = spread(L2.length, 124);
    const l2 = L2.map((n, i) => node(n, xs2(i), 274, 'l2'));
    l2.forEach((t, i) => link(l1[i % l1.length], t));
    const xs3 = spread(nDots, 92);
    const l3 = [];
    for (let i = 0; i < nDots; i++) l3.push(node('', xs3(i), 382 + (i % 3) * 16, 'dot'));
    l3.forEach((t, i) => link(l2[i % l2.length], t));
    const xs4 = spread(AX.length, 520);
    const ax = AX.map((n, i) => node(n, xs4(i), 496, 'ax'));
    ax.forEach((t, i) => { for (let k = 0; k < 6; k++) link(l3[(i * 7 + k * 3) % l3.length], t, 'ax'); });

    const on = (idx, cls = 'on') => idx.forEach(i => D.cls(nodes[i].el, cls));
    /* まとめて出す。await の回数を減らさないと、録画中にタイマーが詰まる */
    const wave = async (idx, cls, chunk, gap) => {
      for (let i = 0; i < idx.length; i += chunk) { on(idx.slice(i, i + chunk), cls); await D.sleep(gap); }
    };
    const band = async (h, mul = 1.1) => {
      if (!h) return;
      D.html('#treeBand', h); D.cls('#tree', 'dim');
      await D.sleep(40); D.cls('#treeBand', 'on');
      await D.sleep(D.read(h, mul));
      D.cls('#treeBand', 'on', false); D.cls('#tree', 'dim', false);
      await D.sleep(230);
    };
    const open = async (o) => {
      const e = D.q('#chk'); e.className = 'chk';
      D.text('#chkH', 'NODE — ' + o.node);
      D.html('#chkGA', s.inspectLabels?.need || '');
      D.html('#chkGB', s.inspectLabels?.has || '');
      D.html('#chkA', o.needHtml); D.html('#chkB', o.hasHtml);
      D.text('#chkEq', '≟'); D.html('#chkV', '&nbsp;'); D.cls('#chkV', 'on', false);
      D.cls('#tree', 'chk'); D.later(() => D.cls('#chk', 'on'), 40);
      await D.sleep((o.read ?? 2.1) * 1000);
      D.text('#chkEq', o.ok ? '=' : '≠');
      D.cls('#chk', o.ok ? 'good' : 'bad');
      await D.sleep(300);
      D.html('#chkV', o.ok ? (s.inspectLabels?.ok || '') : (s.inspectLabels?.ng || ''));
      D.cls('#chkV', 'on');
    };
    const close = async () => { D.cls('#chk', 'on', false); await D.sleep(300); D.cls('#tree', 'chk', false); };

    D.html('#treeH', '$ <b>' + (s.command || 'build') + '</b>');
    D.cls('#tree', 'on');
    await D.sleep(650);

    /* まず失敗の形を見せる。通ったことの意味は、落ちる場合を知ってから分かる */
    if (s.errorHtml) {
      D.html('#treeDone', s.errorHtml); D.cls('#treeDone', 'on');
      await D.sleep(D.read(s.errorPlain, 1.15));
      D.cls('#treeDone', 'on', false); D.html('#treeDone', '&nbsp;');
      await D.sleep(700);
    }

    on([root]); await D.sleep(820);
    await wave(l1, 'on', 2, 150);
    lines.forEach(l => l.classList.add('on'));
    await D.sleep(520);
    await wave(l2, 'on', 3, 150);
    await D.sleep(360);
    await wave(l3, 'on', 8, 90);
    axLines.forEach(l => l.classList.add('on'));
    await wave(ax, 'on', 1, 220);
    if (s.total) {
      D.cls('#dcount', 'on');
      D.html('#dcU', s.unit || '件');
      D.count('dcN', s.total, v => String(v));
      await D.sleep(850);
    }
    await band(s.labels?.built);

    const ins = s.inspect || [];
    if (ins[0]) {
      D.cls(nodes[l1[0]].el, 'focus');
      await D.sleep(500);
      await open(ins[0]);
      await D.sleep(1150);
      await band(s.labels?.compare);
      await close();
      D.cls(nodes[l1[0]].el, 'focus', false);
      on([l1[0]], 'ok');
      await D.sleep(400);
    }

    /* そして同じことが残り全部で起きる */
    on([root], 'ok'); await D.sleep(240);
    await wave(l1, 'ok', 2, 110);
    await wave(l2, 'ok', 3, 110);
    lines.forEach(l => l.classList.add('ok'));
    await wave(l3, 'ok', 8, 80);
    await D.sleep(520);
    await band(s.labels?.ok);

    if (ins[1]) {
      const i = l1[1 % l1.length];
      D.cls(nodes[i].el, 'focus');
      await D.sleep(420);
      await open(ins[1]);
      await D.sleep(1050);
      await band(s.labels?.fail);
      await close();
      D.cls(nodes[i].el, 'focus', false);
      await D.sleep(400);
    }

    if (s.doneHtml) {
      D.html('#treeDone', s.doneHtml); D.cls('#treeDone', 'on');
      await D.sleep(s.hold != null ? s.hold * 1000 : D.read(s.donePlain, 1.1));
    }
    D.cls('#tree', 'on', false);
  },
});
