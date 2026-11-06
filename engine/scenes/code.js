D.register('code', {
  mount: () => `<div class="sc code" id="code"><div class="cw" id="codeW"></div></div>`,

  reset() { D.cls('#code', 'on', false); D.cls('#code', 'dim', false); D.html('#codeW', ''); },

  async play(s) {
    const good = new Set(s.good || []), bad = new Set(s.bad || []), badges = s.badges || {};
    let html = s.tabHtml || '';
    for (const l of s.lines) {
      if (l.gap) { html += '<div class="gap"></div>'; continue; }
      if (s.missing && s.missing.after === l.n) { /* 行の後ろに差す。下で出す */ }
      const kind = good.has(l.n) ? ' good' : bad.has(l.n) ? ' bad' : '';
      const badge = badges[l.n]
        ? `<span class="cb ${good.has(l.n) ? 'ok' : 'no'}" id="cbg${l.n}">${badges[l.n]}</span>` : '';
      html += `<div class="cl" id="cl${l.n}" data-n="${l.n}"><i>${l.n}</i><span>${l.html}</span>${badge}</div>`;
      if (s.missing && s.missing.after === l.n)
        html += `<div class="miss" id="codeMiss"><i>—</i><span>  ${s.missing.text}</span></div>`;
    }
    if (s.note) html += `<div class="note" id="codeNote">${s.note}</div>`;
    D.html('#codeW', html);
    /* 班分けは最初は伏せておく。読んだ後で色がつくから「見落とし」が成立する */
    D.qa('#codeW .cl').forEach(e => e.classList.remove('good', 'bad'));

    D.cls('#code', 'on');
    await D.sleep(s.read != null ? s.read * 1000 : D.read(s.lines.map(l => l.plain).join(' '), 0.5) + 900);

    const okBadge = Object.keys(badges).find(n => good.has(+n));
    if (okBadge) { D.cls('#cbg' + okBadge, 'on'); await D.sleep(1400); }

    D.qa('#codeW .cl').forEach(e => e.classList.add('dim'));
    good.forEach(n => { D.cls('#cl' + n, 'dim', false); D.cls('#cl' + n, 'good'); });
    await D.sleep(700);

    if (s.missing) { D.cls('#codeMiss', 'on'); await D.sleep(520); }
    bad.forEach(n => { D.cls('#cl' + n, 'dim', false); D.cls('#cl' + n, 'bad'); });
    const noBadge = Object.keys(badges).find(n => bad.has(+n));
    if (noBadge) D.cls('#cbg' + noBadge, 'on');
    await D.sleep(820);

    if (s.note) { D.cls('#codeNote', 'on'); D.cls('#code', 'dim'); }
    await D.sleep(s.hold != null ? s.hold * 1000 : D.read(s.note, 1.25));
    D.cls('#code', 'on', false); D.cls('#code', 'dim', false);
  },
});
