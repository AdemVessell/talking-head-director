// Fails if the camera or its near plane enters a paper card, if a card
// pierces the stage, or if the travel no longer shows the card field.
import {clearance} from '../src/stageLayout.ts';
const r = clearance();
console.log(JSON.stringify({
  ok: r.ok,
  minDistance: +r.minDistance.toFixed(3),
  minDepth: +r.minDepth.toFixed(3),
  near: r.near,
  required: r.clearance,
  offStage: r.offStage,
  belowStage: r.belowStage,
  minCardsInFrameDuringTravel: r.minVisible,
  shapeGap: +r.shapeGap.toFixed(3),
}));
if (!r.ok) {
  console.error('CAMERA CLEARANCE FAIL');
  process.exit(1);
}
console.log('CAMERA CLEARANCE PASS');
