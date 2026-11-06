D.register('card', {
  mount: () => `
  <div class="sc card" id="card"><div class="in">
    <div class="tab" id="cardTab"></div>
    <div class="t" id="cardT">&nbsp;</div>
    <div class="big" id="cardN" style="display:none">0</div>
    <div class="s" id="cardS"></div>
    <pre id="cardP" style="display:none"></pre>
  </div></div>`,

  reset() {
    D.cls('#card', 'on', false); D.cls('#card', 'go', false);
    D.show('#cardP', false); D.show('#cardN', false); D.html('#cardTab', '');
  },

  async play(s) {
    D.cls('#card', 'go', false);
    if (D.q('#card').classList.contains('on')) await D.sleep(260);

    D.html('#cardTab', s.tabHtml || '');
    D.show('#cardTab', !!s.tabHtml);
    D.html('#cardT', s.text || '');
    D.show('#cardT', !!s.text);
    D.html('#cardS', s.sub || '');
    D.show('#cardS', !!s.sub);
    D.html('#cardP', (s.codeHtml || []).join('\n'));
    D.show('#cardP', !!(s.codeHtml || []).length);
    const hasN = s.number != null;
    D.show('#cardN', hasN);
    if (hasN) D.text('#cardN', '0');

    /* 文字が増えても画面に収まる大きさまで落とす */
    D.q('#cardT').style.fontSize = '';
    D.cls('#card', 'on');
    await D.sleep(20);
    if (s.text) D.autofit('#cardT', hasN ? 44 : 52, 26, hasN ? 150 : 400);
    await D.sleep(40);
    D.cls('#card', 'go');

    if (hasN) {
      await D.sleep(140);
      const comma = s.format !== 'plain';
      D.count('cardN', s.number, v => comma ? v.toLocaleString() : String(v));
      await D.sleep(900);
    }
    await D.sleep(s.hold != null ? s.hold * 1000
                                 : D.read([s.text, s.sub].join(' ')) + ((s.codeHtml || []).length ? 1600 : 0));
    D.cls('#card', 'go', false);
    if (s._next !== 'card') { await D.sleep(280); D.cls('#card', 'on', false); }
  },
});
