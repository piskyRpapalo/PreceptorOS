(function () {
  'use strict';
  var status = document.getElementById('status');
  var match = /^\/creaciones\/([a-f0-9]{64})$/.exec(location.pathname);
  if (!match) { status.textContent = 'This creation URL is invalid.'; return; }
  fetch('/api/creaciones/' + match[1], { cache: 'no-store' }).then(function (response) {
    if (!response.ok) throw new Error('The rack could not return this creation.');
    return response.text();
  }).then(function (raw) { return CreationPackage.verify(raw); }).then(function (value) {
    if (value.id !== match[1]) throw new Error('Creation identifier mismatch.');
    var points = value.frame.atoms[0].i[0].pts;
    var svg = document.createElementNS('http:' + '//' + 'www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 412 515'); svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Verified ribbon drawing with ' + points.length + ' points');
    var line = document.createElementNS(svg.namespaceURI, 'polyline');
    line.setAttribute('points', points.map(function (point) { return point.join(','); }).join(' '));
    line.setAttribute('fill', 'none'); line.setAttribute('stroke', 'currentColor'); line.setAttribute('stroke-width', '5');
    line.setAttribute('stroke-linecap', 'round'); line.setAttribute('stroke-linejoin', 'round'); svg.appendChild(line);
    document.getElementById('art').replaceChildren(svg);
    document.getElementById('author').textContent = 'Author: ' + value.manifest.author;
    document.getElementById('description').textContent = value.manifest.description;
    document.getElementById('voice').src = URL.createObjectURL(new Blob([value.audio], { type: 'audio/wav' }));
    document.getElementById('creation').hidden = false;
    status.textContent = 'Signature verified · ' + value.id;
  }).catch(function (error) {
    status.textContent = 'Creation could not be verified: ' + (error.message || String(error));
  });
})();
