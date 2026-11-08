D.register('incident', {
  mount: () => '<section id="incident" class="sc incident">' +
    '<h1 id="incidentTitle"></h1>' +
    '<div class="incident-panes">' +
      '<div class="review-window"><div class="window-top"><span class="traffic">● ● ●</span><span id="incidentFile"></span></div>' +
        '<div class="review-meta"><span>GET /posts/:id</span><span class="review-pill">✓ Reviewed</span></div>' +
        '<pre id="incidentCode"></pre><div id="missingLines" class="missing-lines"><pre id="incidentMissing"></pre></div>' +
        '</div>' +
      '<div class="blog-window"><div class="window-top"><span class="traffic">● ● ●</span><span id="incidentURL"></span></div>' +
        '<div class="blog-nav"><strong>Bulletin<span> / blog</span></strong><span class="blog-user">R　rin@example.com</span></div>' +
        '<div class="blog-body"><div class="draft-label" id="draftLabel"></div>' +
          '<div id="draftContent"><div class="post-byline" id="postByline"></div><h2 id="postTitle"></h2><div class="post-date">Nov 7, 2026 · Unpublished</div><div class="post-rule"></div><p id="postBody"></p><div class="draft-ghost"></div><div class="draft-ghost short"></div></div>' +
          '<div class="forbidden"><div class="lock-symbol">⊘</div><div class="http403">403</div><h2>Access denied</h2><p>You don’t have permission to read this draft.</p><button>Back to your posts</button></div>' +
        '</div><div class="http-status" id="incidentStatus"></div></div>' +
    '</div><div class="incident-caption" id="incidentCaption"></div></section>',
  reset() {D.q('incident').className='sc incident';},
  async play(s) {
    this.reset(); const safe=!!s.safe; const timing=s.timing||{};
    D.html('incidentTitle',s.text); D.text('incidentFile',safe?'policies.cedar · Approved policy':'server.js · Code review');
    const missing = D.q('missingLines');
    D.q('incidentCode').after(missing);
    D.html('incidentCode',(s.codeHtml||[]).map(row=>'<div class="incident-row">'+(row||'&nbsp;')+'</div>').join(''));
    D.html('incidentMissing',(s.missingHtml||[]).join('\n'));
    if (!safe) {
      const rows = D.qa('#incidentCode .incident-row');
      const blank = rows.find(row=>row.textContent.trim()==='');
      if (blank) blank.replaceWith(missing);
    }
    D.text('#incident .review-meta > span',safe?'readPost · author-only policy':'GET /posts/:id');
    D.text('#incident .review-pill',safe?'✓ Proven':'✓ Reviewed');
    D.text('incidentURL','app.example.com/posts/3'); D.text('postByline','Rin · You');
    D.text('postTitle','My next blog post'); D.text('postBody','A few ideas for next week. Still a work in progress.');
    D.text('draftLabel','DRAFT · ONLY YOU'); D.text('incidentStatus','GET /posts/3 → 200 OK'); D.html('incidentCaption','');
    D.cls('incident','on'); if(safe)D.cls('incident','safe');
    D.cls('incident','two-line-title',D.q('incidentTitle').getBoundingClientRect().height/D.scale()>85);
    await D.sleep((timing.settle??1.8)*1000); D.text('incidentURL','app.example.com/posts/7'); D.cls('incident','request');
    await D.sleep((timing.request??0.7)*1000);
    if(safe){D.cls('incident','denied');D.text('incidentStatus','GET /posts/7 → 403 Forbidden');}
    else {D.text('postByline','Aoi · Another author'); D.text('postTitle','Our next big announcement');D.text('postBody','We are preparing a new pricing plan. This draft is confidential until launch.');D.text('draftLabel','DRAFT · PRIVATE');D.text('incidentStatus','GET /posts/7 → 200 OK');D.cls('incident','leaked');}
    await D.sleep((timing.reveal??0.9)*1000); D.cls('incident','reveal'); D.html('incidentCaption',s.caption);
    await D.sleep((s.hold??5)*1000);if(!D.smooth){D.cls('incident','on',false);await D.sleep(300);}
  }
});
