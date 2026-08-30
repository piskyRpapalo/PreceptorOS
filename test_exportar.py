"""Puerta de Enlace de Privacidad · que lo que sale, salga limpio.

Esta suite existe porque la promesa del export es fuerte: se pega en una IA de
la nube y ya no se puede recoger. Cada caso comprueba una promesa concreta, y
el ultimo comprueba la mas importante — que cuando NO puede garantizar el
saneado, no escribe nada.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import guardrails as G       # noqa: E402
import memory as M           # noqa: E402

SUCIO_RUTA = "/home/marta/riego/regar.py"
SUCIO_IP = "192.168.50.90"
SUCIO_IP2 = "100.101.96.13"
SUCIO_SSH = "AAAAC3NzaC1lZDI1NTE5AAAAIKmQ2vT9wXyZ0aBcDeFgHiJkLmNoPqRsTuVwXyZ01234"
SUCIO_API = "sk-proj-Zz99Yy88Xx77Ww66"


class Exportar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="export_")
        pol = Path(self.tmp) / "policies.json"
        pol.write_text(json.dumps({
            "PRIVATE_IP": {"activa": True}, "HOME_PATH": {"activa": True},
            "NODE_PATH": {"activa": True, "nombres": ["la-torre", "la-fragua", "sin-rol"]},
        }), encoding="utf-8")
        (Path(self.tmp) / "roles.json").write_text(json.dumps({
            "la-torre": "nodo edge con CUDA", "la-fragua": "nodo ARM de lote",
        }), encoding="utf-8")
        G.POLICIES_PATH = str(pol)
        self.db = str(Path(self.tmp) / "memory.db")
        M.crear(self.db)
        with M.abrir(self.db) as c:
            M.asegurar_tablas(c); M.asegurar_busqueda(c)
            M.escribir_engrama(c, "El riego corre en la-fragua",
                why="Movido desde sin-rol",
                learned=f"Script en {SUCIO_RUTA}, sensor en {SUCIO_IP}. "
                        f"La la-torre ({SUCIO_IP2}) no participa. "
                        f"ssh-ed25519 {SUCIO_SSH} y OPENAI_API_KEY={SUCIO_API}")
        import exportar_contexto
        self.E = exportar_contexto

    def tearDown(self):
        G.POLICIES_PATH = None

    def texto(self):
        t, _, _ = self.E.exportar("riego", self.db)
        return t

    def test_ningun_secreto_sobrevive(self):
        t = self.texto()
        for s in (SUCIO_RUTA, SUCIO_IP, SUCIO_IP2, SUCIO_SSH, SUCIO_API):
            self.assertNotIn(s, t, f"sobrevivio: {s}")

    def test_los_nombres_de_maquina_se_vuelven_papeles(self):
        # Un rol le sirve a la IA externa para razonar; [REDACTED] solo le dice
        # que ahi habia algo. Se gana privacidad y utilidad a la vez.
        t = self.texto()
        self.assertNotIn("la-torre", t)
        self.assertNotIn("la-fragua", t)
        self.assertIn("nodo edge con CUDA", t)

    def test_un_nombre_sin_rol_no_queda_al_descubierto(self):
        # El descuido de no describir un nodo no puede costar una fuga.
        t = self.texto()
        self.assertNotIn("sin-rol", t)
        self.assertIn("otro nodo del equipo", t)

    def test_la_cabecera_declara_lo_que_el_filtro_no_cubre(self):
        # La promesa honesta no es «no queda nada»: es «esto es lo que no miro».
        t = self.texto()
        self.assertIn("Qué NO garantiza este filtro", t)
        self.assertIn("webhook-entrante", t)

    def test_la_cabecera_dice_que_se_quito_y_cuanto(self):
        t = self.texto()
        for pol in ("HOME_PATH", "PRIVATE_IP", "SSH_PUBLIC_KEY", "API_KEY"):
            self.assertIn(pol, t, f"no se declara haber redactado {pol}")

    def test_las_pistas_senalan_sin_redactar(self):
        with M.abrir(self.db) as c:
            M.escribir_engrama(c, "riego con correo",
                learned="avisa a marta.lopez@example.com si falla")
        t = self.texto()
        self.assertIn("Revisa estas líneas", t)
        # senalar NO es redactar: el correo sigue ahi, visible y marcado
        self.assertIn("marta.lopez@example.com", t)

    def test_sin_memoria_no_escribe_nada(self):
        # Falla cerrado. Un export a medias es peor que ninguno: nadie revisa
        # lo que ya cree limpio.
        with self.assertRaises(self.E.NoSePuedeExportar):
            self.E.exportar("riego", str(Path(self.tmp) / "no-existe.db"))


class PortapapelesNoSecuestraLaSalida(unittest.TestCase):
    """El export tiene que poder canalizarse. `| head`, `| tee`, un script, un CI.

    Medido el 2026-08-30: `xclip` se DEMONIZA para servir la seleccion y, al
    hacerlo, heredaba la salida de su padre. Con la salida en una tuberia, el
    extremo de escritura no se cerraba nunca: el proceso de Python ya habia
    terminado y `head` seguia bloqueado en `anon_pipe_read`, con `/proc`
    enseñando el fd 1 de `xclip` sobre el mismo `pipe:[...]`.

    Un comando que no se puede canalizar no se puede automatizar, que es justo
    lo que este export existe para permitir.
    """

    def test_copiar_no_deja_la_tuberia_abierta(self):
        """Se corre en un hijo con la salida en tuberia y se exige EOF.

        Se comprueba el COMPORTAMIENTO (la tuberia se cierra), no la llamada
        (que se pase DEVNULL). Un test sobre el argumento pasaria igual el dia
        que alguien añada otra herramienta de portapapeles y se olvide de ella.
        """
        import shutil
        import subprocess

        import exportar_contexto as E
        disponible = next((o[0] for o in E.PORTAPAPELES if shutil.which(o[0])), None)
        if not disponible:
            self.skipTest("no hay herramienta de portapapeles en este sistema")

        guion = (
            "import sys; sys.path.insert(0, %r)\n"
            "import exportar_contexto as E\n"
            "E.copiar('texto de prueba')\n"
        ) % str(Path(__file__).resolve().parent)

        p = subprocess.Popen([sys.executable, "-c", guion],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            # Si algun hijo se queda con el extremo de escritura, esto NO
            # devuelve y el timeout salta. Ese timeout ES el fallo que
            # describe el docstring.
            p.communicate(timeout=25)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
            self.fail(
                f"la tuberia sigue abierta tras terminar: {disponible} heredo la "
                "salida y se quedo vivo. El export no se puede canalizar")


if __name__ == "__main__":
    unittest.main(verbosity=2)
