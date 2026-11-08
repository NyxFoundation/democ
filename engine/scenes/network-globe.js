/* Port of XNOHub's Three.js globe/material, latLongToVector3 and great-circle
 * geometry. Derived under MIT; original notice retained in source-ui/xno.
 * React/live streams are replaced by deterministic timestamps and fixtures. */
D.NetworkStudy = {
  async create(root,s) {
    const {THREE:T,EffectComposer,RenderPass,UnrealBloomPass,OutputPass,networkNodes}=DemoSourceUI;
    root.innerHTML=`<div class="xno-window"><div class="xno-canvas"></div>
      <div class="xno-brand"><span>ӾNO</span>Hub</div><div class="xno-controls"><button>♧ Starlink View</button><button>↗ Rocket View</button><div>Active <b>●</b></div><button>◷ Full View</button><span>Amount (Ӿ)</span></div>
      <div class="xno-ledger">${Array.from({length:29},(_,i)=>`<div><i></i><span>Ӿ ${(.001+(i*17%71)/1000).toFixed(5)}</span></div>`).join('')}</div>
      <div class="xno-support">Support the project ↗</div></div>`;
    const scene=new T.Scene();scene.background=new T.Color('#000000');
    const camera=new T.PerspectiveCamera(45,1130/1000,.01,100);
    const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
    renderer.setPixelRatio(Math.min(1.5,window.devicePixelRatio));renderer.setSize(1130,1000);
    renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;
    root.querySelector('.xno-canvas').appendChild(renderer.domElement);
    const composer=new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));
    composer.addPass(new UnrealBloomPass(new T.Vector2(1130,1000),.48,.4,1.05));composer.addPass(new OutputPass());
    const loader=new T.TextureLoader();
    const [day,cloud,night,water]=await Promise.all([s.earth_map,s.earth_cloud_map,s.earth_night_map,s.earth_water_map].map(url=>loader.loadAsync(url)));
    day.colorSpace=night.colorSpace=T.SRGBColorSpace;day.anisotropy=4;cloud.anisotropy=4;
    const globe=new T.Group();scene.add(globe);
    const earth=new T.Mesh(new T.SphereGeometry(1,128,96),new T.MeshPhongMaterial({map:day,
      specularMap:water,emissiveMap:night,emissive:new T.Color('lightyellow'),emissiveIntensity:.4,
      specular:new T.Color(0x333333),shininess:15}));globe.add(earth);
    const clouds=new T.Mesh(new T.SphereGeometry(1.006,96,64),new T.MeshPhongMaterial({
      color:0xe6edfa,alphaMap:cloud,transparent:true,opacity:.42,depthWrite:false,shininess:1}));globe.add(clouds);
    scene.add(new T.AmbientLight(0xffffff,.1));const light=new T.DirectionalLight(0xffffff,2);light.position.set(5,1.5,3);scene.add(light);
    // The original app tilts Earth 23.5 degrees and uses Phong water/night maps.
    const atmosphere=new T.Mesh(new T.SphereGeometry(1.012,96,64),new T.ShaderMaterial({
      side:T.BackSide,transparent:true,depthWrite:false,blending:T.AdditiveBlending,
      vertexShader:'varying vec3 n;varying vec3 v;void main(){vec4 p=modelViewMatrix*vec4(position,1.);n=normalize(normalMatrix*normal);v=normalize(-p.xyz);gl_Position=projectionMatrix*p;}',
      fragmentShader:'varying vec3 n;varying vec3 v;void main(){float a=pow(1.-abs(dot(normalize(n),normalize(v))),4.);gl_FragColor=vec4(.035,.15,.38,a*.25);}'
    }));globe.add(atmosphere);
    const latLongToVector3=(lat,long,radius=1)=>{
      const phi=(90-lat)*Math.PI/180,theta=(long+180)*Math.PI/180;
      return new T.Vector3(-radius*Math.sin(phi)*Math.cos(theta),radius*Math.cos(phi),radius*Math.sin(phi)*Math.sin(theta));
    };
    // Exact spherical interpolation/lift construction from network-arc.tsx.
    const greatCircle=(a,b,count=50,maxLift=1.15)=>{
      const points=[],u=a.clone().normalize(),v=b.clone().normalize(),omega=Math.acos(Math.max(-1,Math.min(1,u.dot(v)))),sin=Math.sin(omega);
      for(let i=0;i<=count;i++){
        const t=i/count;if(Math.abs(sin)<.00001){points.push(a.clone());continue;}
        const point=u.clone().multiplyScalar(Math.sin((1-t)*omega)/sin).add(v.clone().multiplyScalar(Math.sin(t*omega)/sin));
        points.push(point.normalize().multiplyScalar(1.002*(1+(maxLift-1)*Math.sin(Math.PI*t))));
      }return points;
    };
    const locations=networkNodes.map(([lat,lon])=>latLongToVector3(lat,lon,1.003));
    const nodeMaterial=new T.MeshBasicMaterial({color:new T.Color(.04,.5,1.6),transparent:true,opacity:.9});
    const nodeGeometry=new T.SphereGeometry(.0035,8,6);
    locations.forEach((position,index)=>{
      const point=new T.Mesh(nodeGeometry,nodeMaterial);point.position.copy(position);globe.add(point);
      if(index<50){const bar=new T.Mesh(new T.CylinderGeometry(.0012,.0012,.018+index%5*.008,5),nodeMaterial);
        bar.position.copy(position.clone().multiplyScalar(1.018));bar.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),position.clone().normalize());globe.add(bar);}
    });
    const pulses=[];
    for(let i=0;i<92;i++){
      const a=locations[(i*7)%locations.length],b=locations[(i*13+3)%locations.length];
      if(a.distanceTo(b)<.08)continue;
      const points=greatCircle(a,b,50,1.15),curve=new T.CatmullRomCurve3(points);
      const route=new T.Line(new T.BufferGeometry().setFromPoints(points),new T.LineBasicMaterial({color:0x4e769c,transparent:true,opacity:.16,depthWrite:false}));globe.add(route);
      const material=new T.ShaderMaterial({transparent:true,depthWrite:false,blending:T.AdditiveBlending,
        uniforms:{progress:{value:0},color:{value:new T.Color(i%5?0x008dff:0x776dff)}},
        vertexShader:'varying float t;void main(){t=uv.x;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
        fragmentShader:'uniform float progress;uniform vec3 color;varying float t;void main(){float d=progress-t;float a=(1.-smoothstep(0.,.22,d))*step(0.,d);gl_FragColor=vec4(color*3.,a);}'
      });
      const trail=new T.Mesh(new T.TubeGeometry(curve,50,.0015,4,false),material);globe.add(trail);
      const head=new T.Mesh(new T.SphereGeometry(.0045,6,4),new T.MeshBasicMaterial({color:new T.Color(.3,1.5,3.5)}));globe.add(head);
      pulses.push({curve,material,head,phase:(i*.137)%1});
    }
    // A few of the reference app's radial launch streaks, with true depth tests.
    const launches=[];
    for(let i=0;i<8;i++){
      const start=locations[(i*11+2)%locations.length].clone(),end=start.clone().multiplyScalar(1.52);
      const curve=new T.LineCurve3(start,end),head=new T.Mesh(new T.CylinderGeometry(.002,.004,.045,6),new T.MeshBasicMaterial({color:new T.Color(.2,1.6,3.3)}));
      head.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),start.clone().normalize());globe.add(head);
      const ray=new T.Line(new T.BufferGeometry().setFromPoints([start,end]),new T.LineBasicMaterial({color:0x079fff,transparent:true,opacity:.2}));globe.add(ray);
      launches.push({curve,head,ray,index:i});
    }
    return {
      drawAt(seconds,duration){
        const t=Math.max(0,Math.min(1,seconds/duration)),ease=t*t*(3-2*t);
        globe.rotation.set(23.5*Math.PI/180,-1.78-.3*t,0);clouds.rotation.y=seconds*.00005;
        camera.position.set(.05,.33,3.55-.58*ease);camera.lookAt(0,0,0);
        pulses.forEach(({curve,material,head,phase})=>{const progress=(seconds*.65+phase)%1;material.uniforms.progress.value=progress;head.position.copy(curve.getPoint(progress));});
        launches.forEach(({curve,head,ray,index})=>{const progress=(seconds*.2+index*.177)%1;head.position.copy(curve.getPoint(progress));ray.material.opacity=.18*Math.sin(Math.PI*progress);});
        composer.render();
      },
      dispose(){scene.traverse(ob=>{ob.geometry?.dispose();if(ob.material)[ob.material].flat().forEach(m=>m.dispose());});[day,night,cloud,water].forEach(t=>t.dispose());composer.dispose();renderer.dispose();renderer.forceContextLoss();}
    };
  }
};
