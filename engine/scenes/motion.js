/* Reusable motion studies. drawAt() is deterministic: t is seconds, no CSS timers. */
D.register('motion',{
 mount:()=>'<section class="sc motion" id="motion"><div class="motion-stage" id="motionStage"></div></section>',
 reset(){this.generation=(this.generation||0)+1;this.key=null;D.cls('motion','on',false);},
 cursor:'<svg class="motion-cursor" id="motionCursor" viewBox="0 0 36 46"><path d="M3 2 30 28 18 29 12 41Z" fill="#17202b" stroke="white" stroke-width="3" stroke-linejoin="round"/></svg><div class="motion-click" id="motionClick"></div>',
 prepare(s){
  const key=JSON.stringify(s);if(this.key===key)return;this.key=key;
  const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const toolbar='<div class="motion-toolbar"><span class="motion-traffic">● ● ●</span><span class="motion-brand">'+esc(s.brand||'Orbit')+'</span><span class="right">Workspace</span></div>';
  if(s.preset==='auto-layout'){
   D.q('motion').style.background='#edece6';
   D.html('motionStage','<div class="motion-ui" id="motionUI"><div class="motion-window">'+toolbar+'<div class="motion-sidebar"><strong>Layers</strong><div>Overview</div><div>Components</div><div>Layout</div></div><div class="motion-canvas"><div class="layout-board"><div class="layout-card" id="layout0"><div class="shape"></div>Discover</div><div class="layout-card" id="layout1"><div class="shape"></div>Build</div><div class="layout-card" id="layout2"><div class="shape"></div>Ship</div><div class="motion-selection" id="motionSelection"></div></div></div><div class="motion-inspector"><strong>Layout</strong><div class="setting">Width <span style="float:right">Auto</span></div><div class="setting">Height <span style="float:right">Hug</span></div><div class="toggle" id="layoutToggle">↔　Auto layout</div><div class="setting">Spacing <span style="float:right">24</span></div></div></div>'+this.cursor+'</div>');
   (s.labels||['Discover','Build','Ship']).forEach((label,i)=>D.q('layout'+i).lastChild.textContent=label);
  }else if(s.preset==='spatial-carousel'){
   const colors=s.colors||['#d4f5b8','#ff715c','#a7a4ff','#f0c984','#6bcba6','#f0c6de','#89c3ef'];
   const words=(s.labels||['Form','Focus','Motion','Light','Rhythm','Space','Flow']).map(esc);
   const cards=colors.map((c,i)=>'<div class="motion-art" id="art'+i+'"><svg viewBox="0 0 340 460"><defs><linearGradient id="g'+i+'" x2="1" y2="1"><stop stop-color="'+c+'"/><stop offset="1" stop-color="'+colors[(i+2)%7]+'"/></linearGradient></defs><rect width="340" height="460" fill="url(#g'+i+')"/>'+Array.from({length:9},(_,j)=>'<ellipse cx="'+(85+j*23)+'" cy="'+(130+j*9)+'" rx="'+(32+j*11)+'" ry="'+(85+j*4)+'" fill="none" stroke="'+(i%2?'#28283b':'#ffffff')+'" stroke-width="'+(i%3===0?15:3)+'" opacity="'+(.2+j*.065)+'" transform="rotate('+(i*17-30)+' 170 230)"/>').join('')+'</svg><div class="art-label">'+words[i]+'</div></div>').join('');
   D.html('motionStage','<div class="motion-carousel"><div class="motion-ring">'+cards+'</div></div>');
  }else if(s.preset==='cursor-zoom'){
   D.q('motion').style.background='radial-gradient(ellipse at 20% 0,#f4d07c,transparent 65%),linear-gradient(135deg,#e2ad9e,#c34d83 70%,#633c8b)';
   const rows=s.rows||[['Project','Owner','Hours','Rate','Total'],['Research','Alex','12','80','960'],['Interface','Rin','18','80','1440'],['Prototype','Sam','8','80','640'],['Review','Alex','4','80','320'],['Delivery','Rin','6','80','480']];
   this.amounts=rows.slice(1).map(row=>Number(row[4]));
   const cells=rows.flatMap((row,r)=>row.map((v,c)=>'<div class="sheet-cell '+(r===0?'head':'')+' '+(c>1?'numeric':'')+'" '+(r&&c===4?'id="amount'+r+'"':'')+'>'+esc(v)+'</div>')).join('');
   D.html('motionStage','<div class="motion-ui sheet" id="motionUI"><div class="motion-window">'+toolbar+'<div class="sheet-bar"><span>File</span><span>Edit</span><span>View</span><span>Insert</span><span>Format</span><span>Data</span></div><div class="sheet-label">ƒx　= C2 * D2</div><div class="sheet-grid">'+cells+'</div><div class="sheet-range" id="sheetRange"></div><div class="sheet-menu" id="sheetMenu"><div>Number</div><div class="chosen">Currency　$</div><div>Percent</div><div>Date</div></div><div class="sheet-result" id="sheetResult">Sum: 3,840</div></div>'+this.cursor+'</div>');
  }else throw new Error('Unknown motion preset: '+s.preset);
 },
 drawAt(s,seconds){
  this.prepare(s);const p=Math.max(0,Math.min(1,seconds/(s.duration||6)));
  const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x);};
  const mix=(a,b,t)=>a+(b-a)*t;
  const pointer=(x,y,click)=>{const c=D.q('motionCursor');if(!c)return;c.style.left=x+'px';c.style.top=y+'px';c.style.transform='scale('+(1-.15*click)+')';const pulse=D.q('motionClick');pulse.style.left=(x-24)+'px';pulse.style.top=(y-24)+'px';pulse.style.opacity=click; pulse.style.transform='scale('+(1.3-click*.4)+')';};
  if(s.preset==='auto-layout'){
   const q=ease((p-.27)/.39),start=[[48,46],[318,142],[153,253]],end=[[80,115],[280,115],[480,115]];
   start.forEach((a,i)=>{const e=D.q('layout'+i);e.style.left=mix(a[0],end[i][0],q)+'px';e.style.top=mix(a[1],end[i][1],q)+'px';e.style.transform='rotate('+mix([-.8,.6,-.4][i],0,q)+'deg)';});
   const sel=D.q('motionSelection');Object.assign(sel.style,{left:mix(36,66,q)+'px',top:mix(34,101,q)+'px',width:mix(466,598,q)+'px',height:mix(394,188,q)+'px'});
   D.q('layoutToggle').classList.toggle('active',p>.29);const move=ease(p/.25);pointer(mix(890,1338,move),mix(690,430,move),Math.max(0,1-Math.abs(p-.27)/.045));
  }else if(s.preset==='spatial-carousel'){
   const turns=(s.turns??.36)*Math.PI*2*p;
   for(let i=0;i<7;i++){const a=(i/7*Math.PI*2+turns+Math.PI)%(2*Math.PI)-Math.PI;const x=Math.sin(a)*790,z=(Math.cos(a)-1)*610;const el=D.q('art'+i);el.style.transform='translate3d('+x+'px,0,'+z+'px) rotateY('+(a*180/Math.PI)+'deg)';el.style.opacity=clamp((Math.cos(a)+.7)/1.5);}
  }else{
   let z,targetX,targetY;
   if(p<.25){const q=ease(p/.25);z=mix(1,1.65,q);targetX=mix(800,1138,q);targetY=mix(500,495,q);}
   else if(p<.61){const q=ease((p-.39)/.22);z=1.65;targetX=mix(1138,650,q);targetY=mix(495,343,q);}
   else{const q=ease((p-.80)/.20);z=mix(1.65,1,q);targetX=mix(650,800,q);targetY=mix(343,500,q);}
   D.q('motionUI').style.transform='translate('+(800-z*targetX)+'px,'+(500-z*targetY)+'px) scale('+z+')';
   const drag=ease((p-.12)/.24);D.q('sheetRange').style.height=(66+264*drag)+'px';D.q('sheetMenu').style.display=p>.53&&p<.79?'block':'none';
   for(let i=1;i<=5;i++)D.text('amount'+i,(p>.75?'$':'')+this.amounts[i-1].toLocaleString('en-US'));
   D.text('sheetResult','Sum: '+(p>.75?'$':'')+this.amounts.reduce((a,b)=>a+b,0).toLocaleString('en-US'));
   const q=ease((p-.36)/.17),menu=ease((p-.55)/.12);pointer(mix(1320,700,q),mix(440+264*drag,258,q)+117*menu,Math.max(0,1-Math.abs(p-.73)/.035));
  }
 },
 async play(s){const generation=this.generation;const start=performance.now();D.cls('motion','on');const tick=()=>{if(this.generation!==generation)return;const t=(performance.now()-start)/1000;this.drawAt(s,t);if(t<(s.duration||6))D.later(tick,1000/30);};tick();await D.sleep((s.duration||6)*1000);this.drawAt(s,s.duration||6);if(!D.smooth)D.cls('motion','on',false);}
});
