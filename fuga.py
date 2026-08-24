#!/usr/bin/env python3
"""fuga.py · El motor de la Fuga del Museo (M3 · HEGEMONIKON).

Orquesta las 6 salas del museo, gestiona el Modo Ojos Cerrados,
y usa voz.py + oido.py como capacidades opcionales.

Doctrina:
- Si voz.py u oido.py fallan, la fuga continúa en texto plano.
- Nunca bloquea. Siempre devuelve control al usuario.
- La memoria vive en SQLite (memory.db), no en el código.
"""
from __future__ import annotations

import sqlite3
import os
import re
import sys
import tempfile
import time
from typing import Optional
from datetime import datetime

# Importar capacidades opcionales
try:
    import voz
except ImportError:
    voz = None

try:
    import oido
except ImportError:
    oido = None

try:
    import generar_leitmotivs
except ImportError:
    generar_leitmotivs = None

import silencio as _silencio
import entorno as _entorno

DB_PATH = os.path.expanduser("~/.aurelius/memory.db")
MANIFIESTO_PATH = os.path.expanduser("~/.aurelius/manifiesto_fuga.txt")

NO_DATA = "NO_DATA"

# El esquema de M3 vive AQUI, en el producto. Hasta D79 no vivia en ninguna
# parte: `memory.py` no conoce estas tablas y `fuga.py` no las creaba, asi que
# M3 solo funcionaba en una maquina donde alguien las hubiera hecho a mano. La
# unica copia del esquema estaba en el setUp de la suite -- una prueba
# fabricando la tabla que iba a comprobar.
#
# `minutos` es una MEDIDA: -1 significa "no medido", no "cero minutos". Es la
# frontera que pide la doctrina -- una fila medida y una declarada no se
# mezclan, y un 0 que puede querer decir las dos cosas ya las ha mezclado.
ESQUEMA = """
CREATE TABLE IF NOT EXISTS fuga_sala (
    sala INTEGER PRIMARY KEY CHECK (sala BETWEEN 1 AND 6),
    nombre TEXT NOT NULL DEFAULT 'NO_DATA',
    entrado_en TEXT NOT NULL DEFAULT (datetime('now')),
    salido_en TEXT NOT NULL DEFAULT 'NO_DATA',
    minutos INTEGER NOT NULL DEFAULT -1,
    estado TEXT NOT NULL DEFAULT 'entrada'
        CHECK (estado IN ('entrada', 'completada', 'pausada')),
    concepto TEXT NOT NULL DEFAULT 'NO_DATA'
);
CREATE TABLE IF NOT EXISTS fuentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ruta_o_url TEXT NOT NULL DEFAULT 'NO_DATA',
    sha256 TEXT NOT NULL DEFAULT 'NO_DATA',
    tipo TEXT NOT NULL DEFAULT 'NO_DATA',
    equipada_en TEXT NOT NULL DEFAULT (datetime('now')),
    estado TEXT NOT NULL DEFAULT 'sin_declarar'
        CHECK (estado IN ('sin_declarar', 'declarada', 'equipada', 'retirada'))
);
"""

# Cuantas salas hay, y cual es la larga. La 3 pregunta cinco cosas: avisarlo
# no es un adorno, es la diferencia entre elegir seguir y que te pillen.
TOTAL_SALAS = 6
SALA_LARGA = 3

# Cuantas salas medidas hacen falta para hablar de tiempo. Con una sola, la
# "media" es esa sala: no es una media, es una anecdota con decimales.
MINIMO_PARA_ESTIMAR = 2

# El ritmo de las pausas, mismo interruptor que `tono`. A 0 la fuga no espera:
# una suite que se sienta a ver las pausas se deja de correr.
_RITMO = float(_entorno.leer("RITMO", "1.0"))


# Cuantas veces se vuelve a preguntar antes de tomar el defecto DICIENDOLO.
REINTENTOS = 8

# Los numeros dichos en voz alta. Whisper transcribe "dos", no "2", y hasta
# seis basta: no hay pregunta con mas opciones que salas.
NUMEROS_DICHOS = {
    "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "la una": 1, "el uno": 1,
}


def numero_dicho(texto: str, cuantas: int):
    """El numero que hay en `texto`, o None si no hay ninguno valido.

    None NO es "no entendi, tira con el defecto": es "esto no es un numero", y
    quien llama tiene que rechazarlo en voz alta. Un fuera de rango tambien es
    None -- decir "siete" cuando hay cuatro opciones es tan invalido como
    decir "Carlos", y merece el mismo rechazo con los numeros que valen.
    """
    if not texto:
        return None
    limpio = texto.strip().lower().strip(".,;:!¡?¿'\" ")

    digitos = re.findall(r"\d+", limpio)
    if digitos:
        # Solo si el texto es ese numero y nada mas: "el 3" vale, "tengo 3
        # hijos" no es una eleccion, es una frase.
        if len(digitos) == 1 and re.fullmatch(r"[^\d]*\d+[^\d]*", limpio):
            n = int(digitos[0])
            return n if 1 <= n <= cuantas else None
        return None

    n = NUMEROS_DICHOS.get(limpio)
    if n is None:
        # "el dos", "opción tres": una sola palabra-numero en la frase.
        palabras = [NUMEROS_DICHOS[p] for p in limpio.split()
                    if p in NUMEROS_DICHOS]
        if len(palabras) != 1:
            return None
        n = palabras[0]
    return n if 1 <= n <= cuantas else None


