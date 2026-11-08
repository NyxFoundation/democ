/* Deterministic playback of source-based UI and WebGL studies. */
D.register('study', {
  mount: () => '<section class="sc study" id="study"><div id="sourceUi"></div></section>',
  reset() { this.key=null;this.generation=(this.generation||0)+1;D.cls('study','on',false); },
  prepare(s) {
    const key=JSON.stringify(s);if(key===this.key)return;this.key=key;
    this.ready=D.SourceStudy.prepare(s);
  },
  drawAt(s,seconds) { this.prepare(s);return this.ready.then(()=>D.SourceStudy.drawAt(s,seconds)); },
  async play(s) {
    const generation=this.generation;this.prepare(s);await this.ready;if(generation!==this.generation)return;
    D.cls('study','on');const start=performance.now();
    const tick=async()=>{
      if(generation!==this.generation)return;
      const t=(performance.now()-start)/1000;await this.drawAt(s,t);
      if(generation===this.generation&&t<(s.duration||4.8))D.later(tick,1000/30);
    };
    tick();await D.sleep((s.duration||4.8)*1000);
    if(generation===this.generation)await this.drawAt(s,s.duration||4.8);
  }
});
