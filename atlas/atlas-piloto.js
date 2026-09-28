/* preceptoros.org · theGame · el PILOTO BASE de ATLAS.

   UNA REGLA FIJA, NO UN MODELO. Lee la instantanea (`atlas.instantanea/1`,
   la misma puerta que tendra la guia) y propone UNA accion del enum cerrado
   `atlas.accion/1`: esperar, recoger, reparar, aplazar o bajar_a <banda>. Son
   las mismas acciones que tiene la persona; ninguna toca valor, claves ni
   red. Proponer no es hacer: quien decide si se puede es el motor.

   ES LA LINEA BASE. Un LoRA del juego solo entra si le gana a esta regla en
   el arnes (`atlas/arnes_piloto.mjs`), con las mismas leyes y el mismo
   horizonte. Si no le gana, no sirve, por bonito que hable.

   PURA como el motor: ni DOM, ni red, ni reloj, ni azar. Misma instantanea,
   misma accion. Por eso corre igual en la pestana y en node. */
(function (raiz) {
  'use strict';

  var ACCIONES = ['esperar', 'recoger', 'reparar', 'aplazar', 'bajar_a'];
  var BANDAS = ['arrecife', 'ruinas', 'bosque', 'nucleo'];
  /* Las etiquetas de profundidad de la instantanea, en el orden de BANDAS. */
  var ETIQUETAS = ['0-50', '50-150', '150-300', '300+'];

  function accion(a, banda) {
    var x = { esquema: 'atlas.accion/1', accion: a, origen: 'piloto_base' };
    if (banda) { x.banda = banda; }
    return x;
  }

  /* LA REGLA, en el orden en que se lee:
     1. Grieta abierta y cobre para cerrarla: reparar.
     2. Lo producido «mientras dormias» esperando: recoger.
     3. Grieta abierta sin cobre: subir al arrecife, donde llega mas luz y la
        Forja hace mas cobre.
     4. Oxigeno por debajo del 10 %: subir antes de que el motor te suba.
     5. En el arrecife, grieta cerrada y oxigeno casi lleno: bajar a lo mas
        hondo permitido (el Nucleo pide Ingenieria 60), que es donde se gana
        Descenso.
     6. Si no, esperar. `c` son las constantes del motor (`AtlasMotor`). */
  function decide(ins, c) {
    if (!ins || ins.esquema !== 'atlas.instantanea/1' || !c) { return null; }
    var r = ins.recursos || {}, g = ins.grieta || {};
    var aqui = BANDAS[ETIQUETAS.indexOf(ins.profundidad)];
    if (!aqui) { return null; }
    if (g.abierta && r.cobre >= c.COBRE_REPARAR) { return accion('reparar'); }
    if (ins.pendiente_ciclos > 0) { return accion('recoger'); }
    if (aqui !== 'arrecife') {
      if (g.abierta) { return accion('bajar_a', 'arrecife'); }
      if (r.oxigeno * 10 < c.O2_MAX) { return accion('bajar_a', 'arrecife'); }
      return accion('esperar');
    }
    if (!g.abierta && r.oxigeno * 10 >= c.O2_MAX * 9) {
      var hondo = (ins.niveles || {}).ingenieria >= c.INGENIERIA_NUCLEO ? 'nucleo' : 'bosque';
      return accion('bajar_a', hondo);
    }
    return accion('esperar');
  }

  /* La forma, no el permiso: el permiso lo da el motor. Lo que no pasa por
     aqui no se ejecuta y cuenta como fallo del piloto. */
  function valida(a) {
    if (!a || a.esquema !== 'atlas.accion/1') { return false; }
    if (ACCIONES.indexOf(a.accion) < 0) { return false; }
    if (a.accion === 'bajar_a') { return BANDAS.indexOf(a.banda) >= 0; }
    return !('banda' in a);
  }

  var AtlasPiloto = { ACCIONES: ACCIONES, BANDAS: BANDAS, decide: decide, valida: valida };
  if (typeof module === 'object' && module.exports) { module.exports = AtlasPiloto; }
  else { raiz.AtlasPiloto = AtlasPiloto; }
})(this);
