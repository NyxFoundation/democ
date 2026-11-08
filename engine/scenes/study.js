/* Short, deterministic domain studies. Values are synthetic, never live market/network data. */
D.register('study', {
  mount: () => '<section class="sc study" id="study"><canvas id="studyCanvas" width="1600" height="1000"></canvas></section>',
  reset() { this.key = null; this.generation = (this.generation || 0) + 1; D.cls('study', 'on', false); },
  prepare(s) {
    const key = JSON.stringify(s); if (key === this.key) return; this.key = key;
    this.ctx = D.q('studyCanvas').getContext('2d'); this.ready = Promise.resolve();
    if (s.preset === 'network-globe' && s.earth_map) {
      const image = new Image(); image.src = s.earth_map;
      this.ready = image.decode().then(() => {
        const temp = document.createElement('canvas'); temp.width = image.width; temp.height = image.height;
        const c = temp.getContext('2d'); c.drawImage(image, 0, 0);
        this.earth = {w:image.width, h:image.height, pixels:c.getImageData(0,0,image.width,image.height).data};
      });
    }
  },
  drawAt(s, seconds) {
    this.prepare(s); const c = this.ctx, p = Math.max(0,Math.min(1,seconds/(s.duration||4.8)));
    const ease = t => { t=Math.max(0,Math.min(1,t));return t*t*(3-2*t); };
    const lerp = (a,b,t) => a+(b-a)*t;
    const box = (x,y,w,h,r,fill,stroke) => {c.beginPath();c.roundRect(x,y,w,h,r);if(fill){c.fillStyle=fill;c.fill();}if(stroke){c.strokeStyle=stroke;c.stroke();}};
    const text = (value,x,y,size=24,color='#d8dfe6',font='monospace') => {c.font=`${size}px ${font}`;c.fillStyle=color;c.fillText(value,x,y);};
    c.clearRect(0,0,1600,1000);c.fillStyle='#101317';c.fillRect(0,0,1600,1000);
    if (s.preset === 'terminal-flow') {
      c.fillStyle='#e8e6dd';c.fillRect(0,0,1600,1000);
      c.shadowColor='#111a2230';c.shadowBlur=85;c.shadowOffsetY=35;box(145,155,1310,690,22,'#151a1d');c.shadowBlur=0;c.shadowOffsetY=0;
      ['#d06f68','#d1b36d','#79a686'].forEach((color,i)=>{c.beginPath();c.fillStyle=color;c.arc(185+i*27,190,7,0,Math.PI*2);c.fill();});
      text('release',760,199,18,'#65737e');
      const command='orbit deploy';const typed=Math.floor(ease(p/.19)*command.length);
      text('›',204,285,29,'#a6ddaa');text(command.slice(0,typed),244,285,29,'#e3e7e7');
      if(p<.2)box(245+typed*17.5,261,15,29,1,'#cce5c2');
      if(p>.21){text('Choose an environment',204,365,28,'#e3e7e7');const choice=p>.44?1:0;
        ['Preview','Production'].forEach((name,i)=>{if(choice===i)box(196,394+i*60,1188,52,5,'#cce5c212');text(choice===i?'›':' ',211,430+i*60,26,'#b5df9f');text(name,254,430+i*60,26,choice===i?'#d6edbe':'#707c80');});
      }
      if(p>.58){box(192,337,1208,200,0,'#151a1d');const stages=['Build','Checks','Publish'];stages.forEach((name,i)=>{
        const progress=Math.max(0,Math.min(1,(p-.58-i*.08)/.085));text(progress>=1?'✓':'·',211,380+i*65,27,progress>=1?'#b5df9f':'#65737e');text(name,254,380+i*65,27,'#dfe7e8');box(590,365+i*65,700,4,2,'#2c383d');box(590,365+i*65,Math.max(1,700*progress),4,2,'#aed99f');
      });}
      if(p>.89){text('Ready',211,668,31,'#c7e8af');text('preview.orbit.app',211,723,24,'#8c9eaa');}
    } else if (s.preset === 'code-diff') {
      const background=c.createRadialGradient(800,350,0,800,500,1000);background.addColorStop(0,'#24302f');background.addColorStop(1,'#101719');c.fillStyle=background;c.fillRect(0,0,1600,1000);
      box(115,115,1370,770,18,'#151c21','#354248');box(115,115,1370,62,18,'#1c252b');text('api.ts',171,155,21,'#a6b6bd');
      const code=['export async function loadProjects() {',"  return fetch('/api/projects');",'}'];
      const replaced=['export async function loadProjects() {',"  const response = await fetch('/api/projects');",'  return response.json();','}'];
      const q=ease((p-.22)/.34),lines=p>.46?replaced:code;
      if(p>.2){c.globalAlpha=.8*(1-q);box(185,307,1210,53,4,'#723e3c');c.globalAlpha=1;}
      if(p>.4){c.globalAlpha=q;box(185,307,1210,112,4,'#21483b');c.globalAlpha=1;}
      lines.forEach((line,i)=>{text(String(i+1),150,284+i*58,21,'#5b6d79');const y=284+i*58;
        const words=line.split(/(export|function|return|true|false)/g);let x=207;
        words.forEach(word=>{const color=/^(export|function|return)$/.test(word)?'#c4b4e5':'#d3dee0';text(word,x,y,29,color);x+=c.measureText(word).width;});
      });
      const cursor=lerp(207,870,ease(p/.17));if(p<.22)box(cursor,292,2,34,0,'#dcead9');
      if(p>.67){box(153,685,1290,152,8,'#10171c');text('checks',185,724,19,'#7e919e');
        text('✓  request routing',185,771,24,'#b1d69d');if(p>.78)text('✓  parses JSON',737,771,24,'#b1d69d');
      }
    } else if (s.preset === 'market-chart') {
      const zoom=1+.14*ease((p-.4)/.6);c.save();c.translate(800,500);c.scale(zoom,zoom);c.translate(-800,-500);
      box(115,130,1370,740,20,'#151b26','#344051');text('ACME',163,191,25,'#e7ebf2');text('1D',1330,191,22,'#9aa8bd');
      const vals=Array.from({length:70},(_,i)=>170+Math.sin(i*.31)*35+Math.sin(i*.77)*14+i*2.6);
      const shown=24+Math.floor(p*45),last=vals[shown-1],baseline=700;
      for(let i=0;i<6;i++){const y=280+i*90;c.beginPath();c.moveTo(160,y);c.lineTo(1432,y);c.strokeStyle='#c5d5e60c';c.stroke();}
      const start=Math.max(0,shown-52),span=52,step=1220/span;
      for(let i=start;i<shown;i++){
        const x=178+(i-start)*step,open=vals[i],close=vals[i]+Math.sin(i*1.9+1)*15+3,high=Math.max(open,close)+8,low=Math.min(open,close)-9;
        const color=close>open?'#61c6b5':'#d88185';c.strokeStyle=color;c.lineWidth=1.5;c.beginPath();c.moveTo(x,baseline-high);c.lineTo(x,baseline-low);c.stroke();box(x-6,baseline-Math.max(open,close),12,Math.max(3,Math.abs(close-open)),2,color);
        box(x-7,792-Math.abs(Math.sin(i*.64))*48,14,Math.abs(Math.sin(i*.64))*48+8,1,color+'45');
      }
      const glow=c.createLinearGradient(0,350,0,730);glow.addColorStop(0,'#67d4d42e');glow.addColorStop(1,'#67d4d400');
      c.beginPath();for(let i=start;i<shown;i++){const x=178+(i-start)*step,y=baseline-vals[i]-70;i===start?c.moveTo(x,y):c.lineTo(x,y);}c.strokeStyle='#78d7e1';c.lineWidth=3;c.shadowColor='#78d7e1';c.shadowBlur=12;c.stroke();c.shadowBlur=0;
      const x=178+(shown-1-start)*step,y=baseline-last;c.setLineDash([4,6]);c.strokeStyle='#b6c5d954';c.lineWidth=1;c.beginPath();c.moveTo(x,225);c.lineTo(x,827);c.moveTo(160,y);c.lineTo(1410,y);c.stroke();c.setLineDash([]);
      box(Math.min(x+13,1290),y-18,100,36,5,'#9cdcd5');text((last/10+70).toFixed(2),Math.min(x+24,1300),y+7,20,'#152226');c.restore();
    } else if (s.preset === 'network-globe') {
      const cx=800,cy=500,radius=300,angle=p*.43;
      const bg=c.createRadialGradient(cx,cy,200,cx,cy,600);bg.addColorStop(0,'#152e3a');bg.addColorStop(1,'#080d16');c.fillStyle=bg;c.fillRect(0,0,1600,1000);
      if(this.earth){
        const size=450,temp=this.sphereCanvas||(this.sphereCanvas=document.createElement('canvas'));temp.width=size;temp.height=size;
        const ctx=temp.getContext('2d'),im=ctx.createImageData(size,size),e=this.earth;
        for(let y=0;y<size;y++)for(let x=0;x<size;x++){
          const nx=(x-size/2)/(size/2),ny=(y-size/2)/(size/2),d=nx*nx+ny*ny;if(d>1)continue;
          const nz=Math.sqrt(1-d),u=((Math.atan2(nx,nz)/(2*Math.PI)+.58+angle) % 1+1)%1,v=.5+Math.asin(ny)/Math.PI;
          const src=(Math.min(e.h-1,Math.floor(v*e.h))*e.w+Math.floor(u*e.w))*4,dst=(y*size+x)*4;
          const light=.24+.68*Math.max(0,-.3*nx-.3*ny+.9*nz);
          im.data[dst]=e.pixels[src]*light;im.data[dst+1]=e.pixels[src+1]*light;im.data[dst+2]=e.pixels[src+2]*light;im.data[dst+3]=255;
        }
        ctx.putImageData(im,0,0);c.drawImage(temp,cx-radius,cy-radius,radius*2,radius*2);
      }
      c.beginPath();c.arc(cx,cy,radius,0,Math.PI*2);c.strokeStyle='#7abfdd55';c.lineWidth=3;c.shadowColor='#64b8e7';c.shadowBlur=23;c.stroke();c.shadowBlur=0;
      const points=Array.from({length:22},(_,i)=>{const longitude=i*.91+angle*Math.PI*2;const latitude=Math.sin(i*2.2)*.9;return [Math.sin(longitude)*Math.cos(latitude),Math.sin(latitude),Math.cos(longitude)*Math.cos(latitude)];});
      const project=(v,h=1)=>[cx+v[0]*radius*h,cy-v[1]*radius*h,v[2]];
      for(let i=0;i<28;i++){
        const a=points[i%22],b=points[(i*7+9)%22];if(a[2]<-.2&&b[2]<-.2)continue;
        c.beginPath();for(let j=0;j<=40;j++){const t=j/40,v=a.map((x,k)=>lerp(x,b[k],t)),length=Math.hypot(...v);const q=project(v.map(x=>x/Math.max(.1,length)),1+.24*Math.sin(Math.PI*t));j?c.lineTo(q[0],q[1]):c.moveTo(q[0],q[1]);}
        c.strokeStyle='#68c3dd'+(a[2]<0?'22':'5c');c.lineWidth=1.2;c.stroke();
        const t=(p*2.4+i*.19)%1,v=a.map((x,k)=>lerp(x,b[k],t)),length=Math.hypot(...v),q=project(v.map(x=>x/Math.max(.1,length)),1+.24*Math.sin(Math.PI*t));
        if(q[2]>0){c.beginPath();c.fillStyle='#c9fbf0';c.arc(q[0],q[1],2.4,0,Math.PI*2);c.fill();}
      }
      points.forEach(v=>{if(v[2]<0)return;const q=project(v);c.beginPath();c.arc(q[0],q[1],3.2,0,Math.PI*2);c.fillStyle='#c9e9e7';c.fill();});
    }
  },
  async play(s) {
    const generation=this.generation;this.prepare(s);await this.ready;if(generation!==this.generation)return;
    D.cls('study','on');const start=performance.now();const tick=()=>{if(generation!==this.generation)return;const t=(performance.now()-start)/1000;this.drawAt(s,t);if(t<(s.duration||4.8))D.later(tick,1000/30);};
    tick();await D.sleep((s.duration||4.8)*1000);this.drawAt(s,s.duration||4.8);
  }
});
