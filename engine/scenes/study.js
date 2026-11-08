/* Short, deterministic domain studies. Values are synthetic, never live market/network data. */
D.register('study', {
  mount: () => '<section class="sc study" id="study"><canvas id="studyCanvas" width="1600" height="1000"></canvas><div id="sourceUi" hidden></div></section>',
  reset() { this.key = null; this.generation = (this.generation || 0) + 1; D.cls('study', 'on', false); },
  prepare(s) {
    const key = JSON.stringify(s); if (key === this.key) return; this.key = key;
    this.source = ['terminal-flow','code-diff','market-chart'].includes(s.preset);
    D.q('sourceUi').hidden = !this.source; D.q('studyCanvas').hidden = this.source;
    if (this.source) { this.ready = D.SourceStudy.prepare(s); return; }
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
    this.prepare(s); if(this.source)return this.ready.then(()=>D.SourceStudy.drawAt(s,seconds));
    const c = this.ctx, p = Math.max(0,Math.min(1,seconds/(s.duration||4.8)));
    const lerp = (a,b,t) => a+(b-a)*t;
    c.clearRect(0,0,1600,1000);c.fillStyle='#101317';c.fillRect(0,0,1600,1000);
    if (s.preset === 'network-globe') {
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
    D.cls('study','on');const start=performance.now();const tick=async()=>{if(generation!==this.generation)return;const t=(performance.now()-start)/1000;await this.drawAt(s,t);if(generation===this.generation&&t<(s.duration||4.8))D.later(tick,1000/30);};
    tick();await D.sleep((s.duration||4.8)*1000);if(generation===this.generation)await this.drawAt(s,s.duration||4.8);
  }
});
