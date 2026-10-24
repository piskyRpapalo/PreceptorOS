(function (raiz) {
  'use strict';

  var VALORES = {
    estado: 'provisional',
        version: 'provisional-2026-10-11.aristas',
        tcs: {
      tc1: { coste: { cobre: 50, luz: 0 }, incuba: 20, base: 'pez' },
      tc2: { coste: { cobre: 200, luz: 100 }, incuba: 40, base: 'centinela' },
      tc3: { coste: { cobre: 600, luz: 300 }, incuba: 60, base: 'leviatan' },
      tc4: { coste: { cobre: 1500, luz: 500 }, incuba: 90, base: 'heraldo' }
    },
        aristas: {
      tc1: [[3, 340], [4, 300], [5, 110], [6, 85], [7, 50], [8, 35], [9, 25], [10, 15], [11, 15], [12, 10], [13, 10], [14, 5]],
      tc2: [[3, 330], [4, 300], [5, 105], [6, 80], [7, 55], [8, 35], [9, 25], [10, 20], [11, 15], [12, 10], [13, 10], [14, 10], [15, 5]],
      tc3: [[3, 325], [4, 300], [5, 100], [6, 75], [7, 55], [8, 35], [9, 30], [10, 20], [11, 15], [12, 15], [13, 15], [14, 10], [15, 5]],
      tc4: [[3, 325], [4, 300], [5, 95], [6, 70], [7, 50], [8, 35], [9, 30], [10, 25], [11, 20], [12, 15], [13, 15], [14, 10], [15, 5], [16, 5]]
    },
        rareza_aristas: { normal: 4, magico: 8, raro: 12 },
        forma: { a1: [6, 16], div: 1 },
    prefijos: {
      atlante: { vida: [4, 9] }, cuprico: { armadura: [3, 7] },
      termico: { inercia: [3, 8] }, solar: { vida: [2, 4], armadura: [1, 3] }
    },
    sufijos: {
      abismo: { profundidad: [2, 6] }, sigilo: { sigilo: [3, 8] },
      velocidad: { velocidad: [3, 7] }, algoritmo: { aura: [2, 5] }
    },
        base: { vida: [10, 4], armadura: [2, 2], velocidad: [3, 3] },
        taller: { gramos_por_arista: 1, leviatan_x: 3, lija: { base: 4, max: 5, paso: 1, stats: ['velocidad', 'armadura', 'vida', 'sigilo'] },
      tinte: { coste: 2 } },
        escuadron: { por_aristas: 96, coloso: 1, tope: 32, radio: 2.4, unidad: 0.3 },
        banderas: { teal: 171, ambar: 37, hielo: 197, violeta: 265, coral: 12, kelp: 140, oro: 50, rosa: 320 },
        simetria: { normal: 2, magico: 3, raro: 5, unico: 7 },
    terminos: { normal: 3, magico: 4, raro: 5, unico: 6 },
        sonidos: {
      pop: { f: 660, m: 2, indice: 120, dur: 0.12, gan: 0.18 },
      huevo: { f: 220, m: 0.5, indice: 30, dur: 0.5, gan: 0.12 },
      eclosion: { f: 440, m: 3, indice: 260, dur: 0.6, gan: 0.2 },
      adopcion: { f: 523, m: 1.5, indice: 80, dur: 0.45, gan: 0.18 }
    },
        sintesis: { modo: 'fm2', adsr: [0.005, 0.03, 0.55, 0.06], m2: 0.5, indice2: 0.5,
            sello: { eclosion: 'PROPUESTA_PENDIENTE_FIRMA', adopcion: 'FIRMADO' },
      urgencia: { PROPUESTA_PENDIENTE_FIRMA: 1, FIRMADO: 0 },
      vibrato_hz: 6, vibrato_prof: 0.02 },
    army_tope: 30,
        combate: {
      rondas: 40, tropas_max: 10, armadura_div: 2,
      ataque: { base: 3, aura: 2, inercia: 1, profundidad: 1 },
      esquiva: { por_sigilo: 12, tope: 300 },
      rating_inicial: 1000, k: 32, k_provisional: 48, provisional_hasta: 10,
            abandono_ciclos: 900
    },
        patrullas: [
      { id: 'arrecife', tc: 'tc1', n: 2 }, { id: 'algas', tc: 'tc1', n: 3 }, { id: 'ruinas', tc: 'tc2', n: 3 },
      { id: 'limo', tc: 'tc3', n: 3 }, { id: 'abismo', tc: 'tc4', n: 4 }, { id: 'nucleo', tc: 'tc4', n: 6 }
    ],
        fluidez: {
            melt_alfa: 0.93,
      melt_zoom: 1.0005,
      melt_rotacion: 0.0001,
            vida_hue_base: 270,
      vida_hue_cobre: 30,
      escudo_lightness_base: 72,
            escudo_lightness_min: 40,
      escudo_ref: 24,
            pulso_brillo_max: 0.3,
      pulso_grosor_max: 1.5,
            buffer_escala: [1.0, 0.5, 0.25],
      buffer_ancho_max: 320,
            dither_on: true,
      dither_patron: [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 13, 5, 15, 7],
            paso_grid: [1.0, 2.0, 4.0],
            niebla_alfa: 0.4,
      vignette_alfa: 0.3,
            npc_chunk: true,
      npc_escala: 0.25,
            estela_max: 8,
            burbujas_por_calidad: [0, 2, 5]
    },
        semantica: {
      melt_alfa: ['cuadro previo * alfa', 'calidad', 'CALIDAD', 'wave_render.js'],
      melt_zoom: ['escala del cuadro previo', 'calidad', 'CALIDAD', 'wave_render.js'],
      melt_rotacion: ['giro del cuadro previo', 'calidad', 'CALIDAD', 'wave_render.js'],
      vida_hue_base: ['H = base + (cobre - base) * (1 - vida)', 'vida restante', 'ESTADO', 'wave_render.js'],
      vida_hue_cobre: ['H con vida 0', 'vida restante', 'ESTADO', 'wave_render.js'],
      escudo_lightness_base: ['L = min + (base - min) * escudo', 'armadura', 'ESTADO', 'wave_render.js'],
      escudo_lightness_min: ['L sin escudo', 'armadura', 'ESTADO', 'wave_render.js'],
      escudo_ref: ['escudo = armadura / ref (ref = maximo medido)', 'armadura', 'ESTADO', 'wave_render.js'],
      pulso_brillo_max: ['max * rampa de ganancia del pop', 'golpe que suena', 'ESTADO', 'wave_render.js'],
      pulso_grosor_max: ['-', '-', 'SIN_LECTOR', null],
      buffer_escala: ['-', '-', 'SIN_LECTOR', null],
      buffer_ancho_max: ['-', '-', 'SIN_LECTOR', null],
      dither_on: ['tramado 4x4', 'calidad', 'CALIDAD', 'wave_render.js'],
      dither_patron: ['umbral por pixel (patron)', 'calidad', 'CALIDAD', 'wave_render.js'],
      paso_grid: ['vertice redondeado a la rejilla', 'calidad', 'CALIDAD', 'wave_render.js'],
      niebla_alfa: ['-', '-', 'SIN_LECTOR', null],
      vignette_alfa: ['oscurecido de bordes', 'lo no explorado', 'ESTADO', 'sea.js'],
      npc_chunk: ['NPC a resolucion baja', 'calidad', 'CALIDAD', 'sea.js'],
      npc_escala: ['-', '-', 'SIN_LECTOR', null],
      estela_max: ['-', '-', 'SIN_LECTOR', null],
      burbujas_por_calidad: ['-', '-', 'SIN_LECTOR', null],
      f: ['portadora = f * (1 - 0,25 * calor)', 'evento (golpe/cae/gana/pierde) y calor del Nucleo', 'ESTADO', 'core.js'],
      m: ['moduladora = f * m', 'evento', 'ESTADO', 'core.js'],
      indice: ['indice * (1 + 2 * calor)', 'calor del Nucleo', 'ESTADO', 'core.js'],
      dur: ['duracion; tambien la del pulso visual', 'evento', 'ESTADO', 'core.js'],
      gan: ['ganancia inicial de la rampa (sonido y pulso)', 'evento', 'ESTADO', 'core.js'],
      modo: ['fm2 (siempre) o fm3_adsr (EN_CURSO_hasta_escucha)', 'decision del Soberano', 'CONSTANTE', 'core.js'],
      adsr: ['envolvente del sonido y del pulso', 'evento', 'ESTADO', 'core.js'],
      m2: ['moduladora2 = portadora * m2', 'evento', 'ESTADO', 'core.js'],
      indice2: ['indice2 = indice * indice2', 'calor del Nucleo', 'ESTADO', 'core.js'],
      sello: ['sello del evento sonoro', 'que espera firma / que esta firmado', 'ESTADO', 'core.js'],
      urgencia: ['urgencia del sello (0 quieto, 1 vibra)', 'sello', 'ESTADO', 'core.js'],
      vibrato_hz: ['frecuencia del vibrato', 'sello', 'ESTADO', 'core.js'],
      vibrato_prof: ['profundidad = portadora * prof * urgencia', 'sello', 'ESTADO', 'core.js'],
      vida: ['base.vida[0]*tcLevel + seedInt(0..base.vida[1]) + affixMods + (unique ? tcLevel : 0) + Workshop sanding', 'signed seed, TC, edge-derived rarity, verified Workshop receipt', 'ESTADO', 'ui-taller.js'],
      armadura: ['base.armadura[0]*tcLevel + seedInt(0..base.armadura[1]) + affixMods + (unique ? tcLevel : 0) + Workshop sanding', 'signed seed, TC, edge-derived rarity, verified Workshop receipt', 'ESTADO', 'ui-taller.js'],
      velocidad: ['base.velocidad[0] + seedInt(0..base.velocidad[1]) + affixMods + (unique ? tcLevel : 0) + Workshop sanding', 'signed seed, TC, edge-derived rarity, verified Workshop receipt', 'ESTADO', 'ui-taller.js'],
      sigilo: ['affixMods + (unique ? tcLevel : 0) + Workshop sanding', 'edge-derived rarity, verified Workshop receipt', 'ESTADO', 'ui-taller.js'],
      inercia: ['affixMods + (unique ? tcLevel : 0)', 'edge-derived rarity; Workshop sanding is ineligible', 'ESTADO', 'ui-taller.js'],
      profundidad: ['affixMods + (unique ? tcLevel : 0)', 'edge-derived rarity; Workshop sanding is ineligible', 'ESTADO', 'ui-taller.js'],
      aura: ['affixMods + (unique ? tcLevel : 0)', 'edge-derived rarity; Workshop sanding is ineligible', 'ESTADO', 'ui-taller.js']
    }
  };

  if (typeof module === 'object' && module.exports) { module.exports = VALORES; }
  else { raiz.AtlasValores = VALORES; }
})(this);
