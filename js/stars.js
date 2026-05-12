(function () {
'use strict';
const canvas = document.getElementById('star-field');
if (!canvas) return;
const ctx = canvas.getContext('2d');
let width, height, stars = [], galaxies = [], nebulae = [], dpr;

function rand(a, b) { return a + Math.random() * (b - a); }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

// [hue, sat%, lightness%] — pastel palette
const STAR_COLORS = [
  null, null, null,               // minority white/blue-white
  [210, 55, 88], // pastel blue
  [195, 50, 85], // ice blue
  [240, 45, 84], // lavender-white
  [40,  50, 90], // warm straw
  [20,  55, 86], // soft orange
  [280, 45, 84], // pastel violet
  [160, 40, 82], // soft mint
  [350, 50, 87], // rosy
  [60,  45, 88], // pale gold
  [300, 40, 85], // soft pink-violet
];

const NEBULA_HUES = [210, 280, 340, 30, 160, 200, 260, 15];

const GALAXY_COLORS = [
  [160, 45, 62], // teal (accent-ish)
  [210, 40, 68], // steel blue
  [280, 35, 62], // soft purple
  [40,  40, 68], // amber
  [195, 45, 65], // cyan
  [320, 35, 65], // pink
];

function resize() {
  dpr = Math.min(window.devicePixelRatio || 1, 2);
  width  = window.innerWidth;
  height = window.innerHeight;
  canvas.width  = width  * dpr;
  canvas.height = height * dpr;
  canvas.style.width  = width  + 'px';
  canvas.style.height = height + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function createStars() {
  // ~60% denser than before
  const count = Math.floor((width * height) / 2400);
  stars = [];
  for (let i = 0; i < count; i++) {
    const rnd = Math.random();
    let r;
    if      (rnd < 0.70)  r = rand(0.15, 0.7);  // tiny
    else if (rnd < 0.90)  r = rand(0.7,  1.5);  // medium
    else if (rnd < 0.99)  r = rand(1.5,  2.6);  // bright
    else                  r = rand(2.6,  3.8);   // rare brilliant

    const color = pick(STAR_COLORS);
    const elliptical = Math.random() < 0.10 && r > 0.7;

    stars.push({
      x: Math.random() * width,
      y: Math.random() * height,
      r,
      alpha: rand(0.18, 0.88),
      twinkleSpeed: rand(0.003, 0.022),
      twinklePhase: Math.random() * Math.PI * 2,
      color,
      elliptical,
      scaleY: elliptical ? rand(0.28, 0.65) : 1,
      rotation: Math.random() * Math.PI,
      twinkle: r > 0.9,
    });
  }
}

function createNebulae() {
  const count = 4 + Math.floor(Math.random() * 5); // 4–8
  nebulae = [];
  for (let i = 0; i < count; i++) {
    const h = pick(NEBULA_HUES);
    const hasSecondary = Math.random() < 0.55;
    nebulae.push({
      x: rand(0.05, 0.95) * width,
      y: rand(0.05, 0.95) * height,
      size:   rand(200, 520),
      alpha:  rand(0.012, 0.042),
      h,
      scaleY: rand(0.35, 0.85),
      rotation: Math.random() * Math.PI,
      hasSecondary,
      sx:    rand(-100, 100),
      sy:    rand(-70,   70),
      ssize: rand(100, 260),
      sh:    (h + 25 + Math.floor(Math.random() * 30)) % 360,
    });
  }
}

function createGalaxies() {
  const count = Math.floor(width / 380) + 3;
  galaxies = [];
  for (let i = 0; i < count; i++) {
    const color = pick(GALAXY_COLORS);
    const size  = rand(18, 48);
    galaxies.push({
      x:        Math.random() * width,
      y:        Math.random() * height,
      size,
      alpha:    rand(0.05, 0.14),
      rotation: Math.random() * Math.PI * 2,
      scaleY:   rand(0.22, 0.52),
      color,
      numArms:  Math.random() < 0.55 ? 2 : (Math.random() < 0.6 ? 3 : 4),
      armWind:  rand(0.35, 0.7),
    });
  }
}

function drawNebulae() {
  nebulae.forEach(n => {
    ctx.save();
    ctx.translate(n.x, n.y);
    ctx.rotate(n.rotation);
    ctx.scale(1, n.scaleY);

    const g = ctx.createRadialGradient(0, 0, 0, 0, 0, n.size);
    g.addColorStop(0,   `hsla(${n.h},60%,70%,${n.alpha * 2.2})`);
    g.addColorStop(0.3, `hsla(${n.h},55%,65%,${n.alpha})`);
    g.addColorStop(0.65,`hsla(${n.h},50%,60%,${n.alpha * 0.35})`);
    g.addColorStop(1,   `hsla(${n.h},45%,55%,0)`);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(0, 0, n.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    if (n.hasSecondary) {
      ctx.save();
      ctx.translate(n.x + n.sx, n.y + n.sy);
      ctx.rotate(n.rotation + 0.6);
      ctx.scale(1, n.scaleY * 0.75);
      const g2 = ctx.createRadialGradient(0, 0, 0, 0, 0, n.ssize);
      g2.addColorStop(0,   `hsla(${n.sh},58%,72%,${n.alpha * 1.8})`);
      g2.addColorStop(0.5, `hsla(${n.sh},52%,66%,${n.alpha * 0.5})`);
      g2.addColorStop(1,   `hsla(${n.sh},48%,60%,0)`);
      ctx.fillStyle = g2;
      ctx.beginPath();
      ctx.arc(0, 0, n.ssize, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  });
}

function drawGalaxy(g) {
  const [h, s, l] = g.color;

  // Diffuse disk
  ctx.save();
  ctx.translate(g.x, g.y);
  ctx.rotate(g.rotation);
  ctx.scale(1, g.scaleY);
  const disk = ctx.createRadialGradient(0, 0, 0, 0, 0, g.size);
  disk.addColorStop(0,    `hsla(${h},${s}%,${l}%,${g.alpha * 1.4})`);
  disk.addColorStop(0.45, `hsla(${h},${s}%,${l}%,${g.alpha * 0.7})`);
  disk.addColorStop(1,    `hsla(${h},${s}%,${l}%,0)`);
  ctx.fillStyle = disk;
  ctx.beginPath();
  ctx.arc(0, 0, g.size, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // Spiral arms — dots along logarithmic spiral
  ctx.save();
  ctx.translate(g.x, g.y);
  ctx.rotate(g.rotation);
  for (let arm = 0; arm < g.numArms; arm++) {
    const armBase = (arm / g.numArms) * Math.PI * 2;
    for (let t = 0.06; t < 1; t += 0.035) {
      const r     = t * g.size * 1.15;
      const theta = armBase + t * Math.PI * 2.2 * g.armWind;
      const ax = Math.cos(theta) * r;
      const ay = Math.sin(theta) * r * g.scaleY;
      const dotA = g.alpha * (1 - t * 0.75) * 0.9;
      const dotR = (1 - t) * 1.8 + 0.25;
      ctx.fillStyle = `hsla(${h},${s}%,${Math.min(l + 18, 94)}%,${dotA})`;
      ctx.beginPath();
      ctx.arc(ax, ay, dotR, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  ctx.restore();

  // Bright compact core
  ctx.save();
  ctx.translate(g.x, g.y);
  const coreR = g.size * 0.18;
  const core  = ctx.createRadialGradient(0, 0, 0, 0, 0, coreR);
  core.addColorStop(0,   `hsla(${h},${Math.max(s - 20, 0)}%,${Math.min(l + 28, 96)}%,${g.alpha * 4})`);
  core.addColorStop(0.5, `hsla(${h},${s}%,${l}%,${g.alpha * 1.8})`);
  core.addColorStop(1,   `hsla(${h},${s}%,${l}%,0)`);
  ctx.fillStyle = core;
  ctx.beginPath();
  ctx.arc(0, 0, coreR, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

let time = 0;
function draw() {
  ctx.clearRect(0, 0, width, height);
  time += 0.016;

  drawNebulae();
  galaxies.forEach(drawGalaxy);

  stars.forEach(s => {
    let a = s.alpha;
    if (s.twinkle) {
      a *= Math.sin(time * s.twinkleSpeed * 60 + s.twinklePhase) * 0.32 + 0.68;
    }

    const colorStr = s.color
      ? `hsla(${s.color[0]},${s.color[1]}%,${s.color[2]}%,${a})`
      : `rgba(218,228,240,${a})`;

    ctx.save();
    if (s.elliptical) {
      ctx.translate(s.x, s.y);
      ctx.rotate(s.rotation);
      ctx.scale(1, s.scaleY);
    }
    ctx.fillStyle = colorStr;
    ctx.beginPath();
    ctx.arc(s.elliptical ? 0 : s.x, s.elliptical ? 0 : s.y, s.r, 0, Math.PI * 2);
    ctx.fill();

    // Soft glow halo for brighter stars
    if (s.r > 1.8) {
      const glowR = s.r * 3.5;
      const h  = s.color ? s.color[0] : 210;
      const sa = s.color ? s.color[1] : 20;
      const l  = s.color ? s.color[2] : 90;
      const gx = s.elliptical ? 0 : s.x;
      const gy = s.elliptical ? 0 : s.y;
      const glow = ctx.createRadialGradient(gx, gy, 0, gx, gy, glowR);
      glow.addColorStop(0, `hsla(${h},${sa}%,${l}%,${a * 0.38})`);
      glow.addColorStop(1, `hsla(${h},${sa}%,${l}%,0)`);
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(gx, gy, glowR, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  });

  requestAnimationFrame(draw);
}

function init() {
  resize();
  createStars();
  createNebulae();
  createGalaxies();
  draw();
}

window.addEventListener('resize', () => {
  resize();
  createStars();
  createNebulae();
  createGalaxies();
});

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
})();
