
(function (raiz) {
  'use strict';


  var O = raiz.AtlasOnda, E = raiz.AtlasEscena, DURA = 3600, ANT = 1100;

  function quieto() { return raiz.matchMedia && raiz.matchMedia('(prefers-reduced-motion: reduce)').matches; }
  function el(tag, clase, texto) { var n = document.createElement(tag); if (clase) { n.className = clase; } if (texto != null) { n.textContent = String(texto); } return n; }
  function T(k, d) { return (raiz.AtlasJuego && raiz.AtlasJuego.texto(k)) || d; }
  function semillaInt(t) { return parseInt(String(t.semilla || '0').slice(0, 8), 16) || 7; }
  function cicloActual() {
    var J = raiz.AtlasJuego, e = J && J.instantanea ? J.instantanea() : null;
    return e && Number.isSafeInteger(e.ciclo) ? e.ciclo : null;
  }


  function batalla() { var b = document.getElementById('thegame-batalla'); return b && !b.hidden ? b : null; }

  function muestra(t, alCerrar) {
    if (!t || !t.armonicos) { return; }
    var enCurso = batalla();
    if (enCurso && raiz.MutationObserver) {
      var ob = new raiz.MutationObserver(function () { if (enCurso.hidden) { ob.disconnect(); muestra(t, alCerrar); } });
      ob.observe(enCurso, { attributes: true, attributeFilter: ['hidden'] });
      return null;
    }
    var capa = document.getElementById('thegame') || document.body, antes = document.activeElement;
    var fondo = el('div', 'revela'), cv = el('canvas', 'revela-lienzo'), n = O.riqueza(t.armonicos);
    var rar = T('rar_' + t.rareza, t.rareza), S = raiz.AtlasSintesis;
    var cuenta = t.aristas ? T('aristas_n', '{n} edges').replace('{n}', t.aristas) : n + ' ' + T('revela_arm', 'harmonics');
    cv.setAttribute('role', 'img');
    cv.setAttribute('aria-label', rar + ' · ' + cuenta + ' · ' + T('revela_aria', 'a new wave is born, harmonic by harmonic'));
    var pie = el('div', 'revela-pie'), txt = el('p', 'revela-txt'), b = el('button', 'boton revela-ok', T('revela_ok', 'Continue'));
    b.type = 'button'; txt.setAttribute('role', 'status');
    pie.appendChild(txt);
    var tarjeta = raiz.AtlasRevelaFicha && raiz.AtlasRevelaFicha.monta(t), personaliza = tarjeta && tarjeta.button;
    if (tarjeta) { pie.appendChild(tarjeta.element); personaliza.addEventListener('click', function () { cierra(); raiz.AtlasRevelaFicha.personaliza(); }); }
    pie.appendChild(b); fondo.appendChild(cv); fondo.appendChild(pie);
    capa.appendChild(fondo);
    var g = cv.getContext('2d'), dpr = Math.min(2, raiz.devicePixelRatio || 1), inicioCiclo = cicloActual(), raf = 0, vivo = true, q = quieto();
    var sem = semillaInt(t), col = O.tono(t), chispas = [];
    for (var i = 0; i < 48; i++) { chispas.push([E.hash(i, 1, sem), E.hash(i, 2, sem), 0.4 + E.hash(i, 3, sem) * 0.6]); }
    var anillos = [];
    function cierra() {
      if (!vivo) { return; }
      vivo = false; raiz.cancelAnimationFrame(raf); fondo.remove();
      document.removeEventListener('keydown', tecla, true);
      if (alCerrar) { alCerrar(); } else if (antes && antes.focus) { antes.focus(); }
    }
    function tecla(e) { if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cierra(); } }
    var sonado = false, tiembla = null, cicloMs = raiz.AtlasMotor && raiz.AtlasMotor.CICLO_MS || 1000;

    function anticipa(W, H, cx, cy, k) {
      g.globalCompositeOperation = 'source-over'; g.fillStyle = 'rgba(4,4,14,.55)'; g.fillRect(0, 0, W, H);
      var fr = Math.floor(k * 40);
      g.strokeStyle = 'hsla(171 78% 54% / .5)'; g.lineWidth = dpr;
      for (var i = 0; i < 26; i++) {
        var y = H * (0.18 + 0.64 * i / 26), d = (1 - k) * H * 0.05 * (E.hash(i, fr, sem) - 0.5);
        g.beginPath(); g.moveTo(W * 0.08, y + d); g.lineTo(W * 0.92, y - d); g.stroke();
      }
      var u = Math.min(1, k * 1.25), cae = 1 - Math.pow(1 - u, 3) + (u >= 1 ? Math.sin((k - 0.8) * 30) * 0.02 * (1 - k) : 0);
      var y0 = -H * 0.1 + (cy + H * 0.1) * cae, rx = Math.min(W, H) * 0.05;
      g.fillStyle = 'hsl(' + col[0] + ' ' + col[1] + '% 62%)'; g.beginPath(); g.ellipse(cx, y0, rx * (u >= 1 ? 1.12 : 0.9), rx * 1.5 * (u >= 1 ? 0.88 : 1.1), 0, 0, Math.PI * 2); g.fill();
    }
    function cuadro() {
      if (!vivo) { return; }
      raf = raiz.requestAnimationFrame(cuadro);
      var ciclo = cicloActual(), transcurrido = ciclo === null || inicioCiclo === null ? ANT + DURA : Math.max(0, ciclo - inicioCiclo) * cicloMs;
      var w = cv.clientWidth, h = cv.clientHeight;
      if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
      var W = cv.width, H = cv.height, cx = W / 2, cy = H * 0.44, R = Math.min(W, H) * 0.3;
      if (!q && transcurrido < ANT) { anticipa(W, H, cx, cy, transcurrido / ANT); return; }
      if (!sonado) { sonado = true; if (!q && S && S.suena) { S.suena({ tipo: 'sonar', portadora: 1320, moduladora: 660, indice: 90, dur: 0.6, gan: 0.06 }); } }
      var p = q ? 1 : Math.min(1, Math.max(0, (transcurrido - ANT) / DURA)), crece = q ? 1 : Math.max(0, Math.min(1, (p - 0.18) / 0.6));
      g.globalCompositeOperation = 'source-over'; g.fillStyle = 'rgba(4,4,14,' + (q ? 1 : 0.35) + ')'; g.fillRect(0, 0, W, H);
      g.globalCompositeOperation = 'lighter';

      if (!q && p < 0.28) {
        var pr = p / 0.28;
        g.strokeStyle = 'hsla(171 78% 54% / ' + (1 - pr) * 0.8 + ')'; g.lineWidth = 3 * dpr;
        g.beginPath(); g.arc(cx, cy, Math.max(W, H) * 0.62 * pr, 0, Math.PI * 2); g.stroke();
      }

      if (p < 0.4) {
        var k = Math.min(1, p / 0.3);
        chispas.forEach(function (c) {
          var a = c[0] * Math.PI * 2, d = (1 - k) * Math.max(W, H) * 0.6 * c[2];
          g.fillStyle = 'hsla(' + col[0] + ' ' + col[1] + '% 80% / ' + (0.3 + 0.7 * k) + ')';
          g.fillRect(cx + Math.cos(a) * d, cy + Math.sin(a) * d, 2.5 * dpr, 2.5 * dpr);
        });
      }

      var entra = Math.floor(crece * t.armonicos.length);
      while (anillos.length < entra) { anillos.push(ciclo); }
      anillos.forEach(function (a0) {
        var d = ((ciclo - a0) * cicloMs) / (2 * cicloMs); if (d > 1) { return; }
        g.strokeStyle = 'hsla(' + col[0] + ' ' + col[1] + '% 75% / ' + (1 - d) * 0.6 + ')'; g.lineWidth = 2 * dpr;
        g.beginPath(); g.arc(cx, cy, R * (0.3 + d * 1.1), 0, Math.PI * 2); g.stroke();
      });
      if (crece > 0) {
        O.dibuja(g, t.armonicos, cx, cy, R * (0.6 + 0.4 * crece), { t: transcurrido, crece: crece, giro: q ? 0 : transcurrido * 0.00035,
          color: col, grosor: 2.6 * dpr, brillo: 0.6 + 0.4 * crece, estela: q ? 0 : 6, respira: !q, calidad: 2, face: true });
      }
      if (tarjeta && p >= 1) { tarjeta.element.hidden = false; }
      if (p >= 1 && !txt.textContent) { txt.textContent = inicioCiclo === null ? 'NO_DATA (game cycle unavailable; showing the measured final frame) · ' + rar + ' · ' + cuenta : rar + ' · ' + cuenta; b.focus(); tiembla = ciclo; if (S && S.vozDe) { S.suena(S.vozDe(t)); } }

      var faseTemblor = tiembla === null || q ? 0 : Math.max(0, 3 - (ciclo - tiembla));
      cv.style.transform = faseTemblor ? 'translate(' + (Math.sin((ciclo - tiembla) * Math.PI / 2) * 3 * faseTemblor / 3).toFixed(1) + 'px,0)' : '';
    }
    b.addEventListener('click', cierra);
    fondo.addEventListener('click', function (e) { if (e.target === cv && (q || transcurrido > 0)) { cierra(); } });
    document.addEventListener('keydown', tecla, true);
    raf = raiz.requestAnimationFrame(cuadro);
    return { cierra: cierra };
  }

  raiz.AtlasRevela = { muestra: muestra, DURA: DURA, ANT: ANT };
})(this);
