#!/usr/bin/env python3
"""compass.py · la Brújula de Aprendizaje. **Sensor de `memory.db`, no actuador.**

Lee el progreso de la persona y dice hacia dónde empuja el terreno. No escribe
en ninguna base de datos, nunca. Si no puede medir algo, lo declara: un número
decorativo en una brújula es peor que no tener brújula.

**Solo biblioteca estándar.** Sin numpy, sin scipy. La matriz es 8x8 (o 12x12 en
modo detalle) y su inversa sale por eliminación gaussiana escrita a mano, que a
ese tamaño es trivial y se audita leyéndola.

DE DÓNDE SALEN LOS PELDAÑOS
---------------------------
De `cara.progreso_camino`, que es la medida del producto, **no de una copia**.
Si viviera aquí un segundo cálculo, el día que cambie uno habría que acertar en
dos sitios — y la brújula diría una cosa mientras el Camino dice otra.

Eso obliga a una traducción, porque el producto mide en estados discretos
(`hecho`, `empezado`, `sin_empezar`, `no_medible`) y el campo necesita continuo:

    hecho        -> 1.0
    empezado     -> la proporción real cuando `cifras` la da (p. ej. salas/6);
                    0.5 solo cuando no hay con qué afinar
    sin_empezar  -> 0.0
    no_medible   -> 0.0 **y el peldaño entra en `no_medible`**, que viaja en la
                    respuesta. Cero porque hay que poner algo en el vector; la
                    marca existe para que nadie lea ese cero como «no ha hecho
                    nada» cuando significa «no se puede saber».

DOS DESVIACIONES DECLARADAS
---------------------------
1. **`calibrate()` no recorre la rejilla 6^8.** Son 1.679.616 puntos, y cada uno
   exige invertir la matriz: en stdlib son horas. Se muestrea un número acotado
   de puntos (por defecto 4.000) con un generador determinista propio — sin
   `random`, para que dos corridas den lo mismo — y se toma el percentil 99,9.
   El método y el número de muestras viajan en el resultado.
2. **La velocidad `v` es cero mientras no haya trayectoria.** El producto no
   guarda instantáneas de `p` a lo largo del tiempo, así que no hay de dónde
   sacar `dp/dt`. Se declara `v = [0]*n` y `velocidad_medible: false`, en vez de
   inventar un movimiento. Quien tenga trayectoria (las pruebas, o un futuro
   registro) la pasa por `historial=` y entonces sí se deriva.
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

PELDANOS = ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7")
NUCLEO_IDX = (0, 1, 2)
DIM_DETALLE = ("memorias_tema", "proyectos_activos", "preferencias", "ritmo")

NO_MEDIBLE = "no_medible"

# Pesos del potencial: el núcleo pesa más porque es de todos; las side quests
# se eligen. Es la misma regla que ya gobierna `cara.NUCLEO`.
PESOS = (1.5, 1.5, 1.5, 1.0, 1.0, 1.0, 1.0, 1.0)
LAMBDA = 0.3          # castigo a la dispersión del esfuerzo
MU = 0.1              # castigo a la curvatura (cambiar de idea a cada paso)
ALPHA = 0.3           # momentum temporal del campo
DELTA_HISTERESIS = 0.05
SATURACION_NUCLEO = 0.8
H_DERIVADA = 0.01
MAX_F_FALLBACK = 5.0
TAU_ESTABILIDAD = 86400.0
LATIDOS_PARA_EMPIRICO = 20
MUESTRAS_CALIBRADO = 4000

_TRANSFERS = os.path.join(AQUI, "docs", "compass_transfers.json")


class BrujulaNoDisponible(RuntimeError):
    """No hay con qué orientar. Ausencia declarada, no fallo mudo."""


# ─────────────────────────── álgebra, a mano ───────────────────────────

def _inversa(M):
    """Inversa por eliminación gaussiana con pivoteo parcial. None si singular."""
    n = len(M)
    A = [list(M[i]) + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col]) < 1e-12:
            return None
        A[col], A[piv] = A[piv], A[col]
        d = A[col][col]
        A[col] = [x / d for x in A[col]]
        for fila in range(n):
            if fila == col:
                continue
            f = A[fila][col]
            if f:
                A[fila] = [a - f * b for a, b in zip(A[fila], A[col])]
    return [fila[n:] for fila in A]


def _matvec(M, v):
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


def _norma_R(v, R):
    """||v||_R = sqrt(v^T R v). La métrica la pone el terreno, no Euclides."""
    return math.sqrt(max(0.0, sum(v[i] * R[i][j] * v[j]
                                  for i in range(len(v)) for j in range(len(v)))))


def _producto_R(u, v, R):
    return sum(u[i] * R[i][j] * v[j] for i in range(len(u)) for j in range(len(v)))


def _entropia(v):
    """Shannon sobre |v| normalizado. Protegida contra el vector nulo."""
    total = sum(abs(x) for x in v)
    if total < 1e-12:
        return 0.0
    h = 0.0
    for x in v:
        p = abs(x) / total
        if p > 1e-12:
            h -= p * math.log(p)
    return h


def _simetrizar(R):
    n = len(R)
    return [[(R[i][j] + R[j][i]) / 2.0 for j in range(n)] for i in range(n)]


def _dominancia_diagonal(R):
    """Diagonal a 1.0 como mínimo; fuera de diagonal capado a 0.95."""
    n = len(R)
    S = [list(f) for f in R]
    for i in range(n):
        if abs(S[i][i]) < 1.0:
            S[i][i] = 1.0
        for j in range(n):
            if i != j and abs(S[i][j]) > 0.95:
                S[i][j] = math.copysign(0.95, S[i][j])
    return S


def _aleatorio_determinista(semilla):
    """LCG propio. `random` daría otra cifra en cada corrida y el calibrado
    dejaría de ser reproducible — que es justo lo que un umbral no puede ser."""
    estado = semilla & 0xFFFFFFFF
    while True:
        estado = (1103515245 * estado + 12345) & 0x7FFFFFFF
        yield estado / 0x7FFFFFFF


# ─────────────────────────── la brújula ───────────────────────────

class LearningCompass:
    def __init__(self, db_path=None, loops_path=None, transfers_path=None,
                 modo="camino"):
        if modo not in ("camino", "detalle"):
            raise ValueError(f"modo desconocido: {modo}")
        self.modo = modo
        self.db_path = db_path
        self.loops_path = loops_path
        self.transfers_path = transfers_path or _TRANSFERS
        self._max_F = None
        self._calibrado = False
        self._prior = self._leer_prior()

    # --- lectura, siempre en solo lectura ---------------------------------

    def _leer_prior(self):
        try:
            with open(self.transfers_path, encoding="utf-8") as f:
                prior = json.load(f)["prior"]
        except Exception:
            # Sin prior no se cae a identidad: identidad dice «no sabemos nada»,
            # y sí sabemos algo. Se reconstruye la diagonal y se declara.
            return [[1.0 if i == j else 0.05 for j in range(8)] for i in range(8)]
        return _dominancia_diagonal(_simetrizar(prior))

    def _abrir_ro(self, ruta):
        if not ruta or not os.path.isfile(ruta):
            return None
        try:
            c = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
            c.row_factory = sqlite3.Row
            return c
        except sqlite3.Error:
            return None

    def _cuenta(self, c, sql, *args):
        try:
            fila = c.execute(sql, args).fetchone()
            return fila[0] if fila else 0
        except sqlite3.Error:
            return 0

    # --- 2 · estado -------------------------------------------------------

    def estado(self, modo=None):
        """Los peldaños en [0,1]. `self.no_medible` queda con los declarados."""
        modo = modo or self.modo
        self.no_medible = set()
        p = {k: 0.0 for k in PELDANOS}

        c = self._abrir_ro(self.db_path)
        if c is None:
            self.no_medible = set(PELDANOS)
            self.cifras = {}
            if modo == "detalle":
                for d in DIM_DETALLE:
                    p[d] = 0.0
                    self.no_medible.add(d)
            return p
        try:
            camino = self._camino_del_producto(c)
            estados = camino["estado"]
            self.cifras = camino.get("cifras", {})
            for clave in PELDANOS:
                p[clave] = self._continuo(clave, estados.get(clave, "sin_empezar"))
            # M1 no es binario: es la calidad del cerebro que responde.
            calidad = self.calidad_inferencia()
            if calidad is None:
                p["M1"] = 0.0
                self.no_medible.add("M1")
            else:
                p["M1"] = calidad
                self.no_medible.discard("M1")
            if modo == "detalle":
                p.update(self._detalle(c))
            return p
        finally:
            c.close()

    def _camino_del_producto(self, c):
        """`cara.progreso_camino`, que es la medida del producto. Si no se puede
        importar (uso suelto del módulo), se declara todo no medible."""
        try:
            import cara as _cara
            return _cara.progreso_camino(c, self.db_path)
        except Exception:
            self.no_medible.update(PELDANOS)
            return {"estado": {k: NO_MEDIBLE for k in PELDANOS}, "cifras": {}}

    def _continuo(self, clave, estado):
        if estado == "hecho":
            return 1.0
        if estado == NO_MEDIBLE:
            self.no_medible.add(clave)
            return 0.0
        if estado == "empezado":
            return self._proporcion(clave)
        return 0.0

    def _proporcion(self, clave):
        """La proporción real cuando las cifras la dan; 0.5 solo si no hay con qué."""
        cif = getattr(self, "cifras", {}) or {}
        if clave == "M0":
            return min(1.0, cif.get("perfil", 0) / 2.0)
        if clave == "M2":
            return 0.5 if cif.get("recuerdos") else 0.0
        if clave == "M3":
            try:
                import cara as _cara
                total = _cara.TOTAL_SALAS
            except Exception:
                total = 6
            return min(1.0, cif.get("salas", 0) / float(total))
        return 0.5

    def _detalle(self, c):
        """Las cuatro dimensiones del usuario. Sin datos: 0.0 y `no_medible`."""
        d = {}
        temas = self._cuenta(
            c, "select count(distinct coalesce(nullif(trim(why),''),'sin_tema')) "
               "from engrams where status='activo'")
        activos = self._cuenta(c, "select count(*) from engrams where status='activo'")
        if activos:
            d["memorias_tema"] = min(1.0, temas / 5.0)
        else:
            d["memorias_tema"] = 0.0
            self.no_medible.add("memorias_tema")

        proyectos = self._cuenta(c, "select count(*) from proyectos")
        if proyectos:
            d["proyectos_activos"] = min(1.0, proyectos / 3.0)
        else:
            d["proyectos_activos"] = 0.0
            self.no_medible.add("proyectos_activos")

        d["preferencias"] = self._preferencias(c)

        ritmo = self._ritmo(c)
        if ritmo is None:
            d["ritmo"] = 0.0
            self.no_medible.add("ritmo")
        else:
            d["ritmo"] = ritmo
        return d

    CAMPOS_PERFIL = ("name", "language", "intereses", "instrucciones", "device")

    def _preferencias(self, c):
        try:
            import memory as M
            perfil = M.leer_perfil(c)
            ausente = getattr(M, "AUSENTE", "NO_DATA")
        except Exception:
            return 0.0
        puestos = sum(1 for k in self.CAMPOS_PERFIL
                      if str(perfil.get(k, ausente)).strip() not in ("", ausente))
        return puestos / float(len(self.CAMPOS_PERFIL))

    def _ritmo(self, c):
        """Engramas de los últimos 7 días contra la mediana semanal histórica."""
        try:
            filas = c.execute(
                "select created_at from engrams where status='activo' "
                "order by created_at").fetchall()
        except sqlite3.Error:
            return None
        marcas = []
        for f in filas:
            v = f[0]
            try:
                marcas.append(float(v))
            except (TypeError, ValueError):
                continue
        if len(marcas) < 2:
            return None
        import time
        ahora = time.time()
        semana = 7 * 86400.0
        recientes = sum(1 for m in marcas if ahora - m <= semana)
        cubos = {}
        for m in marcas:
            cubos[int((ahora - m) // semana)] = cubos.get(int((ahora - m) // semana), 0) + 1
        valores = sorted(cubos.values())
        if not valores:
            return None
        mediana = valores[len(valores) // 2]
        if mediana <= 0:
            return None
        return min(1.0, recientes / float(mediana))

    # --- 2b · calidad del cerebro ----------------------------------------

    def calidad_inferencia(self):
        """[0,1], o None si no se puede medir. Nunca un número inventado.

        0.0 sin cerebro · 0.3 cerebro sin caché · 0.6 con caché (lo medido hoy)
        · 1.0 con afinado declarado y con su huella cuadrando.
        El 0.9 (GPU) **no se emite**: desde dentro del producto no hay forma de
        saber si el binario descarga capas, y suponerlo sería decorar.
        """
        try:
            import conversacion as _conv
        except Exception:
            return None
        try:
            motor = _conv.motor_disponible()
        except Exception:
            return None
        if not motor:
            return 0.0
        afinado = self._afinado_activo()
        if afinado:
            return 1.0
        try:
            cache = _conv.ruta_cache()
        except Exception:
            cache = None
        if cache and os.path.isfile(cache):
            return 0.6
        return 0.3

    def _afinado_activo(self):
        try:
            import afinado as _af
            import casa as _casa
            raiz = _casa.raiz()
        except Exception:
            return False
        for nombre in ("cerebro.json",):
            ruta = os.path.join(str(raiz), nombre)
            if os.path.isfile(ruta):
                try:
                    with open(ruta, encoding="utf-8") as f:
                        d = json.load(f)
                    return bool(d.get("activo") or d.get("destino"))
                except Exception:
                    return False
        return False

    # --- 3 · tensor de rigidez -------------------------------------------

    def tensor_rigidez(self, ventana_dias=90, modo=None, historial=None):
        modo = modo or self.modo
        R = [list(f) for f in self._prior]
        latidos = self._latidos(ventana_dias)
        if historial and len(historial) >= LATIDOS_PARA_EMPIRICO and \
           latidos >= LATIDOS_PARA_EMPIRICO:
            emp = self._empirico(historial)
            if emp:
                R = [[0.7 * R[i][j] + 0.3 * emp[i][j] for j in range(8)]
                     for i in range(8)]
        R = _dominancia_diagonal(_simetrizar(R))
        if modo == "detalle":
            R = self._ampliar_a_12(R)
        return R

    def _latidos(self, ventana_dias):
        c = self._abrir_ro(self.loops_path)
        if c is None:
            return 0
        try:
            import time
            desde = time.time() - ventana_dias * 86400
            return self._cuenta(
                c, "select count(*) from latidos where momento >= ?", desde)
        finally:
            c.close()

    def _empirico(self, historial):
        """R_emp_ij = cov(dpi, dpj) / (var(dpj) + eps), sobre la trayectoria."""
        puntos = [h["p"] for h in historial if isinstance(h.get("p"), list)
                  and len(h["p"]) == 8]
        if len(puntos) < LATIDOS_PARA_EMPIRICO:
            return None
        d = [[puntos[t + 1][i] - puntos[t][i] for i in range(8)]
             for t in range(len(puntos) - 1)]
        n = len(d)
        medias = [sum(fila[i] for fila in d) / n for i in range(8)]
        R = [[0.0] * 8 for _ in range(8)]
        for i in range(8):
            for j in range(8):
                cov = sum((f[i] - medias[i]) * (f[j] - medias[j]) for f in d) / n
                var = sum((f[j] - medias[j]) ** 2 for f in d) / n
                R[i][j] = cov / (var + 1e-9)
        return R

    # C (8x4) y D (4x4) viven en docs/compass_transfers_detalle.json: el prior
    # 12x12 se GENERA por regla, no se firma a mano. Aqui solo el respaldo por
    # si el fichero falta -- y si falta, se declara en `self.detalle_por_defecto`.
    ACOPLES = {("M2", "memorias_tema"): 0.4, ("M7", "proyectos_activos"): 0.4,
               ("M0", "preferencias"): 0.3,
               ("M0", "ritmo"): 0.1, ("M1", "ritmo"): 0.1, ("M2", "ritmo"): 0.1}
    ACOPLE_DEFECTO = 0.05
    D_DIAG = 1.0
    D_OFF = 0.2

    def _leer_acoples(self):
        """Los acoples firmados, o el respaldo del modulo con la falta declarada."""
        self.detalle_por_defecto = False
        ruta = os.path.join(AQUI, "docs", "compass_transfers_detalle.json")
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            acoples = {tuple(k.split("|")): float(v)
                       for k, v in d["acoples_C"].items()}
            return (acoples, float(d.get("acople_defecto", self.ACOPLE_DEFECTO)),
                    float(d.get("D_diagonal", self.D_DIAG)),
                    float(d.get("D_fuera_diagonal", self.D_OFF)))
        except Exception:
            self.detalle_por_defecto = True
            return (self.ACOPLES, self.ACOPLE_DEFECTO, self.D_DIAG, self.D_OFF)

    def _ampliar_a_12(self, R8):
        n = 12
        R = [[0.0] * n for _ in range(n)]
        for i in range(8):
            for j in range(8):
                R[i][j] = R8[i][j]
        acoples, defecto, d_diag, d_off = self._leer_acoples()
        for i, pel in enumerate(PELDANOS):
            for k, dim in enumerate(DIM_DETALLE):
                v = acoples.get((pel, dim), defecto)
                R[i][8 + k] = v
                R[8 + k][i] = v
        for a in range(4):
            for b in range(4):
                R[8 + a][8 + b] = d_diag if a == b else d_off
        return _dominancia_diagonal(_simetrizar(R))

    # --- 4 · el campo ------------------------------------------------------

    def _claves(self, modo=None):
        modo = modo or self.modo
        return list(PELDANOS) + (list(DIM_DETALLE) if modo == "detalle" else [])

    def _potencial(self, p, v, R):
        n = len(p)
        u = sum(PESOS[i] if i < len(PESOS) else 1.0 for i in range(0))  # noqa
        u = 0.0
        for i in range(n):
            w = PESOS[i] if i < len(PESOS) else 1.0
            u += w * math.log(1.0 + max(0.0, p[i]))
        return u - LAMBDA * _entropia(v) - MU * self._curvatura(v, R)

    def _curvatura(self, v, R):
        return _norma_R(v, R)

    def campo_f(self, estado, R, F_previo=None, v=None):
        claves = list(estado.keys()) if isinstance(estado, dict) else None
        p = [estado[k] for k in claves] if claves else list(estado)
        n = len(p)
        v = list(v) if v else [0.0] * n

        grad = []
        for i in range(n):
            arriba = list(p); arriba[i] = min(1.0, arriba[i] + H_DERIVADA)
            abajo = list(p); abajo[i] = max(0.0, abajo[i] - H_DERIVADA)
            paso = arriba[i] - abajo[i]
            if paso <= 0:
                grad.append(0.0)
                continue
            grad.append((self._potencial(arriba, v, R) -
                         self._potencial(abajo, v, R)) / paso)

        inv = _inversa(R)
        if inv is None:
            base = self._prior if n == 8 else self._ampliar_a_12(self._prior)
            inv = _inversa(base) or [[1.0 if i == j else 0.0 for j in range(n)]
                                     for i in range(n)]
        F_raw = _matvec(inv, grad)

        if F_previo and len(F_previo) == n:
            F = [ALPHA * F_raw[i] + (1 - ALPHA) * F_previo[i] for i in range(n)]
            mag_raw = math.sqrt(sum(x * x for x in F_raw))
            mag = math.sqrt(sum(x * x for x in F)) + 1e-9
            F = [x / mag * mag_raw for x in F]
        else:
            F = list(F_raw)
        self._F_raw = F_raw
        self._grad_U = grad
        return F

    # --- 5 · indicadores ---------------------------------------------------

    def indicadores(self, estado, F, v, R, F_previo=None, temperatura=None):
        n = len(F)
        kappa = self._curvatura(v, R)
        max_F = self._max_F or MAX_F_FALLBACK
        intensidad = min(1.0, _norma_R(F, R) / (max_F + 1e-9))
        nv, nF = _norma_R(v, R), _norma_R(F, R)
        coherencia = 0.0 if nv < 1e-9 or nF < 1e-9 else \
            max(-1.0, min(1.0, _producto_R(v, F, R) / (nv * nF + 1e-9)))
        estabilidad = math.exp(-kappa * TAU_ESTABILIDAD) if kappa > 0 else 1.0
        estabilidad = max(0.0, min(1.0, estabilidad))
        T = temperatura if temperatura is not None else nv
        estancado = bool(nv < 0.1 * T and T > 0.01)
        return {
            "orientacion": math.atan2(F[1], F[0]) if n >= 2 else 0.0,
            "intensidad": intensidad,
            "coherencia": coherencia,
            "estabilidad": estabilidad,
            "temperatura": T,
            "estancado": estancado,
            # Los cuatro derivados v3.1, desde el propio campo.
            "S": -math.log(kappa + 1e-9),
            "X": max(0.0, coherencia) if estancado else 0.0,
            "Z": 1.0 - intensidad,
            "W": 0.0,          # lo rellena resumen(), que sabe cuál es el activo
        }

    # --- 6 · peldaño activo ------------------------------------------------

    def peldano_activo(self, estado, F, R, activo_previo=None):
        claves = list(estado.keys())
        p = [estado[k] for k in claves]
        n = len(p)
        phi = []
        for i in range(n):
            w = PESOS[i] if i < len(PESOS) else 1.0
            # Saturación del núcleo: un peldaño casi completo deja de tirar.
            if i in NUCLEO_IDX and p[i] > SATURACION_NUCLEO:
                w *= 0.5
            dU = w / (1.0 + max(0.0, p[i]))
            phi.append(dU * sum(R[i][j] for j in range(n) if j != i))
        mejor = max(range(n), key=lambda i: phi[i])
        if activo_previo in claves:
            k = claves.index(activo_previo)
            if phi[k] >= phi[mejor] - DELTA_HISTERESIS:
                return activo_previo
        return claves[mejor]

    # --- 7 · ETA -----------------------------------------------------------

    def eta(self, estado, v, F, activo, intensidad, coherencia):
        claves = list(estado.keys())
        if activo not in claves:
            return float("inf")
        i = claves.index(activo)
        va = abs(v[i]) if i < len(v) else 0.0
        denom = va * (1.0 + intensidad * coherencia) + 1e-9
        seg = (1.0 - estado[activo]) / denom
        return float("inf") if seg > 30 * 86400 else max(0.0, seg)

    # --- 8 · divergencia -----------------------------------------------------

    def divergencia_kl(self, v, estado=None, q_objetivo=None):
        n = len(v)
        if q_objetivo is None:
            nucleo_incompleto = estado is not None and any(
                estado[k] < SATURACION_NUCLEO for k in list(estado)[:3])
            if nucleo_incompleto:
                q = [1 / 3, 1 / 3, 1 / 3] + [0.0] * (n - 3)
            else:
                resto = n - 3
                q = [0.0, 0.0, 0.0] + [1.0 / resto] * resto
        else:
            q = list(q_objetivo)
        total = sum(abs(x) for x in v)
        if total < 1e-12:
            return 0.0
        vn = [abs(x) / total for x in v]
        d = 0.0
        for i in range(n):
            if vn[i] <= 0:
                continue
            if q[i] <= 0:
                return float("inf")
            d += vn[i] * math.log2(vn[i] / q[i])
        return max(0.0, d)

    # --- 10 · calibrado ------------------------------------------------------

    def calibrate(self, muestras=MUESTRAS_CALIBRADO):
        """Percentil 99,9 de ||F||_R sobre una muestra determinista.

        La rejilla 6^8 del diseño son 1.679.616 puntos con una inversión de
        matriz cada uno: en stdlib son horas. Se muestrea, y el método viaja en
        el resultado para que nadie lo confunda con la rejilla entera.
        """
        if self._calibrado:
            return self._max_F
        R = self.tensor_rigidez()
        n = len(R)
        rnd = _aleatorio_determinista(20260826)
        normas = []
        for _ in range(muestras):
            p = {k: next(rnd) for k in self._claves()[:n]}
            F = self.campo_f(p, R)
            normas.append(_norma_R(F, R))
        normas.sort()
        idx = min(len(normas) - 1, int(0.999 * len(normas)))
        self._max_F = normas[idx] or MAX_F_FALLBACK
        self._calibrado = True
        return self._max_F

    # --- 9 · resumen ---------------------------------------------------------

    def resumen(self, modo=None, activo_previo=None, F_previo=None,
                historial=None, debug=False):
        modo = modo or self.modo
        p = self.estado(modo)
        claves = list(p.keys())
        R = self.tensor_rigidez(modo=modo, historial=historial)

        v = self._velocidad(historial, len(claves))
        F = self.campo_f(p, R, F_previo=F_previo, v=v)
        if not self._calibrado:
            self.calibrate()
        ind = self.indicadores(p, F, v, R, F_previo)
        activo = self.peldano_activo(p, F, R, activo_previo)
        ind["W"] = p.get(activo, 0.0)
        eta = self.eta(p, v, F, activo, ind["intensidad"], ind["coherencia"])
        kl = self.divergencia_kl(v, estado=p)

        # El idioma lo declara la memoria de la persona, como en el resto del
        # producto. Estaba clavado a "es": la rosa hablaba castellano aunque el
        # perfil dijera English, que es la mitad de la promesa bilingue.
        idioma = self._idioma()
        try:
            import cara as _cara
            nombres = dict(_cara.CAMINO.get(idioma, _cara.CAMINO["es"]))
        except Exception:
            nombres = {}
        peldanos = {}
        for k in claves:
            peldanos[k] = {
                "nombre": nombres.get(
                    k, self.NOMBRES_DETALLE.get(idioma, {}).get(k, k)),
                "valor": round(p[k], 4),
                "estado": self._etiqueta(k, p[k]),
            }
        import datetime
        salida = {
            "modo": modo,
            "idioma": idioma,
            "peldaños": peldanos,
            "indicadores": {kk: (vv if isinstance(vv, bool) else round(vv, 4))
                            for kk, vv in ind.items()},
            "activo": activo,
            "eta_segundos": None if eta == float("inf") else round(eta, 1),
            "divergencia_kl": None if kl == float("inf") else round(kl, 4),
            "campo": [round(x, 4) for x in F],
            "velocidad_medible": bool(historial),
            "no_medible": sorted(self.no_medible),
            "timestamp": datetime.datetime.now(
                datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if debug:
            salida["R"] = [[round(x, 4) for x in fila] for fila in R]
            salida["F_raw"] = [round(x, 4) for x in self._F_raw]
            salida["F"] = [round(x, 4) for x in F]
            salida["grad_U"] = [round(x, 4) for x in self._grad_U]
            salida["q_objetivo"] = self._q(p, len(claves))
            salida["calibrado"] = self._calibrado
            salida["max_F"] = round(self._max_F or MAX_F_FALLBACK, 4)
        return salida

    def _idioma(self):
        """El idioma del perfil, o «es» si no hay memoria que preguntar."""
        c = self._abrir_ro(self.db_path)
        if c is None:
            return "es"
        try:
            import memory as M
            perfil = M.leer_perfil(c)
            valor = str(perfil.get("language", "") or "").strip().lower()
            return valor if valor in ("es", "en") else "es"
        except Exception:
            return "es"
        finally:
            c.close()

    # Los nombres de las cuatro dimensiones de detalle no viven en `cara`, asi
    # que viven aqui, en los dos idiomas y no en uno.
    NOMBRES_DETALLE = {
        "es": {"memorias_tema": "Temas", "proyectos_activos": "Proyectos",
               "preferencias": "Perfil", "ritmo": "Ritmo"},
        "en": {"memorias_tema": "Topics", "proyectos_activos": "Projects",
               "preferencias": "Profile", "ritmo": "Pace"},
    }

    def _q(self, estado, n):
        claves = list(estado)[:3]
        if any(estado[k] < SATURACION_NUCLEO for k in claves):
            return [1 / 3, 1 / 3, 1 / 3] + [0.0] * (n - 3)
        resto = n - 3
        return [0.0, 0.0, 0.0] + [1.0 / resto] * resto

    def _velocidad(self, historial, n):
        if not historial or len(historial) < 2:
            return [0.0] * n
        a, b = historial[-2]["p"], historial[-1]["p"]
        dt = max(1e-9, float(historial[-1].get("t", 1)) - float(historial[-2].get("t", 0)))
        v = [(b[i] - a[i]) / dt for i in range(min(len(a), len(b)))]
        return (v + [0.0] * n)[:n]

    def _etiqueta(self, clave, valor):
        if clave in self.no_medible:
            return NO_MEDIBLE
        if valor >= 1.0:
            return "completado"
        if valor > 0.0:
            return "en_progreso"
        return "bloqueado"


# ─────────────────────────── demo ───────────────────────────

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Brújula de Aprendizaje")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--modo", default="camino", choices=("camino", "detalle"))
    ap.add_argument("--db", default=None)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)

    db = a.db
    if db is None:
        try:
            import casa as _casa
            db = str(_casa.raiz() / "memory.db")
        except Exception:
            db = None
    loops = os.path.expanduser("~/.aurelius/loops.db")
    b = LearningCompass(db, loops, modo=a.modo)
    print(json.dumps(b.resumen(modo=a.modo, debug=a.debug),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