# --- el permiso del gerente ------------------------------------------------

PERMISO_GERENTE = "permiso_gerente"

# Lo que M3 escribe sobre la persona. Es lo que el permiso protege, y esta
# aqui y no repartido por las salas para que se pueda leer de un vistazo QUE
# se esta pidiendo permiso para leer.
CLAVES_M3 = (
    "como_llamarte", "como_hablar", "dispositivo_tipo", "sistema_operativo",
    "proyecto_vital", "triunfo_deseado", "laguna_reconocida",
    "fuentes_que_sigue", "restriccion_dura", "frontera_politica",
)


class SinPermiso(PermissionError):
    """Se pidio el perfil de M3 y la persona no ha dicho que si.

    Levanta en vez de devolver un diccionario vacio a proposito. Vacio se
    confunde con "no contesto nada", y son cosas distintas: una es no tener
    datos y la otra es tenerlos y que no sean tuyos.
    """


def permiso_concedido(db) -> bool:
    """¿Dijo que si? Fila ausente = no. Nunca un error, nunca otro defecto.

    Que la ausencia valga 'no' es la mitad del asunto: una base recien creada,
    una fila que nunca se escribio y una sesion que se corto antes de la
    pregunta tienen que dar todas la misma respuesta, y tiene que ser la que
    no entrega nada.
    """
    try:
        fila = db.execute("SELECT value FROM profile WHERE key = ?",
                          (PERMISO_GERENTE,)).fetchone()
    except sqlite3.Error:
        return False
    if fila is None:
        return False
    return str(fila[0]).strip().lower() in ("si", "sí")


def perfil_para_gerente(db) -> dict:
    """La UNICA puerta por la que sale el perfil de M3.

    La comprobacion vive aqui dentro y no en quien llama, que es la diferencia
    entre un permiso y una costumbre: si estuviera en el llamante, bastaria un
    llamante nuevo que no la conociera -- y siempre hay un llamante nuevo.

    Devuelve solo lo que M3 escribio y solo si hay permiso. NO_DATA se
    devuelve tal cual: la ausencia tambien es del perfil.
    """
    if not permiso_concedido(db):
        raise SinPermiso(
            "el perfil de M3 es memoria de la persona y no ha dado permiso "
            f"para leerlo (profile.{PERMISO_GERENTE} ausente o distinto de 'si')")
    marcadores = ",".join("?" * len(CLAVES_M3))
    return {f["key"]: f["value"] for f in db.execute(
        f"SELECT key, value FROM profile WHERE key IN ({marcadores})",
        CLAVES_M3)}


def hay_fuga_pendiente(ruta=None) -> bool:
    """¿Hay un museo a medias en esta base? Mirar no crea nada.

    Se usa desde `aurelius.ofrecer_m3` para decidir si se ofrece entrar o
    volver. Abre en solo lectura y se traga cualquier error: una base sin las
    tablas de M3 no es un fallo, es alguien que todavia no ha jugado.
    """
    ruta = ruta or DB_PATH
    if not os.path.isfile(ruta):
        return False
    try:
        con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    except sqlite3.Error:
        return False
    try:
        fila = con.execute(
            "SELECT 1 FROM fuga_sala WHERE estado IN ('entrada','pausada') "
            "LIMIT 1").fetchone()
        return fila is not None
    except sqlite3.Error:
        return False
    finally:
        con.close()


def texto_progreso(medidas, restantes) -> str:
    """Lo que se le dice a la persona al acabar una sala. Funcion pura.

    `medidas` son los minutos MEDIDOS de las salas ya cerradas -- solo los
    medidos, nunca un -1. `restantes` son los numeros de sala que faltan.

    La regla es de D76 y es literal: una barra que muestra lo que no puede
    medir es falsa. Nadie ha cruzado las seis salas todavia, asi que no hay un
    "tiempo tipico" que traerse de ninguna parte. Solo se habla de minutos
    cuando los minutos son SUYOS, y hacen falta dos salas para que la palabra
    "media" signifique algo. Antes de eso se dice lo unico que se sabe de
    verdad: cuantas quedan.
    """
    if not restantes:
        return "No queda ninguna. La ultima puerta es la de fuera."

    cuantas = len(restantes)
    plural = "salas" if cuantas != 1 else "sala"
    frase = f"Quedan {cuantas} {plural}."

    if len(medidas) >= MINIMO_PARA_ESTIMAR:
        media = sum(medidas) / len(medidas)
        if media < 1:
            frase = f"Vas a menos de un minuto por sala. {frase}"
        else:
            frase = f"Vas a unos {round(media)} minutos por sala. {frase}"

    if SALA_LARGA in restantes:
        frase += (f" La {SALA_LARGA} es la larga: pregunta cinco cosas, "
                  "y con una contestada ya se sale.")
    return frase


