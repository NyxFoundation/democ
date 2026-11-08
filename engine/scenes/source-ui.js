/* Source-based studies. Upstream implementations, licenses and versions live in
 * templates/library/source-ui. The app content/data are fixed demonstration fixtures. */
D.SourceStudy = {
  icon(name, extra='') { return `<i class="codicon codicon-${name} ${extra}" aria-hidden="true"></i>`; },
  async prepare(s) {
    this.term?.dispose(); this.editor?.dispose(); this.diff?.dispose();
    this.network?.dispose();this.network=null;
    this.models?.forEach(m=>m.dispose()); this.charts?.forEach(c=>c.remove());
    this.term=this.editor=this.diff=null;this.models=[];this.charts=[];
    this.root=D.q('sourceUi');this.root.className='source-ui '+s.preset;this.root.innerHTML='';
    this.phase=-1;
    if(s.preset==='terminal-flow')await this.terminal();
    else if(s.preset==='code-diff')await this.code();
    else if(s.preset==='market-chart')await this.market();
    else if(s.preset==='network-globe')this.network=await D.NetworkStudy.create(this.root,s);
  },
  async terminal() {
    this.root.innerHTML='<div class="gum-screen"><div class="gum-terminal"></div></div>';
    await document.fonts.load('44px "JetBrains Mono"');
    const {Terminal}=DemoSourceUI;
    const extendedAnsi=Array.from({length:240},(_,n)=>{const a=[0,95,135,175,215,255];return n<216?'#'+[a[Math.floor(n/36)],a[Math.floor(n/6)%6],a[n%6]].map(v=>v.toString(16).padStart(2,'0')).join(''):'#'+Array(3).fill((8+(n-216)*10).toString(16).padStart(2,'0')).join('');});
    extendedAnsi[212-16]='#b47e9e';
    this.term=new Terminal({cols:80,rows:24,fontSize:44,lineHeight:1.03,letterSpacing:2.7,
      fontFamily:'"JetBrains Mono", "DejaVu Sans Mono", monospace',fontWeight:'400',
      cursorBlink:false,allowTransparency:false,scrollback:0,convertEol:false,
      theme:{background:'#171717',foreground:'#eeeeec',cursor:'#00c4a7',selectionBackground:'#444444',extendedAnsi}});
    this.term.open(this.root.querySelector('.gum-terminal'));
    this.term.options.cursorInactiveStyle='block';
    await document.fonts.ready;
  },
  async code() {
    const i=(name)=>this.icon(name);
    const tree=[['chevron-right','.copilot',0],['chevron-right','public',0],['chevron-down','src',0],
      ['chevron-right','components',1],['chevron-right','data',1],['','App.jsx',1],['','main.jsx',1],
      ['','search.js',1],['','styles.css',1],['chevron-right','tests',0],['','.gitignore',0],
      ['','index.html',0],['','package.json',0],['','README.md',0],['','vite.config.js',0]];
    this.root.innerHTML=`<div class="monaco-workbench source-workbench">
      <div class="workbench-titlebar"><span class="vscode-brand">${i('vscode')}</span>
        <nav>File<span>Edit</span><span>Selection</span><span>View</span><span>…</span></nav>
        <div class="titlebar-center">${i('arrow-left')}${i('arrow-right')}<div>Trail Atlas</div>${i('copilot')}${i('chevron-down')}</div>
        <div class="window-tools">${i('layout-sidebar-left')}${i('layout-panel')}${i('layout-sidebar-right')}<b></b>${i('chrome-minimize')}${i('chrome-maximize')}${i('chrome-close')}</div>
      </div>
      <aside class="activitybar"><div>${['files','search','source-control','debug-alt','extensions'].map((n,j)=>`<span class="${j===0?'selected':''}">${i(n)}</span>`).join('')}</div><div>${i('account')}${i('settings-gear')}</div></aside>
      <aside class="explorer"><header><b>trail-atlas</b><span>${i('new-file')}${i('new-folder')}${i('refresh')}${i('collapse-all')}${i('ellipsis')}</span></header>
        <div class="explorer-tree">${tree.map(([icon,name,depth])=>`<div class="tree-row ${name==='App.jsx'?'selected':''}" style="padding-left:${21+depth*15}px">${icon?i(icon):'<i class="tree-spacer"></i>'}<span>${name}</span></div>`).join('')}</div></aside>
      <div class="editor-group"><div class="editor-tabs"><span>App.jsx <small>×</small></span><span class="active">search.js <small>×</small></span><div>${i('split-horizontal')}${i('ellipsis')}</div></div>
        <div class="breadcrumbs">src ${i('chevron-right')} search.js ${i('chevron-right')}</div>
        <div class="source-editor" id="sourceCodeEditor"></div><div class="source-editor source-diff" id="sourceDiffEditor"></div>
        <div class="edit-review">${i('arrow-up')}${i('arrow-down')}<button>Keep</button><span>Undo</span><span>1 of 5</span>${i('close')}</div>
      </div>
      <aside class="chat-panel"><header><b>Chat</b><span>${i('add')}${i('chevron-down')}${i('gear')}${i('ellipsis')}${i('screen-full')}${i('close')}</span></header>
        <div class="interactive-session"><div class="chat-scroll">
          <div class="chat-request">${i('arrow-left')}<b>Plan how to make trail search ignore case and extra spaces.</b>${i('split-horizontal')}</div>
          <div class="chat-finished">Finished with 2 steps</div>
          <p class="chat-intro"><code>searchTrails</code> compares raw text, so <code>PINE</code> misses Pine Ridge Loop. Here’s a plan to normalize the query and trail names and add a regression test.</p>
          <div class="plan-card"><header><b>Case- and space-insensitive trail search</b><span>Open Full Plan ${i('chevron-down')}</span></header>
            <p>Normalize the query in <code>searchTrails</code> so <code>PINE</code> and <code>pine</code> both find Pine Ridge Loop.</p>
            <b>Steps</b><ol><li>Add a <code>normalize</code> helper to <code>src/search.js</code>.</li><li>Normalize the query and each <code>trail.name</code>.</li><li>Trim the query in the empty-state message.</li><li>Add an “ignores case and extra spaces” test.</li></ol>
            <b>Verification</b><ol><li>Run <code>npm test</code> and confirm both tests pass.</li></ol>
            <footer><button class="implement">Implement ${i('chevron-down')}</button><button>Reject</button></footer>
          </div>
          <div class="chat-execution"><div class="chat-bubble">Plan how to make trail search ignore case and extra spaces.</div>
            <p>Normalize the query in <code>searchTrails</code> so <code>PINE</code> and <code>pine</code> both find Pine Ridge Loop.</p>
            <b>Steps</b><ol><li>Add a <code>normalize</code> helper to <code>src/search.js</code>.</li><li>Normalize the query and each <code>trail.name</code>.</li><li>Trim the query in the empty-state message.</li><li>Add an “ignores case and extra spaces” test.</li></ol>
            <b>Verification</b><p>1. Run <code>npm test</code> and confirm both tests pass.</p><div class="plan-status">Open full plan file (plan.md)</div>
            <div class="file-change"><span>Running <code>npm test</code> ${i('chevron-down')}</span></div>
            <div class="test-command"><code>npm test</code></div>
          </div>
        </div><div class="interactive-input-part"><div class="chat-input-container"><div class="chat-attached-context">${i('add')}<span><em>JS</em> search.js</span></div><div class="chat-editor-container">Chat with Copilot</div><div class="chat-input-toolbars"><span>${i('add')} ${i('flame')} Agent ${i('copilot')} Auto</span>${i('debug-stop')}</div></div><div class="chat-secondary-toolbar">${i('list-tree')} Plan <span>Manual permissions</span></div></div></div>
      </aside></div><svg class="source-pointer" width="19" height="25" viewBox="0 0 19 25"><path d="M2 1v20l5-5 4 8 3-2-4-8 7-1z" fill="white" stroke="#101210" stroke-width="1.3"/></svg>`;
    const {monaco,theme}=DemoSourceUI;
    const vars=this.root.querySelector('.monaco-workbench').style;
    const themeColors=Object.fromEntries(Object.entries(theme.colors).filter(([,value])=>typeof value==='string'));
    Object.entries(themeColors).forEach(([name,value])=>vars.setProperty('--vscode-'+name.replaceAll('.','-'),value));
    // The reference film has a subtle green tint over the GitHub Dark theme.
    const colors={...themeColors,'editor.background':'#0e140f','editor.foreground':'#d8ddd8',
      'editorLineNumber.foreground':'#58615b','editor.lineHighlightBackground':'#22262a',
      'diffEditor.insertedTextBackground':'#255a2c80','diffEditor.insertedLineBackground':'#234e28',
      'diffEditor.removedTextBackground':'#63262a70','diffEditor.removedLineBackground':'#3b1f22'};
    const rule=(scope,fallback)=>theme.tokenColors.find(t=>[t.scope].flat().includes(scope))?.settings.foreground?.slice(1)||fallback;
    monaco.editor.defineTheme('source-github',{base:'vs-dark',inherit:true,colors,rules:[
      {token:'keyword',foreground:rule('keyword','ff7b72')},
      {token:'string',foreground:rule('string','a5d6ff')},
      {token:'number',foreground:rule('constant.numeric','79c0ff')},
      {token:'identifier',foreground:'d8ddd8'}, {token:'comment',foreground:'6e7681'},
      {token:'delimiter',foreground:'d8ddd8'}]});
    const original=`const LEVELS = ['Easy', 'Moderate', 'Hard'];\n\nexport function searchTrails(trails, query) {\n  const matches = trails\n    .filter(trail =>\n      trail.name.includes(query),\n    )\n    .sort((a, b) => a.distance - b.distance);\n\n  const message = matches.length\n    ? ''\n    : \`No trails match \${query}\`;\n\n  return { matches, message };\n}\n\nexport function sortByDifficulty(trails) {\n  return [...trails].sort(\n    (a, b) =>\n      LEVELS.indexOf(a.difficulty) -\n      LEVELS.indexOf(b.difficulty),\n  );\n}\n\nexport function describeTrail(trail) {\n  return \`\${trail.name} · \${trail.distance} km\`;\n}\n`;
    const modified=original.replace('\n\nexport function searchTrails',
      '\n\nfunction normalize(text) {\n  return text.trim().toLowerCase();\n}\n\nexport function searchTrails')
      .replace('  const matches = trails', "  const term = normalize(query);\n  if (!term) {\n    return { matches: trails, message: '' };\n  }\n\n  const matches = trails")
      .replace('trail.name.includes(query)','normalize(trail.name).includes(term)')
      .replace('No trails match ${query}','No trails match ${query.trim()}');
    const model=monaco.editor.createModel(original,'javascript');
    const changed=monaco.editor.createModel(modified,'javascript');this.models=[model,changed];
    const opts={theme:'source-github',fontFamily:'Consolas, "Courier New", monospace',fontSize:17.8,lineHeight:25,
      minimap:{enabled:false},readOnly:true,scrollBeyondLastLine:false,automaticLayout:false,
      lineNumbersMinChars:4,lineDecorationsWidth:20,padding:{top:4},glyphMargin:false,folding:false,
      scrollbar:{vertical:'hidden',horizontal:'hidden'},renderLineHighlight:'all',overviewRulerLanes:0,
      stickyScroll:{enabled:false},guides:{indentation:true},occurrencesHighlight:'off',selectionHighlight:false,
      contextmenu:false,renderValidationDecorations:'off',bracketPairColorization:{enabled:false}};
    this.editor=monaco.editor.create(D.q('sourceCodeEditor'),{...opts,model});
    this.diff=monaco.editor.createDiffEditor(D.q('sourceDiffEditor'),{...opts,renderSideBySide:false,
      renderOverviewRuler:false,enableSplitViewResizing:false,originalEditable:false,diffAlgorithm:'advanced',
      hideUnchangedRegions:{enabled:false},renderGutterMenu:false});
    this.diff.setModel({original:model,modified:changed});
    this.editor.layout({width:665,height:812});this.diff.layout({width:665,height:812});
    await Promise.race([new Promise(resolve=>this.diff.onDidUpdateDiff(resolve)),new Promise(r=>setTimeout(r,500))]);
    await document.fonts.ready;
  },
  async market() {
    const toolbar=['cursor','add','graph-line','symbol-ruler','pencil','symbol-text','smiley','ruler','zoom-in','magnet','lock','eye','trash'];
    const i=(name)=>this.icon(name);
    const panel=(id,symbol)=>`<div class="tv-panel ${id}"><div class="tv-topbar"><b>${symbol}</b><span>1h</span><span>${i('graph-line')}</span><span>Indicators</span><span>Alert</span><span>Replay</span><span class="tv-tools">${i('undo')}${i('redo')}${i('settings-gear')}${i('screen-full')}${i('device-camera')}</span></div><div class="tv-leftbar">${toolbar.map(n=>i(n)).join('')}</div><div class="tv-legend">${symbol} · 1h · BINANCE <span>O 93,751.03　H 94,207.74　L 93,128.10　C 93,962.43</span></div><div class="tv-native-chart" id="${id}"></div><div class="tv-bottom"><span>1D　5D　1M　3M　6M　YTD　1Y　5Y　All</span><span>10:04:55 (UTC)　%　log　auto</span></div></div>`;
    this.root.innerHTML=`<div class="market-letterbox"><div class="market-set"><div class="neon-horizon"><svg viewBox="0 0 1600 650" preserveAspectRatio="none"><defs><filter id="neon"><feGaussianBlur stdDeviation="8"/></filter></defs>${[0,1,2,3,4].map(n=>`<path d="M-180 ${-30+n*33} Q800 ${820+n*20} 1780 ${-30+n*33}"/>`).join('')}</svg></div><div class="market-floor"></div><div class="market-camera"><div class="chart-stack">${panel('tv-main','BTCUSDT')}${panel('tv-second','BTCUSDT')}${panel('tv-third','ETHUSDT')}</div></div><div class="market-vignette"></div></div></div>`;
    const {charts}=DemoSourceUI;
    this.primary=[];
    let seed=10391,price=93350;
    const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
    const data=Array.from({length:155},(_,n)=>{price+=(n<34?6:n<51?-7:n<88?13:n<118?-4:8)+(random()-.49)*105;return {time:1748736000+n*3600,value:price};});
    ['tv-main','tv-second','tv-third'].forEach((id,j)=>{
      const container=D.q(id);
      const chart=charts.createChart(container,{width:1038,height:458,
        layout:{background:{type:charts.ColorType.Solid,color:'#0d101b'},textColor:'#a7a9b7',fontSize:12,fontFamily:'Arial',attributionLogo:true,
          panes:{separatorColor:'#202334',separatorHoverColor:'#202334',enableResize:false}},
        grid:{vertLines:{color:'#20233355'},horzLines:{color:'#20233355'}},
        rightPriceScale:{borderColor:'#2c2c40',minimumWidth:74},
        timeScale:{borderColor:'#2c2c40',timeVisible:true,secondsVisible:false,barSpacing:7,rightOffset:3},
        crosshair:{mode:charts.CrosshairMode.Normal,vertLine:{color:'#777a9b88',labelVisible:false},horzLine:{color:'#777a9b88',labelVisible:true}},
        handleScale:false,handleScroll:false});
      const main=chart.addSeries(charts.AreaSeries,{lineColor:j===2?'#8d82ff':'#38dbe5',lineWidth:2,
        topColor:'#1ec8d82b',bottomColor:'#1ec8d800',priceLineVisible:false,lastValueVisible:true,crosshairMarkerVisible:false});
      main.setData(data.map((d,n)=>({...d,value:d.value+(j===1?Math.sin(n*.37)*125:0)})));
      const candles=chart.addSeries(charts.CandlestickSeries,{upColor:'#26a69a80',downColor:'#ef535080',
        wickUpColor:'#26a69a88',wickDownColor:'#ef535088',borderVisible:false,priceLineVisible:false,lastValueVisible:false});
      candles.setData(data.map((d,n)=>({time:d.time,open:d.value-20*Math.sin(n),close:d.value+18*Math.cos(n*.7),high:d.value+53,low:d.value-42})));
      const comparison=chart.addSeries(charts.LineSeries,{color:'#cc557b88',lineWidth:1,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});
      comparison.setData(data.map((d,n)=>({...d,value:d.value-90+Math.sin(n*.27)*40})));
      const vol=chart.addSeries(charts.HistogramSeries,{color:'#3ec5d855',priceLineVisible:false,lastValueVisible:false},1);
      vol.setData(data.map((d,n)=>({time:d.time,value:200+Math.sin(n*.43)*100+Math.cos(n*.79)*80,color:n%3?'#31a8ac66':'#e0526855'})));
      const rsi=chart.addSeries(charts.LineSeries,{color:'#38cead',lineWidth:1,priceLineVisible:false,lastValueVisible:true,crosshairMarkerVisible:false},2);
      rsi.setData(data.map((d,n)=>({time:d.time,value:45+Math.sin(n*.17)*18+Math.sin(n*.49)*9})));
      if(j===1||j===2){['#e346ac','#e6b02a','#8a6df1'].forEach((color,k)=>{const line=chart.addSeries(charts.LineSeries,{color,lineWidth:2,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});line.setData(data.map((d,n)=>({...d,value:93550+Math.sin(n*.11+k*.5)*100+k*35+n*.9})));});}
      chart.panes()[0].setHeight(310);chart.panes()[1].setHeight(57);chart.panes()[2].setHeight(72);
      chart.timeScale().fitContent();this.charts.push(chart);this.primary.push({series:main,data});
    });
    await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    this.charts.forEach((chart,j)=>{
      const {series,data}=this.primary[j],path=data.map((d,n)=>`${n?'L':'M'}${chart.timeScale().timeToCoordinate(d.time)},${series.priceToCoordinate(d.value)}`).join(' ');
      D.q(['tv-main','tv-second','tv-third'][j]).insertAdjacentHTML('beforeend',`<svg class="chart-line-bloom" width="1038" height="458"><path d="${path}" fill="none" stroke="${j===2?'#8d82ff':'#38dbe5'}" stroke-width="2.2"/></svg>`);
    });
  },
  drawAt(s,seconds) {
    if(s.preset==='network-globe')return this.network.drawAt(seconds,s.duration);
    const p=Math.max(0,Math.min(1,seconds/s.duration)),ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
    if(s.preset==='terminal-flow'){
      const t=seconds+.1,events=DemoSourceUI.gum.events.filter(([at])=>at<=t);
      this.term.reset();
      return new Promise(resolve=>this.term.write(events.map(([,data])=>data).join(''),()=>{
        this.term.scrollToTop();resolve();
      }));
    }
    if(s.preset==='code-diff'){
      const phase=p<.36?0:p<.58?1:2;
      this.root.dataset.phase=phase;
      this.root.style.setProperty('--plan-opacity',1-ease((p-.31)/.07));
      const approach=ease((p-.23)/.11),leave=ease((p-.38)/.12);
      this.root.querySelector('.source-pointer').style.transform=`translate(${1560-480*approach+480*leave}px,${875-182*approach+182*leave}px)`;
      if(phase!==this.phase){
        this.phase=phase;
        if(phase===2){this.diff.getModifiedEditor().setScrollTop(0);this.diff.getModifiedEditor().render(true);}
      }
      return;
    }
    if(s.preset==='market-chart'){
      const push=ease((p-.13)/.38),slide=ease((p-.53)/.43);
      const camera=this.root.querySelector('.market-camera');
      camera.style.transform=`translate3d(${-70-185*push-780*slide}px,${34-40*push-12*slide}px,0) scale(${.76+1.9*push-.5*slide})`;
      const stack=this.root.querySelector('.chart-stack');
      stack.style.transform=`rotateX(${-5+7*slide}deg) rotateY(${-16+24*slide}deg) rotateZ(${-2+3*slide}deg)`;
      this.root.querySelector('.neon-horizon').style.opacity=1-.83*push;
      this.root.querySelector('.tv-third').style.opacity=.15+.85*ease((p-.27)/.3);
      this.charts.forEach((chart,j)=>{
        const {series,data}=this.primary[j],idx=Math.min(151,110+Math.floor(p*40));
        chart.setCrosshairPosition(data[idx].value,data[idx].time,series);
      });
      return new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    }
  }
};
