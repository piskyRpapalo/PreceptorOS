(function () {
  var BD = 'preceptoros', ALMACEN = 'identity', CLAVE = 'me';
  
  
  var FIRMA_HEX = 128;
  var zona = document.getElementById('identity');
  if (!zona) return;
    var T = {};
  var yo = null;

    var menu = document.createElement('div');
  menu.id = 'identity-menu';
  menu.popover = 'auto';
  document.body.appendChild(menu);

  function abrir() {
    return new Promise(function (ok, mal) {
      var p = indexedDB.open(BD, 1);
      p.onupgradeneeded = function () { p.result.createObjectStore(ALMACEN); };
      p.onsuccess = function () { ok(p.result); };
      p.onerror = function () { mal(p.error); };
    });
  }
  function tx(modo, fn) {
    return abrir().then(function (db) {
      return new Promise(function (ok, mal) {
        var t = db.transaction(ALMACEN, modo), s = t.objectStore(ALMACEN), r = fn(s);
        t.oncomplete = function () { ok(r && r.result); };
        t.onerror = function () { mal(t.error); };
      });
    });
  }
  function hex(buf) {
    return [].map.call(new Uint8Array(buf), function (b) {
      return ('0' + b.toString(16)).slice(-2);
    }).join('');
  }
  
  
  function apodo(pub) {
    return crypto.subtle.exportKey('raw', pub).then(function (raw) {
      return crypto.subtle.digest('SHA-256', raw);
    }).then(function (h) { return 'Tester-' + hex(h).slice(0, 4).toUpperCase(); });
  }

  function pintar() {
    zona.innerHTML = '';
    menu.innerHTML = '';
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'leve';
    b.setAttribute('popovertarget', 'identity-menu');
    if (yo) {
            b.textContent = T.idClave;
      b.setAttribute('aria-label', T.idClave);
            if (T.idPerfil && !/\/profile\.html$/.test(location.pathname)) {
        var mi = document.createElement('a');
        mi.className = 'leve yo-perfil';
        mi.href = './community.html#perfil';
        mi.textContent = yo.apodo;
        mi.title = T.idPerfil;
        zona.appendChild(mi);
      } else {
        
        var p = document.createElement('span');
        p.className = 'yo'; p.textContent = yo.apodo;
        zona.appendChild(p);
      }
      
      
      
      var n = document.createElement('p');
      n.className = 'tenue'; n.style.wordBreak = 'break-all';
      menu.appendChild(n);
      crypto.subtle.exportKey('raw', yo.claves.publicKey).then(function (raw) {
        var completa = hex(raw);
        n.textContent = T.idPublica + ' ' + completa;
                b.textContent = completa.slice(0, 6);
        b.classList.add('huella-corta');
      });
    } else {
            b.className = 'leve identity-icono';
      b.setAttribute('aria-label', T.idEntrar);
      b.title = T.idEntrar;
      b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        + ' stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"'
        + ' aria-hidden="true"><circle cx="12" cy="8" r="4"></circle>'
        + '<path d="M4 21v-1a7 7 0 0 1 7-7h2a7 7 0 0 1 7 7v1"></path></svg>';
            var av = document.createElement('p');
      av.className = 'nodata'; av.textContent = T.idAviso;
      var ok = document.createElement('button');
      ok.type = 'button'; ok.className = 'boton'; ok.textContent = T.idEntrar;
      ok.addEventListener('click', function () {
        if (menu.hidePopover) menu.hidePopover();
        registrar();
      });
      menu.appendChild(av); menu.appendChild(ok);
    }
    zona.appendChild(b);
  }
  function registrar() {
    
    
    
    var aviso = document.createElement('p');
    aviso.className = 'nodata';
    zona.appendChild(aviso);
    return crypto.subtle.generateKey({ name: 'Ed25519' }, false, ['sign', 'verify'])
      .then(function (k) {
        return tx('readwrite', function (s) { s.put(k, CLAVE); }).then(function () { return k; });
      })
      .then(function (k) { return apodo(k.publicKey).then(function (a) { yo = { claves: k, apodo: a }; }); })
      .then(function () {
        pintar();
        document.dispatchEvent(new CustomEvent('preceptor:identity', { detail: { apodo: yo.apodo } }));
      })
      .catch(function (e) {
        aviso.textContent = T.idFallo + ' ' + (e && e.message ? e.message : e);
      });
  }

  window.Identity = {
    quien: function () { return yo && yo.apodo; },
        crear: function () { return registrar(); },
    
    
    
    publica: function () {
      if (!yo) return Promise.reject(new Error('sin identidad'));
      return crypto.subtle.exportKey('raw', yo.claves.publicKey).then(hex);
    },
        olvidar: function () {
      if (!yo) return Promise.reject(new Error('sin identidad'));
      return tx('readwrite', function (s) { s.delete(CLAVE); }).then(function () {
        yo = null;
        pintar();
        document.dispatchEvent(new CustomEvent('preceptor:identity',
                                               { detail: { apodo: null } }));
      });
    },
    
    
    
    
    
    
    
    
    
    
        firmarTexto: function (texto) {
      if (!yo) return Promise.reject(new Error('sin identidad'));
      return crypto.subtle.sign({ name: 'Ed25519' }, yo.claves.privateKey,
        new TextEncoder().encode(String(texto))).then(function (f) {
          var h = hex(f);
          if (h.length !== FIRMA_HEX) {
            return Promise.reject(new Error(
              'firma de ' + h.length + ' caracteres, se esperaban ' + FIRMA_HEX));
          }
          return h;
        });
    },
    firmar: function (obj) {
      if (!yo) return Promise.reject(new Error('sin identidad'));
      var texto = JSON.stringify(obj);
      return crypto.subtle.sign({ name: 'Ed25519' }, yo.claves.privateKey,
        new TextEncoder().encode(texto)).then(function (f) {
          
          
          
          var h = hex(f);
          if (h.length !== FIRMA_HEX) {
            return Promise.reject(new Error(
              'firma de ' + h.length + ' caracteres, se esperaban ' + FIRMA_HEX));
          }
          return { firma: 'ed25519:' + h, autor: yo.apodo, algoritmo: 'Ed25519' };
        });
    }
  };

    function rotulos() {
    var bloque = document.getElementById('i18n');
    if (bloque) {
      try {
        var propio = JSON.parse(bloque.textContent);
        if (propio && propio.idPerfil) return Promise.resolve(propio);
      } catch (err) { }
    }
        return Promise.resolve({ idClave: 'Your key', idPublica: 'Public key:', idEntrar: 'Create my key',
      idAviso: 'Your key is born in this browser. It cannot be exported or recovered.', idFallo: 'Could not create the key:' });
  }

  rotulos().then(function (t) { T = t; return arranca(); });

  function arranca() {
  return tx('readonly', function (s) { return s.get(CLAVE); }).then(function (k) {
    if (!k) { pintar(); return; }
    return apodo(k.publicKey).then(function (a) {
      yo = { claves: k, apodo: a }; pintar();
      document.dispatchEvent(new CustomEvent('preceptor:identity', { detail: { apodo: a } }));
    });
  }).catch(function () { pintar(); });
  }
})();
