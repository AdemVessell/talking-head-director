import React from 'react';
import {Composition,registerRoot} from 'remotion';
import {Main} from './Main';
import TL from './timeline.json';
const n=Math.round(TL.duration*TL.fps);
registerRoot(()=>React.createElement(React.Fragment,null,
 React.createElement(Composition,{id:'Main',component:Main,width:1080,height:1350,fps:TL.fps,durationInFrames:n}),
 React.createElement(Composition,{id:'Draft',component:Main,width:540,height:676,fps:TL.fps,durationInFrames:n})));
