(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.ColonyGround = factory();
})(globalThis, function () {
  'use strict';
  const W = 640, H = 276, CELL = 28;
  const CLEAR = Object.freeze({ left: 180, top: 88, right: 460, bottom: 188, margin: 18 });
  function hash(x, y, salt) {
    let n = Math.imul(x | 0, 0x1f123bb5) ^ Math.imul(y | 0, 0x5f356495) ^ salt;
    n = Math.imul(n ^ (n >>> 16), 0x45d9f3b);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
  }
  function field(x, y) {
    const gx = x / 112, gy = y / 112, ix = Math.floor(gx), iy = Math.floor(gy);
    const fx = gx - ix, fy = gy - iy;
    const mix = (a, b, t) => a + (b - a) * t;
    return mix(mix(hash(ix, iy, 19), hash(ix + 1, iy, 19), fx),
      mix(hash(ix, iy + 1, 19), hash(ix + 1, iy + 1, 19), fx), fy);
  }
  function scatter(width, height, rect, ox = 0, oy = 0) {
    if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1 || width * height > 1000000 ||
        !Number.isSafeInteger(ox) || !Number.isSafeInteger(oy) || Math.abs(ox) > 1000000 || Math.abs(oy) > 1000000) throw new RangeError('viewport');
    const points = [], m = rect.margin;
    for (let cy = Math.floor(oy / CELL); cy * CELL < oy + height; cy++) for (let cx = Math.floor(ox / CELL); cx * CELL < ox + width; cx++) {
      const x = Math.floor(cx * CELL + hash(cx, cy, 7) * CELL);
      const y = Math.floor(cy * CELL + hash(cx, cy, 11) * CELL);
      if (x < ox || y < oy || x >= ox + width || y >= oy + height) continue;
      const dx = Math.max(rect.left - x, 0, x - rect.right), dy = Math.max(rect.top - y, 0, y - rect.bottom);
      const edge = Math.max(dx, dy);
      if (edge <= m) continue;
      const threshold = Math.min(0.9, 0.12 + field(x, y) * 0.55 + (edge <= m + CELL * 2 ? 0.3 : 0));
      if (hash(cx, cy, 31) < threshold) points.push({ x: x - ox, y: y - oy });
    }
    return points;
  }
  function canvas(doc, w, h) { const c = doc.createElement('canvas'); c.width = w; c.height = h; return c; }
  function sprite(doc) {
    const c = canvas(doc, 32, 38), g = c.getContext('2d');
    g.fillStyle = '#785b3d'; g.fillRect(14, 20, 4, 16);
    g.fillStyle = '#387c4c'; g.fillRect(6, 8, 20, 16); g.fillRect(10, 4, 12, 24);
    g.fillStyle = '#55a95d';
    for (let y = 7; y < 24; y += 3) for (let x = 7; x < 25; x += 3) if (hash(x, y, 43) > 0.45) g.fillRect(x, y, 2, 2);
    for (let y = 8; y < 24; y += 5) for (let x = 8; x < 25; x += 5) if (hash(x, y, 53) > 0.55) g.clearRect(x, y, 2, 2);
    return c;
  }
  function patch(doc) {
    const c = canvas(doc, 16, 16), g = c.getContext('2d');
    g.fillStyle = '#d8be78'; g.fillRect(0, 0, 16, 16); g.fillStyle = '#b8a465';
    g.fillRect(2, 3, 2, 1); g.fillRect(10, 8, 1, 2); g.fillRect(6, 13, 2, 1);
    return c;
  }
  function renderGround(ctx, doc) {
    ctx.fillStyle = ctx.createPattern(patch(doc), 'repeat');
    ctx.fillRect(0, 0, W, H);
  }
  function mount(floor, doc) {
    const base = canvas(doc, W, H), ctx = base.getContext('2d'), crown = sprite(doc);
    base.className = 'ground-patch'; renderGround(ctx, doc); floor.prepend(base);
    const points = scatter(W, H, CLEAR), url = crown.toDataURL();
    points.forEach(p => {
      const item = doc.createElement('img'); item.className = 'ground-prop'; item.src = url; item.alt = '';
      item.style.left = (p.x / W * 100) + '%'; item.style.top = (p.y / H * 100) + '%';
      item.style.zIndex = String(p.y * 100); floor.appendChild(item);
    });
    const reference = canvas(doc, W, H), r = reference.getContext('2d');
    renderGround(r, doc); points.forEach(p => r.drawImage(crown, p.x - 16, p.y - 36));
    const preview = doc.getElementById('ground-preview');
    preview.getContext('2d').drawImage(reference, 0, 0, preview.width, preview.height);
  }
  return { field, scatter, mount };
});
