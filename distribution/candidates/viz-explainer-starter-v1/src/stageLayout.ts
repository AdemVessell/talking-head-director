// Card field and camera keys for the starter scene.
// The camera keys are the original starter keys.
// The cards used to stand in the camera's foreground and through the stage:
// their bottoms fell below the stage top, and the nearest centers sat outside
// the stage radius, so the travel read as the lens cutting through the paper.
// They now stand on the stage in a receding row, still the near/mid/far field
// the pan is there to show, and clear of the camera's near plane.
import * as THREE from 'three';
import type {Key} from './track';

export const STAGE_TOP = 0.06; // cylinder at y=0.03, height 0.06
export const STAGE_RADIUS = 2.05;
export const NEAR = 0.02;
export const CLEARANCE = 0.5; // camera must stay at least this far from every card box

const rng = (seed: number) => {
  let r = seed >>> 0;
  return () => {
    r = (Math.imul(r, 1664525) + 1013904223) >>> 0;
    return r / 4294967296;
  };
};

export const CAMERA_KEYS: Key[] = [
  {t: 0, p: [2.6, 1.7, 4.4], l: [0, .3, 0]},
  {t: 1.4, p: [3.2, .9, 2.6], l: [.6, .3, -.2]},
  {t: 2.8, p: [1.2, 1.0, 3.8], l: [0, .3, .1]},
  {t: 4, p: [0, 1.3, 4.3], l: [0, .3, .15], hold: true},
];

export type Card = {w: number; h: number; th: number; x: number; y: number; z: number; ry: number};

export function layerCards(): Card[] {
  const R = rng(3);
  const cards: Card[] = [];
  for (let i = 0; i < 9; i++) {
    const w = .35 + R() * .25, h = .3 + R() * .3, th = .008;
    const along = i / 8;
    // Right of the hero shapes (the cylinder ends near x=0.9) and inside the stage.
    const x = 1.46 - along * 0.08 + (R() - 0.5) * 0.03;
    const z = 0.55 - along * 1.35 + (R() - 0.5) * 0.03;
    const y = STAGE_TOP + h / 2;
    const ry = -0.45 + (R() - 0.5) * 0.2;
    cards.push({w, h, th, x, y, z, ry});
  }
  return cards;
}

type V3 = {x: number; y: number; z: number};

function hermite(keys: Key[]) {
  const K = keys.map(k => ({
    t: k.t, hold: !!k.hold,
    p: new THREE.Vector3(...k.p), l: new THREE.Vector3(...k.l),
    vp: new THREE.Vector3(), vl: new THREE.Vector3(),
  }));
  for (let i = 1; i < K.length - 1; i++) {
    if (K[i].hold) continue;
    const dt = K[i + 1].t - K[i - 1].t;
    K[i].vp = K[i + 1].p.clone().sub(K[i - 1].p).divideScalar(dt);
    K[i].vl = K[i + 1].l.clone().sub(K[i - 1].l).divideScalar(dt);
  }
  return (t: number) => {
    if (t <= K[0].t) return {p: K[0].p.clone(), l: K[0].l.clone()};
    const e = K[K.length - 1];
    if (t >= e.t) return {p: e.p.clone(), l: e.l.clone()};
    let i = 0;
    while (t >= K[i + 1].t) i++;
    const a = K[i], b = K[i + 1], h = b.t - a.t, u = (t - a.t) / h, u2 = u * u, u3 = u2 * u;
    const c = [2 * u3 - 3 * u2 + 1, (u3 - 2 * u2 + u) * h, -2 * u3 + 3 * u2, (u3 - u2) * h];
    const m = (pa: THREE.Vector3, va: THREE.Vector3, pb: THREE.Vector3, vb: THREE.Vector3) =>
      new THREE.Vector3().addScaledVector(pa, c[0]).addScaledVector(va, c[1]).addScaledVector(pb, c[2]).addScaledVector(vb, c[3]);
    return {p: m(a.p, a.vp, b.p, b.vp), l: m(a.l, a.vl, b.l, b.vl)};
  };
}

function corners(card: Card) {
  const hx = card.w / 2, hy = card.h / 2, hz = card.th / 2;
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, card.ry, 0));
  const o = new THREE.Vector3(card.x, card.y, card.z);
  const out: THREE.Vector3[] = [];
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1])
    out.push(o.clone().add(new THREE.Vector3(sx * hx, sy * hy, sz * hz).applyQuaternion(q)));
  return out;
}

