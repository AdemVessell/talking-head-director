// Time-keyed Hermite camera track. Tangents are central differences in TIME so speed is continuous through
// keys; key spacing sets pace; hold:true makes a dead stop. Pure function of t (deterministic).
import * as THREE from 'three';
export type Key={t:number,p:[number,number,number],l:[number,number,number],hold?:boolean};
export class Track{private k:{t:number,p:THREE.Vector3,l:THREE.Vector3,vp:THREE.Vector3,vl:THREE.Vector3}[];
 constructor(keys:Key[]){this.k=keys.map(x=>({t:x.t,p:new THREE.Vector3(...x.p),l:new THREE.Vector3(...x.l),vp:new THREE.Vector3(),vl:new THREE.Vector3()}));
  const K=this.k;for(let i=1;i<K.length-1;i++){if(keys[i].hold)continue;const dt=K[i+1].t-K[i-1].t;K[i].vp=K[i+1].p.clone().sub(K[i-1].p).divideScalar(dt);K[i].vl=K[i+1].l.clone().sub(K[i-1].l).divideScalar(dt)}}
 eval(t:number){const K=this.k;if(t<=K[0].t)return {p:K[0].p.clone(),l:K[0].l.clone()};const e=K[K.length-1];if(t>=e.t)return {p:e.p.clone(),l:e.l.clone()};
  let i=0;while(t>=K[i+1].t)i++;const a=K[i],b=K[i+1],h=b.t-a.t,u=(t-a.t)/h,u2=u*u,u3=u2*u;const c=[2*u3-3*u2+1,(u3-2*u2+u)*h,-2*u3+3*u2,(u3-u2)*h];
  const m=(pa:THREE.Vector3,va:THREE.Vector3,pb:THREE.Vector3,vb:THREE.Vector3)=>new THREE.Vector3().addScaledVector(pa,c[0]).addScaledVector(va,c[1]).addScaledVector(pb,c[2]).addScaledVector(vb,c[3]);
  return {p:m(a.p,a.vp,b.p,b.vp),l:m(a.l,a.vl,b.l,b.vl)}}}
