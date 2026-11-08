D.register('browser', {
  mount: () => `
  <div class="sc brw" id="brw">
    <div class="bar"><span>‹ ›</span><span class="url" id="brwUrl"></span><span>⟳</span></div>
    <div class="nav">
      <span class="lg" id="brwBrand"></span>
      <span class="nv" id="brwNav"></span>
      <span class="me"><span class="em" id="brwEm"></span><span class="av" id="brwAv"></span></span>
    </div>
    <div class="body">
      <div class="bc" id="brwBc"></div>
      <div id="brwFiles"></div>
      <div class="stamp" id="brwStamp">&nbsp;</div>
    </div>
  </div>`,

  reset() { D.cls('#brw', 'on', false); D.cls('#brwStamp', 'on', false); D.html('#brwFiles', ''); },

  async play(s) {
    const files = rows => rows.map((f, i) =>
      `<div class="f" id="bf${i}"><span class="ic">${f[0]}</span><span>${f[1]}</span>` +
      `<span class="sz">${f[2] || ''}</span></div>`).join('');

    D.html('#brwUrl', s.urlHtml);
    D.html('#brwBrand', s.brand || '');
    D.html('#brwNav', (s.nav || []).map((n, i) => i === 0 ? `<b>${n}</b>` : `<span>${n}</span>`).join(''));
    D.html('#brwEm', s.user?.email || '');
    D.text('#brwAv', s.user?.initial || '');
    D.html('#brwBc', s.crumbHtml || '');
    D.html('#brwFiles', files(s.files || []));
    D.cls('#brwStamp', 'on', false);
    D.html('#brwStamp', s.change?.stamp || '&nbsp;');

    D.cls('#brw', 'on');
    await D.sleep(500);
    for (let i = 0; i < (s.files || []).length; i++) { D.cls('#bf' + i, 'on'); await D.sleep(170); }
    await D.sleep((s.settle ?? 1.2) * 1000);

    if (s.change) {
      D.html('#brwUrl', s.change.urlHtml);          /* 変わったのは URL の一文字だけ */
      await D.sleep(420);
      D.html('#brwBc', s.change.crumbHtml || '');
      (s.change.files || []).forEach((f, i) => {
        const el = D.q('#bf' + i); if (!el) return;
        el.querySelector('.ic').textContent = f[0];
        el.children[1].innerHTML = f[1];
        el.querySelector('.sz').textContent = f[2] || '';
        el.classList.add('leaked');
      });
      await D.sleep(560);
      if (s.change.stamp) D.cls('#brwStamp', 'on');
      await D.sleep(s.hold != null ? s.hold * 1000 : D.read(s.change.stamp, 1.1));
    } else {
      await D.sleep(s.hold != null ? s.hold * 1000 : 1800);
    }
    if (!D.smooth) D.cls('#brw', 'on', false);
  },
});
