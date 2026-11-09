/* Typography studies: deterministic transforms and a licensed variable font.
 * References and adaptations are recorded in templates/library/catalog.yaml. */
D.register('typography',{
  mount:()=>'<section class="sc typography" id="typography"><div class="type-stage" id="typeStage"></div></section>',
  reset(){this.key=null;this.generation=(this.generation||0)+1;D.cls('typography','on',false);},
  prepare(s){
    const key=JSON.stringify(s);if(key===this.key)return;this.key=key;
    if(!document.getElementById('demoTypeFont')){
      const style=document.createElement('style');style.id='demoTypeFont';
      style.textContent=`@font-face{font-family:'Demo Inter';font-style:normal;font-weight:100 900;src:url(${s.font_data}) format('woff2');font-display:block}`;
      document.head.appendChild(style);
    }
    const root=D.q('typeStage');root.replaceChildren();this.words=[];this.glyphs=[];this.lines=[];
    const glyphs=text=>[...new Intl.Segmenter(undefined,{granularity:'grapheme'}).segment(text)].map(x=>x.segment);
    if(s.preset==='type-punch'){
      for(const word of s.words){const el=document.createElement('div');el.className='type-punch-word';el.textContent=word;root.appendChild(el);this.words.push(el);}
    }else{
      const container=document.createElement('div');container.className=s.preset==='type-flight'?'type-flight-lines':'type-morph-lines';root.appendChild(container);
      for(const [row,text] of s.lines.entries()){
        const line=document.createElement('div');line.className=s.preset==='type-flight'?'type-flight-line':'type-morph-line';container.appendChild(line);this.lines.push(line);
        glyphs(text).forEach((character,index)=>{const el=document.createElement('span');el.className=s.preset==='type-flight'?'type-glyph':'type-morph-glyph';el.textContent=character===' '?'\u00a0':character;line.appendChild(el);this.glyphs.push({el,row,index,character});});
      }
    }
    this.ready=document.fonts.load('800 220px "Demo Inter"').then(()=>{
      this.words.forEach(el=>{el.style.fontSize=Math.min(s.font_size||240,240*1420/Math.max(1420,el.scrollWidth))+'px';});
      this.lines.forEach(line=>{
        const scale=Math.min(1,1400/line.scrollWidth);line.style.fontSize=(s.font_size|| (s.preset==='type-flight'?232:220))*scale+'px';
      });
      if(s.preset==='type-morph')this.glyphs.forEach(({el})=>el.style.width=el.getBoundingClientRect().width/(D.q('stage').getBoundingClientRect().width/1600)+'px');
    });
  },
  async drawAt(s,seconds){
    this.prepare(s);await this.ready;
    const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return 1-(1-x)**4;};
    const p=clamp(seconds/s.duration),stage=D.q('typography');
    if(s.preset==='type-punch'){
      const index=Math.min(s.words.length-1,Math.floor(p*s.words.length)),q=p*s.words.length-index;
      const light=index%2===1;stage.style.background=light?'#f4f2ed':'#08090b';stage.style.color=light?'#0b0c0f':'#f4f2ed';
      this.words.forEach((el,i)=>{
        el.style.opacity=i===index?1:0;
        const enter=ease(q/.25),leave=index===s.words.length-1?0:ease((q-.86)/.14);
        el.style.transform=`translateY(${48*(1-enter)-leave*85}px) scale(${1+.14*(1-enter)-leave*.06}) rotate(${(i%2?1:-1)*(1-enter)*2}deg)`;
        el.style.filter=`blur(${(1-enter)*7}px)`;
      });
    }else if(s.preset==='type-flight'){
      stage.style.background='#08090b';stage.style.color='#f4f2ed';
      this.glyphs.forEach(({el,row,index},i)=>{
        const stagger=ease((p-.025-i*.009)/.49),a=(i*2.399+row*.7),distance=1-stagger;
        const wave=Math.sin(clamp((p-.57-i*.009)/.25)*Math.PI);
        el.style.opacity=.55+.45*stagger;
        el.style.transform=`translate3d(${Math.cos(a)*(240+i%3*80)*distance}px,${Math.sin(a)*240*distance-wave*40}px,${(i%2?250:-450)*distance}px) rotateX(${Math.sin(a)*50*distance}deg) rotateY(${Math.cos(a)*45*distance}deg) rotateZ(${Math.sin(a*2)*60*distance}deg)`;
        el.style.filter=`blur(${distance*3}px)`;
      });
    }else{
      stage.style.background='#211c36';stage.style.color='#f5efeb';
      this.glyphs.forEach(({el,row,index})=>{
        const enter=ease((p+.025-row*.035)/.12),finish=ease((p-.78)/.16);
        const wave=(Math.sin(p*12-index*.64-row*1.3)+1)/2;
        const weight=(170+wave*710)*(1-finish)+820*finish;
        el.style.fontVariationSettings=`'wght' ${weight.toFixed(2)},'opsz' 32`;
        el.style.transform=`translateY(${(1-enter)*160}px) scaleY(${1+.13*Math.sin(p*10-index*.5)*(1-finish)})`;
        el.style.opacity=enter;
      });
    }
  },
  async play(s){
    const generation=this.generation;this.prepare(s);await this.ready;if(generation!==this.generation)return;
    D.cls('typography','on');const start=performance.now();
    const tick=async()=>{if(generation!==this.generation)return;const t=(performance.now()-start)/1000;await this.drawAt(s,t);if(t<s.duration&&generation===this.generation)D.later(tick,1000/30);};
    tick();await D.sleep(s.duration*1000);if(generation===this.generation)await this.drawAt(s,s.duration);
  }
});
