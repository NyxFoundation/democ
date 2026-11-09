/* Real screenshot textures, a deterministic camera, then one readable result.
 * The sample metric is explicitly a demo value, not measured publisher reach. */
D.register('press',{
  mount:()=>'<section class="sc press" id="press"><div class="press-stage" id="pressStage"><div class="press-space" id="pressSpace"></div><div class="press-shade" id="pressShade"></div><div class="press-metric" id="pressMetric"><div class="press-metric-number" id="pressNumber"></div><div class="press-metric-label" id="pressLabel"></div><div class="press-metric-copy" id="pressCopy"></div></div></div></section>',
  reset(){this.key=null;this.generation=(this.generation||0)+1;D.cls('press','on',false);},
  prepare(s){
    const key=JSON.stringify(s);if(key===this.key)return;this.key=key;
    if(!document.getElementById('demoTypeFont')){const style=document.createElement('style');style.id='demoTypeFont';style.textContent=`@font-face{font-family:'Demo Inter';font-style:normal;font-weight:100 900;src:url(${s.font_data}) format('woff2');font-display:block}`;document.head.appendChild(style);}
    const space=D.q('pressSpace');space.replaceChildren();this.cards=[];
    const count=s.preset==='press-cascade'?24:35;
    for(let i=0;i<count;i++){
      const card=document.createElement('div');card.className='press-card';const img=new Image();img.src=s.image_data[i%s.image_data.length];img.alt='';card.appendChild(img);space.appendChild(card);this.cards.push(card);
    }
    D.text('pressLabel',s.metric.label);D.text('pressCopy',s.copy||'');
    this.ready=Promise.all([document.fonts.load('800 220px "Demo Inter"'),...Array.from(space.querySelectorAll('img'),img=>img.decode())]);
  },
  async drawAt(s,seconds){
    this.prepare(s);await this.ready;
    const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x);};
    const p=clamp(seconds/s.duration),quiet=ease((p-.59)/.14),metric=ease((p-.72)/.12),space=D.q('pressSpace');
    if(s.preset==='press-cascade'){
      D.q('press').classList.remove('metric-light');
      const travel=1.6*p+2.9*p*p;
      this.cards.forEach((card,i)=>{
        const depth=((i*.22-travel+12)%5.3),z=700-depth*560;
        const a=i*2.399,spread=260+depth*65;
        const x=Math.cos(a)*spread,y=Math.sin(a)*spread*.58;
        const near=clamp((depth-.03)/.22),far=clamp((5.15-depth)/.7);
        card.style.opacity=near*far*(1-quiet*.94);
        card.style.transform=`translate(-50%,-50%) translate3d(${x}px,${y}px,${z}px) rotateZ(${Math.sin(a)*13}deg) rotateY(${Math.cos(a)*13}deg)`;
        card.style.filter=quiet>0?`blur(${quiet*8}px)`:'none';
      });
      // Blur each plane: filtering the parent flattens the 3D depth ordering.
      space.style.transform=`rotateZ(${-7+p*7}deg)`;space.style.filter='none';
      D.q('pressShade').style.opacity=.45+quiet*.55;
    }else{
      D.q('press').classList.add('metric-light');
      const expand=ease(p/.67);
      this.cards.forEach((card,i)=>{
        const col=i%7-3,row=Math.floor(i/7)-2;
        const x=col*660+(row%2)*150,y=row*490;
        card.style.opacity=(1-quiet*.84);
        card.style.transform=`translate(-50%,-50%) translate3d(${x}px,${y}px,0) rotateZ(${(i%3-1)*3}deg)`;
      });
      space.style.transform=`translate(${120-220*expand}px,${40-85*expand}px) scale(${1.25-.92*expand}) rotateZ(${-11+7*expand}deg)`;
      space.style.filter=`blur(${quiet*7}px)`;D.q('pressShade').style.opacity=0;
    }
    const number=ease((p-.72)/.14)*s.metric.value;
    const display=s.metric.format==='integer'?Math.round(number).toLocaleString('en-US'):(number/1000000).toFixed(1)+'M';
    D.text('pressNumber',display);
    const element=D.q('pressMetric');element.style.opacity=metric;element.style.transform=`translateY(${50*(1-metric)}px) scale(${.94+.06*metric})`;
  },
  async play(s){const generation=this.generation;this.prepare(s);await this.ready;if(generation!==this.generation)return;D.cls('press','on');const start=performance.now();const tick=async()=>{if(generation!==this.generation)return;const t=(performance.now()-start)/1000;await this.drawAt(s,t);if(t<s.duration&&generation===this.generation)D.later(tick,1000/30);};tick();await D.sleep(s.duration*1000);if(generation===this.generation)await this.drawAt(s,s.duration);}
});
