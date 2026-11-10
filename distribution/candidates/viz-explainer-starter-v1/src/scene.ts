// Neutral starter world: an ivory stage, three primitive shapes, a field of thin layers to travel past,
// one continuous camera. Replace the contents per film; keep the update(t) contract (pure function of time).
import * as THREE from 'three';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';
import {PAL} from './tokens';
import {Track} from './track';
import {CAMERA_KEYS, layerCards} from './stageLayout';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const ease=(a:number,b:number,t:number)=>{const x=clamp((t-a)/(b-a));return x*x*x*(10+x*(-15+6*x))};
const rng=(seed:number)=>{let r=seed>>>0;return()=>{r=(r*1664525+1013904223)>>>0;return r/4294967296}};
// seeded paper-like surface (albedo + bump) generated once
function paperTexture(seed:number,base:[number,number,number]){const S=256,c=document.createElement('canvas');c.width=c.height=S;const g=c.getContext('2d')!;const im=g.createImageData(S,S);const R=rng(seed);
 for(let i=0;i<S*S;i++){const n=(R()+R()+R()-1.5)*9;for(let k=0;k<3;k++)im.data[i*4+k]=base[k]+n;im.data[i*4+3]=255}g.putImageData(im,0,0);
 g.globalAlpha=.12;g.strokeStyle='#6d6250';for(let i=0;i<600;i++){const x=R()*S,y=R()*S,a=R()*6.28;g.beginPath();g.moveTo(x,y);g.lineTo(x+Math.cos(a)*8,y+Math.sin(a)*8);g.stroke()}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;return t}
export function makeScene(canvas:HTMLCanvasElement,W:number,H:number){
 const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});renderer.setSize(W,H,false);renderer.setPixelRatio(1);
 renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.AgXToneMapping;renderer.toneMappingExposure=.85;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 const scene=new THREE.Scene();scene.background=new THREE.Color(PAL.void);scene.fog=new THREE.Fog(PAL.void,5,13);
 const pm=new THREE.PMREMGenerator(renderer);const env=pm.fromScene(new RoomEnvironment(),.04);scene.environment=env.texture;scene.environmentIntensity=.3;
 const camera=new THREE.PerspectiveCamera(36,W/H,.02,60);
 scene.add(new THREE.HemisphereLight('#efe6d6','#2a241e',.2));
 const key=new THREE.SpotLight(PAL.key,45,0,.55,.7,1.4);key.position.set(-3,4.4,2.6);key.target.position.set(0,.4,0);key.castShadow=true;key.shadow.mapSize.set(1024,1024);key.shadow.normalBias=.01;scene.add(key,key.target);
 const rim=new THREE.DirectionalLight(PAL.cool,1);rim.position.set(3,2.5,-4);scene.add(rim);
 const paper=paperTexture(7,[232,224,208]);
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(40,40),new THREE.MeshStandardMaterial({color:'#2a2622',roughness:.9}));floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);
 const stage=new THREE.Mesh(new THREE.CylinderGeometry(2.2,2.24,.06,96),new THREE.MeshStandardMaterial({map:paper,bumpMap:paper,bumpScale:.4,color:PAL.stage,roughness:.75}));stage.position.y=.03;stage.receiveShadow=true;scene.add(stage);
 const mat=(c:string,r=.5,m=0)=>new THREE.MeshStandardMaterial({color:c,roughness:r,metalness:m});
 const shapes=[new THREE.Mesh(new THREE.SphereGeometry(.22,48,32),mat(PAL.accent,.45)),new THREE.Mesh(new THREE.BoxGeometry(.36,.36,.36),mat('#d9d0c0',.6)),new THREE.Mesh(new THREE.CylinderGeometry(.17,.17,.42,48),mat('#4a3a2c',.38,.8))];
 const start=[[-.8,.28,-.4],[.15,.24,.35],[.9,.27,-.2]],end=[[-.6,.28,.2],[0,.24,.2],[.6,.27,.2]];
 shapes.forEach(s=>{s.castShadow=s.receiveShadow=true;scene.add(s)});
 // a field of thin layers the camera travels past: near, mid and far. They stand
 // on the stage (see stageLayout.ts), clear of the lens.
 const layers:THREE.Mesh[]=[];
 for(const card of layerCards()){const m=new THREE.Mesh(new THREE.BoxGeometry(card.w,card.h,card.th),new THREE.MeshStandardMaterial({map:paper,color:'#e9e1d2',roughness:.8}));
  m.position.set(card.x,card.y,card.z);m.rotation.y=card.ry;m.castShadow=m.receiveShadow=true;scene.add(m);layers.push(m)}
 const track=new Track(CAMERA_KEYS);
 const update=(t:number)=>{const a=ease(2.2,3.4,t);shapes.forEach((s,i)=>{s.position.set(start[i][0]+(end[i][0]-start[i][0])*a,start[i][1],start[i][2]+(end[i][2]-start[i][2])*a);s.rotation.y=t*.6*(i-1)});
  const c=track.eval(t);camera.position.copy(c.p);camera.lookAt(c.l);renderer.render(scene,camera)};
 return {update,dispose:()=>{scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose())}});env.dispose();pm.dispose();renderer.dispose()}};
}
