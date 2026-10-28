(function () {
  'use strict';
  const units = [
    { row: {kind:'unit',id:'guide',q:-2,r:0,seed:0}, style:'tutorial' },
    { row: {kind:'unit',id:'keeper',q:0,r:0,seed:2}, style:'atlantis' },
    { row: {kind:'unit',id:'wanderer',q:2,r:0,seed:4}, style:'risen' },
    { row: {kind:'unit',id:'scout',q:-2,r:-3,seed:1}, style:'tutorial' },
    { row: {kind:'unit',id:'tender',q:0,r:-3,seed:2}, style:'tutorial' },
    { row: {kind:'unit',id:'sailor',q:2,r:-3,seed:3}, style:'atlantis' },
    { row: {kind:'unit',id:'listener',q:-3,r:3,seed:4}, style:'risen' },
    { row: {kind:'unit',id:'helper',q:-1,r:3,seed:5}, style:'atlantis' },
    { row: {kind:'unit',id:'visitor',q:1,r:3,seed:0}, style:'risen' }
  ];
  const map = document.getElementById('floor'), status = document.getElementById('status');
  ColonyGround.mount(map, document);
  let cycle = 0;
  const figures = units.map(item => {
    const el = document.createElement('div');
    el.className = 'unit'; el.dataset.style = item.style; el.setAttribute('role','img');
    map.appendChild(el); return el;
  });
  function draw() {
    units.forEach((item, index) => {
      const frame = ColonyWalkingFrames.frame(item.row, cycle, item.style);
      const atom = frame.atoms[0], wave = atom.i[0];
      figures[index].style.transform = 'translate(' + (wave.x - 20) + 'px,' + (wave.y - 20) + 'px)';
      figures[index].style.zIndex = String(Math.round((138 + wave.y) * 100));
      figures[index].setAttribute('aria-label', atom.r);
    });
    status.textContent = 'Synthetic fixture · cycle ' + cycle + ' · sound NO_DATA';
  }
  document.getElementById('step').addEventListener('click', () => { cycle += 1; draw(); });
  draw();
})();
