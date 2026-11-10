// Design tokens: palette, type, safe zones. Edit here, not inside scenes.
export const PAL={void:'#15120f',stage:'#efe8db',ink:'#15120F',accent:'#E2452B',cool:'#a9bdd4',key:'#ffe8cc',text:'#F4EFE6'};
export const TYPE={serif:{family:'Serif',file:'fonts/BodoniModa.ttf',weight:500,size:64,track:'-0.01em'},mono:{family:'Mono',file:'fonts/IBMPlexMono.ttf',weight:600,size:46,track:'0.12em'}};
export const SAFE={top:0.10,bottom:0.13,side:0.083}; // fractions of frame
// reading hold rule: max(1.2 s, 0.3 s per word + 0.5 s)
export const readHold=(text:string)=>Math.max(1.2,0.3*text.trim().split(/\s+/).length+0.5);
