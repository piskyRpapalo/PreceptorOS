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
import sys
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

DB_PATH = os.path.expanduser("~/.aurelius/memory.db")
MANIFIESTO_PATH = os.path.expanduser("~/.aurelius/manifiesto_fuga.txt")

NO_DATA = "NO_DATA"

# El ritmo de las pausas, mismo interruptor que `tono`. A 0 la fuga no espera:
# una suite que se sienta a ver las pausas se deja de correr.
_RITMO = float(os.environ.get("AURELIUS_RITMO", "1.0"))


class FugaMuseo:
    """Motor de la Fuga del Museo."""

    def __init__(self, idioma: str = "es"):
        self.idioma = idioma
        self.db = sqlite3.connect(DB_PATH)
        self.db.row_factory = sqlite3.Row
        self.modo_oscuro = False  # Modo Ojos Cerrados
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

        # Detectar si hay fuga en curso
        sala_actual = self._detectar_reanudacion()

        if sala_actual is None:
            # Fuga nueva: ritual de entrada
            self._ritual_entrada()
            sala_actual = 1

        # Ejecutar salas desde donde se quedó
        for sala_num in range(sala_actual, 7):
            self._ejecutar_sala(sala_num)
            if sala_num < 6:
                self._marcar_sala_completada(sala_num)
                self._marcar_sala_entrada(sala_num + 1)

        # Fuga completa: ritual de salida
        self._ritual_salida()
        print("\n✓ Fuga completada. Manifiesto firmado en:")
        print(f"  {MANIFIESTO_PATH}")

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
        # El ritual de salida ya hace el trabajo
        self._marcar_sala_completada(6)

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
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO fuga_sala (sala, nombre, entrado_en, estado)
            VALUES (?, 'NO_DATA', datetime('now'), 'entrada')
        """, (sala_num,))
        self.db.commit()

    def _marcar_sala_completada(self, sala_num: int):
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE fuga_sala
            SET salido_en = datetime('now'), estado = 'completada'
            WHERE sala = ?
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
        """Escribe de golpe lo que la sala dejo anotado. Cero DELETE."""
        cursor = self.db.cursor()
        for clave, valor in self._pendiente.items():
            cursor.execute("""
                INSERT OR REPLACE INTO profile (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
            """, (clave, valor))
        self.db.commit()
        self._pendiente.clear()

    def _guardar_fuente(self, ruta: str, estado: str):
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO fuentes (ruta_o_url, sha256, tipo, equipada_en, estado)
            VALUES (?, 'NO_DATA', 'NO_DATA', datetime('now'), ?)
        """, (ruta, estado))
        self.db.commit()

    def _guardar_cita(self, cita: str):
        # Guardar como engram en el salón de los recuerdos
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO engrams (texto, creado_en, tipo)
            VALUES (?, datetime('now'), 'cita_forja')
        """, (self._dato(cita),))
        self.db.commit()

    # --- Helpers de comunicación ---

    def _hablar(self, texto: str, pausa: float = 0.5):
        """Habla con voz.py si existe, si no imprime."""
        print(f"\n[AURELIUS] {texto}")

        if voz and voz.piper_disponible():
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                ruta = tmp.name
            try:
                voz.hablar(texto, ruta)
                self._reproducir_wav(ruta)
            except Exception as e:
                pass  # Si falla, ya está impreso en texto
            finally:
                if os.path.exists(ruta):
                    os.unlink(ruta)

        if _RITMO > 0:
            time.sleep(pausa * _RITMO)

    def _preguntar(self, pregunta: str, opciones: list[str], default: str) -> str:
        """Pregunta con opciones. Usa voz si existe."""
        print(f"\n{pregunta}")
        for i, op in enumerate(opciones, 1):
            print(f"  {i}) {op}")
        print(f"  [Enter para: {default}]")

        if voz and voz.piper_disponible():
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                ruta = tmp.name
            try:
                texto_voz = pregunta + ". Opciones: " + ", ".join(opciones)
                voz.hablar(texto_voz, ruta)
                self._reproducir_wav(ruta)
            except:
                pass
            finally:
                if os.path.exists(ruta):
                    os.unlink(ruta)

        # Intentar oído primero
        if oido and oido.oido_disponible():
            print("  (habla ahora, o escribe un número)")
            texto = oido.grabar_y_transcribir(duracion_seg=5, idioma=self.idioma)
            if texto:
                print(f"  [OÍDO] {texto}")
                # Buscar la opción en el texto
                for op in opciones:
                    if op in texto.lower():
                        return op
                # Si no coincide, usar default
                return default

        # Fallback: input por teclado
        while True:
            try:
                resp = input("> ").strip()
                if not resp:
                    return default
                if resp.isdigit():
                    idx = int(resp) - 1
                    if 0 <= idx < len(opciones):
                        return opciones[idx]
                # Buscar coincidencia parcial
                for op in opciones:
                    if op in resp.lower():
                        return op
                print(f"  No entendí. Elige un número del 1 al {len(opciones)}.")
            except (EOFError, KeyboardInterrupt):
                return default

    def _preguntar_libre(self, prompt: str) -> str:
        """Pregunta abierta. Usa voz si existe."""
        print(f"\n{prompt}")

        if voz and voz.piper_disponible():
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                ruta = tmp.name
            try:
                voz.hablar(prompt, ruta)
                self._reproducir_wav(ruta)
            except:
                pass
            finally:
                if os.path.exists(ruta):
                    os.unlink(ruta)

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
        """Reproduce un WAV con el reproductor disponible."""
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
