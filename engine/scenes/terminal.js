D.register('terminal', {
  mount: () => `
  <div class="sc term" id="term"><div class="tw">
    <div class="th" id="termH"><i></i></div><div class="trule"></div>
    <div id="termLines"></div>
    <div class="side" id="termSide"></div>
  </div></div>`,

  reset() { D.cls('#term', 'on', false); D.cls('#termSide', 'on', false); D.html('#termLines', ''); },

  async play(s) {
    D.html('#termH', '<i></i>' + (s.title || ''));
    D.html('#termLines', s.codeHtml.map((l, i) => `<div class="ln" id="tl${i}">${l || '&nbsp;'}</div>`).join(''));
    D.html('#termSide', s.side ? (s.side.tabHtml || '') + `<pre>${s.side.codeHtml.join('\n')}</pre>` : '');
    D.cls('#termSide', 'on', false);
    D.cls('#term', 'on');
    await D.sleep(420);

    const gap = (s.gapMs ?? 390);
    for (let i = 0; i < s.codeHtml.length; i++) {
      D.cls('#tl' + i, 'on');
      if (s.side && s.side.after === i + 1) D.cls('#termSide', 'on');
      await D.sleep(s.codeHtml[i].trim() ? gap : gap * 0.5);
    }
    await D.sleep(s.hold != null ? s.hold * 1000 : 1600);
    if (!D.smooth) D.cls('#term', 'on', false);
  },
});
