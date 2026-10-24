(function (root) {
  'use strict';
  var IS_NODE = typeof module === 'object' && !!module.exports;
  var AtlasSemantica = IS_NODE ? require('./tabla_semantica.js') : root.AtlasSemantica;
  var AtlasComicTokens = IS_NODE ? require('./comic_tokens.js') : root.AtlasComicTokens;
  var NEUTRAL = AtlasComicTokens.NEUTRAL;

  var BASE_VERMILION = '#E63946';
  var BASE_COMIC_YELLOW = '#FFB702';

  function channels(color) {
    var s = String(color).trim();
    var hex = /^#([0-9a-f]{6})$/i.exec(s);
    if (hex) {
      return [parseInt(hex[1].slice(0, 2), 16), parseInt(hex[1].slice(2, 4), 16), parseInt(hex[1].slice(4, 6), 16)];
    }
    var fn = /^rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/i.exec(s);
    if (fn && Number(fn[1]) <= 255 && Number(fn[2]) <= 255 && Number(fn[3]) <= 255) {
      return [Number(fn[1]), Number(fn[2]), Number(fn[3])];
    }
    throw new Error('unparseable color: ' + s);
  }

  function luminance(color) {
    var c = channels(color).map(function (v) {
      var s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }

  function contrast(a, b) {
    var la = luminance(a), lb = luminance(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
  }

  function round2(x) { return Math.round(x * 100) / 100; }

  function bandsOf(h, s, l, base) {
    var b = AtlasSemantica.bandas(h, s, l);
    return Object.freeze({ brillo: b.brillo, base: base, sombra: b.sombra, contorno: b.contorno });
  }

  function varaOf(base, against) {
    return Object.freeze(against.map(function (name) {
      return Object.freeze({ against: name, ratio: round2(contrast(base, NEUTRAL[name])) });
    }));
  }

  var ACCENTS = Object.freeze({
    'vermilion': Object.freeze({
      label: 'vermilion',
      bands: bandsOf(355, 78, 56, BASE_VERMILION),
      vara: varaOf(BASE_VERMILION, ['paper', 'ocean']),
      sound: Object.freeze({ g: 1, o: 0, words: 'one soft low bell' }),
      use: 'the p tile of the cover'
    }),
    'comic yellow': Object.freeze({
      label: 'comic yellow',
      bands: bandsOf(43, 100, 50, BASE_COMIC_YELLOW),
      vara: varaOf(BASE_COMIC_YELLOW, ['ink', 'ocean']),
      sound: Object.freeze({ g: 3, o: 1, words: 'one warm bell' }),
      use: 'the gold edge of the house letters, the Rare troops and the yellow play button'
    })
  });

  function tone(name) {
    if (!Object.prototype.hasOwnProperty.call(ACCENTS, name)) {
      return { name: 'NO_DATA', cause: 'unknown accent', bands: null };
    }
    return Object.freeze({ name: name, label: ACCENTS[name].label, bands: ACCENTS[name].bands });
  }

  var AtlasComicAccents = Object.freeze({ ACCENTS: ACCENTS, tone: tone, contrast: contrast });
  if (IS_NODE) { module.exports = AtlasComicAccents; }
  else { root.AtlasComicAccents = AtlasComicAccents; }
})(typeof module === 'object' && module.exports ? this : (this || window));