function pointToBox(p: V3, card: Card) {
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, card.ry, 0));
  const local = new THREE.Vector3(p.x - card.x, p.y - card.y, p.z - card.z).applyQuaternion(q.invert());
  const hx = card.w / 2, hy = card.h / 2, hz = card.th / 2;
  const cx = Math.max(-hx, Math.min(hx, local.x));
  const cy = Math.max(-hy, Math.min(hy, local.y));
  const cz = Math.max(-hz, Math.min(hz, local.z));
  const outside = Math.hypot(local.x - cx, local.y - cy, local.z - cz);
  const inside = Math.abs(local.x) <= hx && Math.abs(local.y) <= hy && Math.abs(local.z) <= hz;
  return inside ? -Math.min(hx - Math.abs(local.x), hy - Math.abs(local.y), hz - Math.abs(local.z)) : outside;
}

export function clearance(frames = 120, fps = 30) {
  const cards = layerCards();
  const at = hermite(CAMERA_KEYS);
  const cam = new THREE.PerspectiveCamera(36, 540 / 676, NEAR, 60);
  let minDistance = Infinity, minDepth = Infinity, offStage = 0, belowStage = 0;
  const visible: number[] = [];
  for (const card of cards) {
    if (Math.hypot(card.x, card.z) + Math.max(card.w, card.th) / 2 > STAGE_RADIUS) offStage++;
    if (card.y - card.h / 2 < STAGE_TOP - 1e-6) belowStage++;
  }
  for (let f = 0; f <= frames; f++) {
    const {p, l} = at(f / fps);
    cam.position.copy(p);
    cam.lookAt(l);
    cam.updateMatrixWorld();
    let n = 0;
    const near = p.clone().add(l.clone().sub(p).normalize().multiplyScalar(NEAR));
    for (const card of cards) {
      minDistance = Math.min(minDistance, pointToBox(p, card), pointToBox(near, card));
      let seen = false;
      for (const c of corners(card)) {
        const depth = -c.clone().applyMatrix4(cam.matrixWorld.clone().invert()).z;
        minDepth = Math.min(minDepth, depth);
        const ndc = c.clone().project(cam);
        if (depth > NEAR && ndc.x > -1 && ndc.x < 1 && ndc.y > -1 && ndc.y < 0.75) seen = true;
      }
      if (seen) n++;
    }
    visible.push(n);
  }
  const travel = visible.slice(Math.round(0.4 * fps), Math.round(2.2 * fps));
  const minVisible = Math.min(...travel);
  const shapeGap = minShapeGap(cards);
  const ok = minDistance >= CLEARANCE && minDepth >= CLEARANCE && offStage === 0 && belowStage === 0 && minVisible >= 5 && shapeGap >= 0.05;
  return {ok, minDistance, minDepth, offStage, belowStage, minVisible, shapeGap, near: NEAR, clearance: CLEARANCE};
}

const SHAPES = [
  {kind: 'sphere' as const, r: 0.22, a: [-.8, .28, -.4], b: [-.6, .28, .2]},
  {kind: 'box' as const, r: 0.36 / 2, a: [.15, .24, .35], b: [0, .24, .2]},
  {kind: 'cyl' as const, r: 0.17, h: 0.42, a: [.9, .27, -.2], b: [.6, .27, .2]},
];

function smooth(t: number) {
  const x = Math.max(0, Math.min(1, (t - 2.2) / (3.4 - 2.2)));
  return x * x * x * (10 + x * (-15 + 6 * x));
}

function minShapeGap(cards: Card[]) {
  let gap = Infinity;
  for (let s = 0; s <= 16; s++) {
    const u = smooth(4 * s / 16);
    for (const shape of SHAPES) {
      const x = shape.a[0] + (shape.b[0] - shape.a[0]) * u;
      const y = shape.a[1] + (shape.b[1] - shape.a[1]) * u;
      const z = shape.a[2] + (shape.b[2] - shape.a[2]) * u;
      for (const card of cards) {
        const dx = card.x - x, dz = card.z - z;
        const horiz = Math.hypot(dx, dz) - shape.r - Math.max(card.w, card.th) / 2;
        const vert = Math.abs(card.y - y) - (shape.kind === 'cyl' ? shape.h! / 2 : shape.r) - card.h / 2;
        gap = Math.min(gap, Math.max(horiz, vert));
      }
    }
  }
  return gap;
}
