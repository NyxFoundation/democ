D.register('split', {
  mount: () => `
  <div class="sc split" id="sp">
    <div class="l"><div id="spLT"></div><pre id="spL"></pre></div>
    <div class="r"><div id="spRT"></div><pre id="spR">&nbsp;</pre></div>
    <div class="arrow" id="spAr">→</div>
    <div class="band" id="spBand">&nbsp;</div>
    <div class="fly" id="fly"><span class="fa" id="flyA"></span><span class="fb" id="flyB"></span></div>
  </div>`,

  reset() {
    D.cls('#sp', 'on', false); D.cls('#sp', 'ar', false); D.cls('#sp', 'dim', false);
    D.cls('#spBand', 'on', false); D.cls('#fly', 'on', false);
    D.html('#spL', ''); D.html('#spR', '&nbsp;');
  },

  async play(s) {
    D.cls('#sp', 'ar', false); D.cls('#spBand', 'on', false); D.cls('#fly', 'on', false);
    D.html('#spLT', s.left.tabHtml || ''); D.html('#spRT', s.right.tabHtml || '');
    D.html('#spL', s.left.codeHtml.join('\n'));
    D.html('#spR', '&nbsp;');
    D.cls('#sp', 'on');
    await D.sleep(s.read != null ? s.read * 1000 : D.read(s.left.plain, 0.7) + 700);

    D.cls('#sp', 'ar');
    /* 着地先を先に組む。opacity 0 のまま置いておけば、飛んだ先に場所がある */
    D.html('#spR', s.right.codeHtml.join('\n'));
    D.cls('#spR', 'pending');
    await D.sleep(260);

    const from = D.q('#spFly'), to = D.q('#spLand');
    if (from && to) {
      const ms = (s.flight ?? 1.25) * 1000;
      const F = D.box(from), T = D.box(to), el = D.q('#fly');
      D.cls(from, 'srcfade');
      el.style.transition = 'none';
      el.style.left = F.left + 'px'; el.style.top = F.top + 'px';
      el.style.transform = 'translate(0,0)';
      D.html('#flyA', `<span class="bx">${from.innerHTML}</span>`);
      D.html('#flyB', `<span class="bx">${to.innerHTML}</span>`);
      D.cls('#fly', 'swap', false); D.cls('#fly', 'on');
      void el.offsetWidth;
      el.style.transition = `transform ${ms}ms cubic-bezier(.45,.02,.2,1)`;
      el.style.transform =
        `translate(${(T.left - F.left).toFixed(1)}px, ${(T.top - F.top).toFixed(1)}px)`;
      await D.sleep(ms * 0.40);
      D.cls('#fly', 'swap');                       /* 空中で表記が変わる */
      await D.sleep(ms * 0.60 + 90);
      D.cls(from, 'srcfade', false);
    }
    D.cls('#spR', 'pending', false);
    if (to) D.cls(to, 'landed');
    D.cls('#fly', 'on', false);
    await D.sleep(600);

    if (s.band) {
      D.html('#spBand', s.band); D.cls('#sp', 'dim');
      await D.sleep(40); D.cls('#spBand', 'on');
      await D.sleep(s.hold != null ? s.hold * 1000 : D.read(s.band, 1.2));
      D.cls('#spBand', 'on', false); D.cls('#sp', 'dim', false);
      await D.sleep(230);
    }
    D.cls('#sp', 'on', false);
  },
});
