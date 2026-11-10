import React,{useEffect,useRef,useState} from 'react';
import {AbsoluteFill,delayRender,continueRender,cancelRender,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {makeScene} from './scene';
import {PAL,TYPE,SAFE} from './tokens';
import TL from './timeline.json';
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
// Frame clock: everything derives from useCurrentFrame()/fps. Capture is blocked until bundled fonts load;
// if a font fails to load the render is cancelled (no silent fallback).
export const Main:React.FC=()=>{
 const frame=useCurrentFrame(),{fps,width,height}=useVideoConfig();const t=frame/fps;const canvas=useRef<HTMLCanvasElement>(null);
 const world=useRef<ReturnType<typeof makeScene>|null>(null);const tr=useRef(t);tr.current=t;const [h]=useState(()=>delayRender('fonts and scene'));
 useEffect(()=>{let gone=false;Promise.all(Object.values(TYPE).map(f=>new FontFace(f.family,`url(${staticFile(f.file)})`,{weight:'100 900'}).load())).then(async fs=>{
   fs.forEach(f=>document.fonts.add(f));await document.fonts.ready;for(const f of Object.values(TYPE))if(!document.fonts.check(`${f.size}px ${f.family}`))throw new Error('Font failed to load: '+f.file);
   if(gone)return;world.current=makeScene(canvas.current!,width,height);world.current.update(tr.current);continueRender(h)}).catch(e=>cancelRender(e));
  return()=>{gone=true;world.current?.dispose()}},[h,width,height]);
 useEffect(()=>{world.current?.update(t)},[t]);const k=width/1080;
 return <AbsoluteFill style={{background:PAL.void}}><canvas ref={canvas} width={width} height={height} style={{width:'100%',height:'100%'}}/>
  {TL.text.map(x=>{const a=clamp((t-x.in)/.3)*clamp((x.out-t)/.3);if(a<=0)return null;const f=TYPE[x.font as keyof typeof TYPE];
   return <div key={x.id} style={{position:'absolute',left:SAFE.side*width,right:SAFE.side*width,textAlign:'center',top:x.pos==='top'?SAFE.top*height:undefined,bottom:x.pos==='bottom'?SAFE.bottom*height:undefined,opacity:a,
    fontFamily:f.family,fontWeight:f.weight,fontSize:f.size*k,letterSpacing:f.track,color:PAL.text,textShadow:`0 ${2*k}px ${10*k}px rgba(0,0,0,.65)`}}>{x.text}</div>})}
 </AbsoluteFill>};