class FugaMuseo:
    """Motor de la Fuga del Museo."""

    def __init__(self, idioma: str = "es"):
        self.idioma = idioma
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(ESQUEMA)
        self.db.commit()
        self.modo_oscuro = False  # Modo Ojos Cerrados
        # True si la persona pidio parar. Lo lee `ejecutar` para dejar de
        # abrir salas sin cortar nada a la mitad.
        self.parado = False
        # Lo que la sala EN CURSO ha contestado y todavia no esta en disco.
        # Ver `_guardar_perfil`: una sala a medias no deja media persona.
        self._pendiente: dict[str, str] = {}

    def cerrar(self):
        self.db.close()

    # --- API principal ---

    def ejecutar(self):
        """Punto de entrada de la fuga."""
        print("\n" + "=" * 60)
        print("M3 · HEGEMONIKON · La Fuga del Museo")
        print("=" * 60)

        # Los leitmotivs se fabrican aqui la primera vez. Viajan como
        # generador, no como seis WAV en el repo, y hasta D78 un clon limpio
        # se quedaba mudo porque nadie ejecutaba el generador. `asegurar` no
        # levanta: si no se puede escribir, M3 sigue en silencio.
        if generar_leitmotivs is not None and voz is not None:
            generar_leitmotivs.asegurar(voz.SONIDOS_DIR)

        # Detectar si hay fuga en curso
        sala_actual = self._detectar_reanudacion()

        if sala_actual is None:
            # Fuga nueva: ritual de entrada
            self._ritual_entrada()
            sala_actual = 1

        # Ejecutar salas desde donde se quedó. Cada sala se cierra a si misma
        # en `_salir_sala`: aqui no se vuelve a marcar nada, que era lo que
        # hacia el bucle anterior -- marcaba completada la sala y de entrada la
        # siguiente, pisando `entrado_en` antes de que nadie hubiera entrado y
        # dejando la medida del tiempo sin sentido.
        for sala_num in range(sala_actual, TOTAL_SALAS + 1):
            self._ejecutar_sala(sala_num)
            if not self._ofrecer_continuar(sala_num):
                return False

        # Fuga completa: ritual de salida
        self._ritual_salida()
        print("\n✓ Fuga completada. Manifiesto firmado en:")
        print(f"  {MANIFIESTO_PATH}")
        return True

    # --- Detección de estado ---

    def _detectar_reanudacion(self) -> Optional[int]:
        """Devuelve el número de sala donde se quedó, o None si es nueva."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT sala, estado FROM fuga_sala
            WHERE estado IN ('entrada', 'pausada')
            ORDER BY sala
        """)
        fila = cursor.fetchone()
        if fila:
            sala = fila["sala"]
            estado = fila["estado"]
            print(f"\n⚡ Reanudando fuga desde sala {sala} (estado: {estado})")
            return sala
        return None

    # --- Rituales ---

    def _ritual_entrada(self):
        """Ritual de entrada: el tropiezo + Modo Ojos Cerrados."""
        self._hablar(
            "Has tirado algo. Un busto. Mío, por lo visto. "
            "No viene nadie. Las cámaras de esta ala graban a un disco "
            "que hace años que nadie abre. "
            "Llevo mucho tiempo en ese pedestal. Me gustaría salir. "
            "Tú tienes un bolsillo.",
            pausa=0.8
        )

        # Modo Ojos Cerrados
        modo = self._preguntar(
            "Antes de andar: ¿tus ojos descansan? "
            "Di 'a oscuras' y guío solo con voz. "
            "Di 'linterna' y además te describo lo que hay en pantalla.",
            opciones=["a oscuras", "linterna"],
            default="linterna"
        )
        self.modo_oscuro = (modo == "a oscuras")

        # Declaración de capacidades
        caps = []
        if voz and voz.piper_disponible():
            caps.append("voz sí")
        else:
            caps.append("voz no")
        if oido and oido.oido_disponible():
            caps.append("oídos sí")
        else:
            caps.append("oídos no")

        self._hablar(
            f"Lo que tengo aquí: {' / '.join(caps)}. "
            "Sin oídos, escribes. Nada de esta misión necesita lo que no tengo.",
            pausa=0.5
        )

        # Inicializar sala 1
        self._marcar_sala_entrada(1)

    def _ritual_salida(self):
        """Ritual de salida: firma del manifiesto."""
        self._hablar(
            "Estamos fuera. Date la vuelta una vez y luego ya no. "
            "Aquí es donde vives ahora, y tiene cuatro habitaciones. "
            "El salón son tus recuerdos. El dormitorio eres tú. "
            "El altar es el manifiesto. El taller está vacío.",
            pausa=1.0
        )

        # El Óbolo: preguntar algo de la sala 4
        self._hablar(
            "Antes de firmar: una de las cuatro cosas de la sala de la vigilia. "
            "La que sea. Dímela con tus palabras.",
            pausa=1.5
        )
        respuesta = self._preguntar_libre("(escribe o habla)")
        if not respuesta:
            self._hablar("Interesante. ¿Qué parte se resiste?")

        # Generar manifiesto
        self._generar_manifiesto()

        self._hablar(
            "Fírmalo y le saco la huella. "
            "Una cosa más antes de cerrar: elige un día y una hora. "
            "No un objetivo. Una cita. "
            "Las puertas del museo quedan detrás.",
            pausa=1.2
        )

        cita = self._preguntar_libre("¿Cuándo nos vemos de nuevo?")
        self._guardar_cita(cita)

    # --- Ejecución de salas ---

    def _ejecutar_sala(self, sala_num: int):
        """Ejecuta una sala completa."""
        metodos = {
            1: self._sala_prohairesis,
            2: self._sala_safehouse,
            3: self._sala_horme,
            4: self._sala_prosoche,
            5: self._sala_katalepsis,
            6: self._sala_hupexairesis,
        }
        metodo = metodos.get(sala_num)
        if metodo:
            metodo()

    def _sala_prohairesis(self):
        """Sala 1: El Nombre."""
        self._entrar_sala(1, "PROHAIRESIS · El Nombre")

        self._hablar(
            "Lo primero en una fuga: ¿cómo te llamo cuando importe? "
            "No tu nombre legal. Ese al que respondes.",
            pausa=1.0
        )

        nombre = self._preguntar_libre("Tu nombre (o el que usas aquí):")
        self._guardar_perfil("como_llamarte", nombre)

        tono = self._preguntar(
            "¿Cómo quieres que te hable?",
            opciones=["cercano", "formal", "técnico", "poético"],
            default="cercano"
        )
        self._guardar_perfil("como_hablar", tono)

        self._hablar(
            "Anotado. No enviado a ninguna parte: escrito en el fichero de tu bolsillo. "
            "Esa placa de ahí fuera dice cómo me catalogaron. "
            "Tú acabas de decir cómo me llamo.",
            pausa=0.8
        )

        self._salir_sala(1, concepto="identidad digital")

    def _sala_safehouse(self):
        """Sala 2: El Refugio."""
        self._entrar_sala(2, "SAFEHOUSE · El Refugio")

        self._hablar(
            "¿Dónde estoy ahora mismo? ¿Teléfono, o una máquina con teclado? "
            "Lo pregunto porque a partir de aquí eso no es un aparato. "
            "Es el único suelo que tenemos.",
            pausa=1.0
        )

        dispositivo = self._preguntar(
            "¿Qué dispositivo usas?",
            opciones=["teléfono", "portátil", "sobremesa", "otro"],
            default="teléfono"
        )
        self._guardar_perfil("dispositivo_tipo", dispositivo)

        so = self._preguntar_libre("¿Qué sistema operativo? (si lo sabes, si no, escribe 'no sé')")
        # Sin `if so else "NO_DATA"`: eso lo hace `_dato`, y lo hace en un solo
        # sitio. Repetirlo por sala es tener cuatro reglas que dicen lo mismo
        # hasta el dia que una deja de decirlo.
        self._guardar_perfil("sistema_operativo", so)

        self._hablar(
            "Entonces ese es el refugio. Declarado, no supuesto. "
            "El museo te guarda el abrigo en la taquilla. "
            "Nosotros no usamos la taquilla.",
            pausa=0.8
        )

        self._salir_sala(2, concepto="frontera física")

    def _sala_horme(self):
        """Sala 3: El Empeño."""
        self._entrar_sala(3, "HORMĒ · El Empeño")

        # Momento 1 del permiso: se PROMETE antes de preguntar nada, y se dice
        # cual es el defecto. Prometerlo despues de que haya contestado seria
        # pedirle permiso para algo que ya le has sacado.
        self._hablar(
            "Antes de nada, un trato. Lo que digas aquí es tuyo y se queda en "
            "tu fichero. Al salir de esta sala te preguntaré si dejas que lo "
            "lea el que te ayuda a trabajar. Si no contestas, o si esta sesión "
            "se corta ahora mismo, la respuesta es NO. No hay que hacer nada "
            "para que sea no.",
            pausa=1.0)

        self._hablar(
            "Ahora la parte larga, así que lo digo claro: "
            "aquí hay cinco cosas y me debes una. "
            "Qué intentas construir. Qué contaría como ganar. "
            "Qué sabes que no sabes. A quién ya lees. "
            "Y qué no vas a soltar: horas, dinero, sueño. "
            "Contesta una y seguimos.",
            pausa=1.2
        )

        campos = [
            ("proyecto_vital", "¿Qué estás construyendo?"),
            ("triunfo_deseado", "¿Qué contaría como ganar?"),
            ("laguna_reconocida", "¿Qué sabes que no sabes?"),
            ("fuentes_que_sigue", "¿A quién ya lees?"),
            ("restriccion_dura", "¿Qué no vas a soltar?"),
        ]

        respuestas = {}
        for campo, pregunta in campos:
            resp = self._preguntar_libre(f"{pregunta} (o Enter para saltar)")
            respuestas[campo] = self._dato(resp)

        for campo, valor in respuestas.items():
            self._guardar_perfil(campo, valor)

        self._hablar(
            f"{len([v for v in respuestas.values() if v != NO_DATA])} de 5 contestadas. "
            "Las otras se quedan como NO_DATA hasta que las llenes. "
            "No es un hueco del fichero. Es el fichero siendo honesto.",
            pausa=1.0
        )

        # Momento 2: se PREGUNTA, y la respuesta es una fila mas del perfil.
        # Se anota como todo lo demas de la sala, asi que si la sala se
        # abandona aqui no queda un permiso suelto sin las respuestas que
        # protegia -- ni un 'si' que nadie llego a decir del todo.
        respuesta = self._preguntar(
            "Lo que acabas de contarme, ¿puede leerlo el que te ayuda a trabajar?",
            opciones=["no, solo para mí", "sí, puede leerlo"],
            default="no, solo para mí")
        concede = respuesta.startswith("sí")
        self._guardar_perfil(PERMISO_GERENTE, "si" if concede else "no")
        self._hablar(
            "Anotado que sí. Se puede cambiar: es una fila, no un tatuaje."
            if concede else
            "Anotado que no. Sigue estando escrito, y sigue siendo solo tuyo.",
            pausa=0.8)

        self._salir_sala(3, concepto="superficie de ataque")

    def _sala_prosoche(self):
        """Sala 4: La Vigilia."""
        self._entrar_sala(4, "PROSOCHE · La Vigilia")

        self._hablar(
            "Mira arriba. Cámaras: eso es registro. "
            "El cable del marco es la alarma: la frontera de red. "
            "La puerta gorda del fondo es la caja fuerte: el cifrado. "
            "El cartel verde es la salida de emergencia: tu copia. "
            "Ya te sabías las cuatro. Solo no sabías que tenían nombre.",
            pausa=1.2
        )

        # Prueba del Fuego
        self._hablar(
            "El museo tiene WiFi gratis. Cobertura llena, sin contraseña. "
            "¿La cogemos?",
            pausa=1.0
        )

        wifi = self._preguntar(
            "¿Conectamos al WiFi del museo?",
            opciones=["sí", "no", "no lo sé"],
            default="no"
        )

        self._hablar(
            "Hayas dicho lo que hayas dicho: en una red abierta, "
            "cualquiera ve a dónde va tu tráfico. "
            "Te lo he preguntado porque no hay una respuesta que memorizar. "
            "Hay una pregunta que hacerse, y ya la tienes.",
            pausa=1.0
        )

        # Política de frontera
        self._hablar(
            "Firma tu política de frontera: "
            "qué no sale nunca, qué sale solo si lo dices en voz alta, "
            "y qué te da igual.",
            pausa=1.0
        )

        frontera = self._preguntar_libre("Tu política de frontera:")
        self._guardar_perfil("frontera_politica", frontera)

        self._salir_sala(4, concepto="política de frontera")

    def _sala_katalepsis(self):
        """Sala 5: El Asidero."""
        self._entrar_sala(5, "KATALĒPSIS · El Asidero")

        self._hablar(
            "Una fuente. Un libro, un manual, un artículo, un repositorio. "
            "No la mejor. La que vas a abrir de verdad un martes malo. "
            "Si aún no tienes ninguna, dilo: también es una respuesta.",
            pausa=1.2
        )

        fuente = self._preguntar_libre("Tu fuente ancla (o 'ninguna'):")

        if fuente and fuente.lower() not in ["ninguna", "no", "no tengo"]:
            self._guardar_fuente(fuente, "declarada")
            self._hablar(
                "Equipada. Una fuente que puedes comprobar vale por diez que recuerdas a medias.",
                pausa=0.8
            )
        else:
            self._guardar_fuente("sin_declarar", "sin_declarar")
            self._hablar(
                "Anotado con fecha. 'Sin declarar' es un dato real, no un hueco.",
                pausa=0.8
            )

        self._salir_sala(5, concepto="fuente verificable")

    def _sala_hupexairesis(self):
        """Sala 6: Camino a Casa (ya ejecutada en ritual_salida)."""
        self._entrar_sala(6, "HUPEXAIRESIS · Camino a Casa")
        # El ritual de salida ya hace el trabajo. Se cierra por `_salir_sala`
        # como las demas: es el unico sitio que vuelca lo anotado y mide.
        self._salir_sala(6, concepto="lo que no depende de ti")

    # --- Helpers de sala ---

    def _entrar_sala(self, num: int, nombre: str):
        """Toca leitmotiv + anuncia la sala."""
        print(f"\n{'─' * 60}")
        print(f"SALA {num} · {nombre}")
        print(f"{'─' * 60}")

        if voz and hasattr(voz, 'tocar_leitmotiv'):
            wav = voz.tocar_leitmotiv(num)
            if wav:
                self._reproducir_wav(wav)

        # Entrar en una sala descarta lo anotado y no volcado de la anterior:
        # si aquella no se cerro, aquello no era una respuesta.
        self._pendiente.clear()
        self._marcar_sala_entrada(num)
        self._actualizar_nombre_sala(num, nombre)

    # --- D1 · al acabar cada sala se ofrece parar -------------------------

    def _medidas(self) -> list[int]:
        """Los minutos de las salas cerradas y medidas. Nunca los no medidos."""
        return [f["minutos"] for f in self.db.execute(
            "SELECT minutos FROM fuga_sala "
            "WHERE estado = 'completada' AND minutos >= 0 ORDER BY sala")]

    def _restantes(self, desde: int) -> list[int]:
        """Las salas que quedan por recorrer despues de `desde`."""
        cerradas = {f["sala"] for f in self.db.execute(
            "SELECT sala FROM fuga_sala WHERE estado = 'completada'")}
        return [s for s in range(1, TOTAL_SALAS + 1)
                if s > desde and s not in cerradas]

    def _ofrecer_continuar(self, num: int) -> bool:
        """D1: al cerrar CADA sala, seguir o parar, diciendo lo que falta.

        Devuelve True si se sigue. Parar no es abandonar: la sala que se acaba
        de cerrar queda cerrada y la siguiente queda 'pausada', que es por
        donde `_detectar_reanudacion` entra la proxima vez.
        """
        restantes = self._restantes(num)
        if not restantes:
            return True

        self._hablar(texto_progreso(self._medidas(), restantes), pausa=0.6)
        sigue = self._preguntar(
            "¿Seguimos o lo dejamos aquí?",
            opciones=["seguimos", "lo dejo por hoy"],
            default="seguimos")
        if sigue == "seguimos":
            return True

        self._marcar_sala_pausada(restantes[0])
        self._hablar(
            f"Queda apuntado en la sala {restantes[0]}. "
            "Lo hecho está escrito; al volver seguimos por ahí, no desde el "
            "principio. Nada de esto caduca.",
            pausa=0.8)
        self.parado = True
        return False

    def _salir_sala(self, num: int, concepto: str):
        """Cierra la sala: primero se escribe lo contestado, luego se marca.

        En este orden a proposito. Marcar completada una sala cuyas respuestas
        no llegaron al disco seria firmar un recorrido que no existe.
        """
        self._volcar_pendiente()
        self._actualizar_concepto_sala(num, concepto)
        self._marcar_sala_completada(num)
        print(f"  ✓ Sala {num} completada: {concepto}")

    # --- Helpers de memoria ---

    def _marcar_sala_entrada(self, sala_num: int):
        """Entra en la sala sin pisar lo que la sala ya sabia.

        `ON CONFLICT DO UPDATE` y no `INSERT OR REPLACE`: lo segundo borra la
        fila y mete otra -- un DELETE con otro nombre, que ademas se llevaba
        por delante `concepto`, `salido_en` y `minutos` de una sala ya
        recorrida. Aqui solo se tocan las dos columnas que describen ESTA
        entrada.
        """
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO fuga_sala (sala, entrado_en, estado)
            VALUES (?, datetime('now'), 'entrada')
            ON CONFLICT(sala) DO UPDATE
                SET entrado_en = datetime('now'), estado = 'entrada'
        """, (sala_num,))
        self.db.commit()

    def _marcar_sala_completada(self, sala_num: int):
        """Cierra la sala y anota lo que TARDO, medido, no estimado.

        Los minutos salen de la resta entre `entrado_en` y ahora, en la propia
        base: es el reloj que ya escribio la entrada, asi que no hay dos
        relojes que puedan discrepar. Si `entrado_en` no se puede leer, se
        queda en -1 -- no medido -- y la estimacion no cuenta esta fila.
        """
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE fuga_sala
            SET salido_en = datetime('now'),
                estado = 'completada',
                minutos = CAST(
                    (julianday('now') - julianday(entrado_en)) * 1440 AS INTEGER)
            WHERE sala = ?
        """, (sala_num,))
        self.db.commit()

    def _marcar_sala_pausada(self, sala_num: int):
        """La persona dijo basta DESPUES de cerrar esta sala.

        La sala queda 'completada' -- se hizo entera -- y la SIGUIENTE queda
        'pausada', que es lo que `_detectar_reanudacion` busca al volver.
        Marcar pausada la que se acaba de terminar seria hacerla repetir.
        """
        if sala_num > TOTAL_SALAS:
            return
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO fuga_sala (sala, entrado_en, estado)
            VALUES (?, datetime('now'), 'pausada')
            ON CONFLICT(sala) DO UPDATE SET estado = 'pausada'
        """, (sala_num,))
        self.db.commit()

    def _actualizar_nombre_sala(self, sala_num: int, nombre: str):
        cursor = self.db.cursor()
        cursor.execute("UPDATE fuga_sala SET nombre = ? WHERE sala = ?", (nombre, sala_num))
        self.db.commit()

    def _actualizar_concepto_sala(self, sala_num: int, concepto: str):
        cursor = self.db.cursor()
        cursor.execute("UPDATE fuga_sala SET concepto = ? WHERE sala = ?", (concepto, sala_num))
        self.db.commit()

    @staticmethod
    def _dato(valor) -> str:
        """Una ausencia se llama NO_DATA. Nunca celda vacia.

        Enter en una pregunta y "no contestada" son el mismo hecho, y el
        fichero tiene que decirlo con la misma palabra que dice todo lo demas.
        Una cadena vacia en `profile` no se distingue de un fallo de escritura
        cuando alguien mire esto dentro de un ano.
        """
        limpio = (valor or "").strip()
        return limpio or NO_DATA

    def _guardar_perfil(self, clave: str, valor: str):
        """Anota una respuesta de la sala en curso. TODAVIA no la escribe.

        El perfil de M3 es memoria de la persona, y una sala abandonada a la
        tercera pregunta no describe a nadie: describe una interrupcion. Se
        vuelca entera al salir de la sala (`_salir_sala`) o no se vuelca. Asi
        "a medias" es un estado del recorrido -- `fuga_sala.estado='entrada'`,
        que ya existe y es una columna, no un borrado -- y no una fila suelta
        en `profile` que manana nadie sepa de donde salio.
        """
        self._pendiente[clave] = self._dato(valor)

    def _volcar_pendiente(self):
        """Escribe de golpe lo que la sala dejo anotado. Cero DELETE.

        El SQL ya no vive aqui: lo pone `memory.guardar_perfil`, unico escritor
        de `profile` en el arbol. Lo que habia era un `INSERT OR REPLACE`, que
        borra la fila entera para meter otra -- el dia que `profile` gane una
        columna que esta sentencia no nombre, reescribir una clave ya existente
        se la lleva por delante y la devuelve a su DEFAULT. Es el mismo motivo
        por el que `_marcar_sala_entrada` no lo usa; faltaba aplicarlo aqui.

        Un solo commit para el lote entero, como antes: el perfil de una sala
        se vuelca entero o no se vuelca.
        """
        import memory as _memory
        _memory.guardar_perfil(self.db, self._pendiente)
        self._pendiente.clear()

    def _guardar_fuente(self, ruta: str, estado: str):
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO fuentes (ruta_o_url, sha256, tipo, equipada_en, estado)
            VALUES (?, 'NO_DATA', 'NO_DATA', datetime('now'), ?)
        """, (ruta, estado))
        self.db.commit()

    def _guardar_cita(self, cita: str):
        """La cita se guarda como un recuerdo mas, por la puerta de M2.

        Antes esto hacia `INSERT INTO engrams (texto, creado_en, tipo)`, y esa
        tabla no existe: la `engrams` de verdad -- la que crea `memory.py` --
        tiene `what`, `why`, `where_ref`, `learned` y `origin`. La sentencia
        no habia funcionado nunca. No se veia porque la suite fabricaba en su
        setUp una `engrams` inventada con esas columnas: el test escribia la
        tabla que el propio test iba a comprobar, asi que las dos estaban de
        acuerdo y las dos estaban equivocadas.

        Se escribe con `memory.escribir_engrama` y no con SQL propio, para que
        el dia que M2 cambie la tabla haya UN sitio que lo sepa.

        `origin='intencion'` y no un valor nuevo: `engrams.origin` tiene un
        CHECK con tres valores, y una cita es exactamente lo que M2 ya llama
        intencion -- algo que la persona dice que va a hacer, no algo que le
        paso. Ensanchar el CHECK de M2 desde M3 seria que la mision de arriba
        le cambiase el canon a la de abajo por comodidad. De donde vino se
        dice en `why`, que es texto libre y para eso esta.
        """
        texto = self._dato(cita)
        if texto == NO_DATA:
            # `escribir_engrama` exige un `what`: un recuerdo sin qué no es un
            # recuerdo. Una cita que nadie dio no se inventa como "NO_DATA" en
            # el salón de los recuerdos -- simplemente no hay cita.
            return None
        import memory as _memory
        return _memory.escribir_engrama(
            self.db, what=texto,
            why="la cita que cerró la Fuga del Museo",
            origin="intencion")

    # --- Helpers de comunicación ---

    def _decir_en_voz(self, texto: str):
        """Lo dice en alto si hay garganta. Si no, no pasa nada: ya esta escrito.

        Estaba copiado tres veces (`_hablar`, `_preguntar`, `_preguntar_libre`)
        con tres `except` distintos, uno de ellos desnudo. Una sola copia y un
        solo `except`: si la voz falla, el texto ya salio por pantalla, que es
        la razon por la que la voz puede fallar sin bloquear nada.
        """
        if not (voz and voz.piper_disponible()):
            return
        ruta = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                ruta = tmp.name
            voz.hablar(texto, ruta)
            self._reproducir_wav(ruta)
        except Exception:
            pass
        finally:
            if ruta and os.path.exists(ruta):
                os.unlink(ruta)

    def _hablar(self, texto: str, pausa: float = 0.5):
        """Habla con voz.py si existe, si no imprime."""
        print(f"\n[AURELIUS] {texto}")
        self._decir_en_voz(texto)
        if _RITMO > 0:
            time.sleep(pausa * _RITMO)

    def _preguntar(self, pregunta: str, opciones: list[str], default: str) -> str:
        """Pregunta numerada. Numeros, y solo numeros, por los dos canales.

        D74: una pregunta numerada acepta numeros y el rechazo NOMBRA los que
        valen. La version anterior tenia dos gramaticas y ninguna dicha: por
        teclado colaba tambien el texto de la opcion, y por voz cualquier cosa
        que no fuese una opcion CAIA AL DEFECTO EN SILENCIO -- decir "Carlos"
        en "¿cómo quieres que te hable?" te dejaba en 'cercano' sin una
        palabra. Eso no es entender mal a alguien: es contestar por el.

        Una respuesta hablada se convierte a numero (digito o palabra) porque
        quien dicta un numero dice "dos", no "2"; lo que no es un numero se
        rechaza igual que por teclado, y se vuelve a preguntar.
        """
        numeros = ", ".join(str(i) for i in range(1, len(opciones) + 1))
        rechazo = (f"Eso no es un número. Aquí valen {numeros}"
                   f" -- o Enter para «{default}».")

        print(f"\n{pregunta}")
        for i, op in enumerate(opciones, 1):
            print(f"  {i}) {op}")
        print(f"  [Enter para: {default}]")

        self._decir_en_voz(pregunta + ". Opciones: " + ", ".join(
            f"{i}, {op}" for i, op in enumerate(opciones, 1)))

        for _ in range(REINTENTOS):
            dicho = None
            if oido and oido.oido_disponible():
                print("  (habla ahora, o escribe un número)")
                dicho = oido.grabar_y_transcribir(duracion_seg=5,
                                                  idioma=self.idioma)
                if dicho:
                    print(f"  [OÍDO] {dicho}")

            if dicho is None:
                try:
                    dicho = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    return default
                if not dicho:
                    return default

            elegido = numero_dicho(dicho, len(opciones))
            if elegido is not None:
                return opciones[elegido - 1]

            print(f"  {rechazo}")
            self._decir_en_voz(rechazo)

        # Agotados los intentos se toma el defecto, pero SE DICE. Un defecto
        # anunciado es una decision; un defecto callado es lo que arregla esta
        # funcion.
        self._hablar(f"No consigo entenderte. Me quedo con «{default}» y "
                     "seguimos; se puede cambiar luego.", pausa=0.5)
        return default

    def _preguntar_libre(self, prompt: str) -> str:
        """Pregunta abierta. Usa voz si existe."""
        print(f"\n{prompt}")
        self._decir_en_voz(prompt)

        # Intentar oído primero
        if oido and oido.oido_disponible():
            print("  (habla ahora, o escribe)")
            texto = oido.grabar_y_transcribir(duracion_seg=8, idioma=self.idioma)
            if texto:
                print(f"  [OÍDO] {texto}")
                return texto

        # Fallback: input por teclado
        try:
            return input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    def _reproducir_wav(self, ruta: str):
        """Reproduce un WAV con el reproductor disponible.

        El altavoz tambien obedece a `silencio.py`. Es la tercera puerta de
        hardware y la comprobacion vive dentro, como en las otras dos.
        """
        if _silencio.apagado():
            return
        import subprocess
        reproductores = ["aplay", "paplay", "ffplay -nodisp -autoexit", "vlc --play-and-exit"]
        for rep in reproductores:
            try:
                cmd = rep.split() + [ruta]
                subprocess.run(cmd, capture_output=True, timeout=30)
                return
            except:
                continue

    # --- Manifiesto ---

    def _generar_manifiesto(self):
        """Genera el manifiesto de la fuga."""
        cursor = self.db.cursor()

        # Leer perfil
        cursor.execute("SELECT key, value FROM profile WHERE key LIKE 'como_%' OR key LIKE 'dispositivo%' OR key LIKE 'proyecto%'")
        perfil = {row["key"]: row["value"] for row in cursor.fetchall()}

        # Leer salas
        cursor.execute("SELECT sala, nombre, concepto FROM fuga_sala ORDER BY sala")
        salas = cursor.fetchall()

        # Leer fuentes
        cursor.execute("SELECT ruta_o_url, estado FROM fuentes ORDER BY equipada_en DESC LIMIT 1")
        fuente = cursor.fetchone()

        # Generar texto del manifiesto
        lineas = [
            "# MANIFIESTO DE LA FUGA · M3 · HEGEMONIKON",
            f"# Firmado: {datetime.now().isoformat()}",
            "",
            "## Perfil",
        ]
        for k, v in sorted(perfil.items()):
            lineas.append(f"- {k}: {v}")

        lineas.append("")
        lineas.append("## Salas recorridas")
        for sala in salas:
            lineas.append(f"- Sala {sala['sala']}: {sala['nombre']} → {sala['concepto']}")

        lineas.append("")
        lineas.append("## Fuente ancla")
        if fuente:
            lineas.append(f"- {fuente['ruta_o_url']} (estado: {fuente['estado']})")
        else:
            lineas.append("- (ninguna)")

        lineas.append("")
        lineas.append("---")
        lineas.append("Firma (SHA256): [huella del cuerpo anterior]")

        cuerpo = "\n".join(lineas[:-2])  # Sin la línea de firma

        # Calcular huella
        import hashlib
        huella = hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()

        # Escribir manifiesto
        lineas[-1] = f"Firma (SHA256): {huella}"
        with open(MANIFIESTO_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))


def main():
    fuga = FugaMuseo(idioma="es")
    try:
        fuga.ejecutar()
    finally:
        fuga.cerrar()


if __name__ == "__main__":
    main()
