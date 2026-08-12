"""TANDA A · Fase 0 del filtro de privacidad · tests primero.

Estos once casos se escriben ANTES de que exista guardrails.py y deben estar
todos en rojo en esa primera ejecución. Un caso que pase sin implementación es
un caso mal escrito: no prueba nada.

Sin dependencias externas: librería estándar. Se ejecuta con
    python3 -m unittest -v test_guardrails
"""

import ast
import inspect
import json
import os
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent
FUENTE = RAIZ / "guardrails.py"
LEXICO = Path(os.environ.get("GUARDRAILS_LEXICO") or (RAIZ / "lexico_prohibido.txt"))

# Credenciales falsas, inventadas para los tests. No corresponden a nada real.
TOKEN_A = "sk-live-4kQ8ZzR2mN7pXw0aBcDeFgHiJkLmNoPq"
TOKEN_B = "ghp_9Xy2Wv4Ut6Sr8Qp0OnMlKjIhGfEdCbA1zZ23"
TOKEN_I = "sk-proj-Ab12Cd34Ef56Gh78Ij90Kl12Mn34Op56"

# Los seis prefijos que HOME_PATH cubre desde su primer test.
PREFIJOS_CUBIERTOS = [
    "/home/alice/proyecto/notas.txt",
    "/mnt/volumen1/datos.db",
    "/srv/www/app.conf",
    "/opt/herramientas/bin/arranque",
    "/var/log/aplicacion.log",
    "/media/usb0/copia.tar",
]

# Forma de un identificador de regla ajeno (letra + número, p. ej. "D31").
FORMA_ID_REGLA = re.compile(r"\b[A-Z]\d{1,3}\b")

# Rutas absolutas que jamás deben viajar en un mensaje mostrado al usuario.
RUTA_EN_MENSAJE = re.compile(r"/(?:home|mnt|srv|opt|var|media|Users)/")

IMPORTS_PERMITIDOS = {"re", "json", "hashlib", "pathlib", "typing", "dataclasses"}

# Vocabulario de exención. Ni el módulo ni su configuración pueden usarlo.
FORMA_EXENCION = re.compile(
    r"(?i)(exent|exempt|allow_?list|white_?list|lista_blanca|bypass|"
    r"trusted_?dir|safe_?dir|dir_?seguro|omitir|saltar)"
)


def cargar(caso):
    """Importa guardrails o marca el caso en rojo si todavía no existe."""
    if not FUENTE.exists():
        caso.fail("guardrails.py no existe todavía: rojo esperado de la tanda A")
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    import guardrails  # noqa: PLC0415

    return guardrails


def fuente(caso):
    """Devuelve el código de guardrails.py o marca el caso en rojo."""
    if not FUENTE.exists():
        caso.fail("guardrails.py no existe todavía: rojo esperado de la tanda A")
    return FUENTE.read_text(encoding="utf-8")


def lexico(caso):
    """Lee el léxico vigilado. Su ausencia es rojo, nunca un aprobado."""
    if not LEXICO.exists():
        caso.fail(
            "falta el fichero de léxico vigilado: sin lista no se puede afirmar "
            "que no hay fugas (fail-closed)"
        )
    terminos = []
    for linea in LEXICO.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            terminos.append(linea.lower())
    if not terminos:
        caso.fail("el fichero de léxico vigilado está vacío")
    return terminos


def cuenta(hallazgos):
    """[{policy, count}] -> {policy: count}."""
    return {h["policy"]: h["count"] for h in hallazgos}


class A_RutaYTokenEnLaMismaLinea(unittest.TestCase):
    """A · una ruta local en la línea no puede eclipsar al token."""

    def test_ruta_local_y_token_en_la_misma_linea(self):
        g = cargar(self)
        linea = f'curl -H "Authorization: Bearer {TOKEN_A}" --netrc-file /home/alice/proyecto/.netrc'
        redactado, hallazgos = g.redactar_salida(linea)
        c = cuenta(hallazgos)

        self.assertGreaterEqual(c.get("API_KEY", 0), 1, "el token debía bloquear por API_KEY")
        self.assertNotIn(TOKEN_A, redactado, "el token sobrevivió a la redacción")
        self.assertGreaterEqual(
            c.get("HOME_PATH", 0), 1, "la ruta debía detectarse además del token"
        )
        self.assertNotIn("/home/alice", redactado)


class B_FirmaSinParametroDeRuta(unittest.TestCase):
    """B · redactar_salida(texto) y nada más."""

    def test_la_firma_es_exactamente_texto(self):
        g = cargar(self)
        parametros = list(inspect.signature(g.redactar_salida).parameters.values())

        self.assertEqual([p.name for p in parametros], ["texto"])
        p = parametros[0]
        self.assertIn(
            p.kind,
            (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD),
        )
        self.assertIs(p.default, inspect.Parameter.empty, "el único parámetro no lleva default")
        self.assertNotIn(
            inspect.Parameter.VAR_KEYWORD,
            [q.kind for q in parametros],
            "**kwargs abriría la puerta a un parámetro de ruta",
        )
        self.assertNotIn(inspect.Parameter.VAR_POSITIONAL, [q.kind for q in parametros])
        self.assertFalse(
            re.search(r"(?i)(ruta|path|dir|fich|file|base)", p.name),
            "el parámetro no puede nombrar una ruta",
        )


class C_SinExencionPorDirectorio(unittest.TestCase):
    """C · ningún directorio compra una excepción."""

    def test_el_modulo_no_expone_vocabulario_de_exencion(self):
        g = cargar(self)
        publicos = [n for n in dir(g) if not n.startswith("__")]
        for nombre in publicos:
            self.assertFalse(
                FORMA_EXENCION.search(nombre), f"el módulo expone una exención: {nombre}"
            )

    def test_la_configuracion_no_admite_exenciones(self):
        g = cargar(self)
        datos = json.loads(Path(g.POLICIES_PATH).read_text(encoding="utf-8"))
        pendientes = [("", datos)]
        while pendientes:
            _, nodo = pendientes.pop()
            if isinstance(nodo, dict):
                for clave, valor in nodo.items():
                    self.assertFalse(
                        FORMA_EXENCION.search(str(clave)),
                        f"policies.json admite una exención: {clave}",
                    )
                    pendientes.append((clave, valor))

    def test_el_mismo_secreto_se_redacta_viva_donde_viva(self):
        g = cargar(self)
        resultados = []
        for directorio in ("/home/alice/publico", "/opt/compartido", "/srv/interno"):
            redactado, hallazgos = g.redactar_salida(f"{directorio}/x.env: {TOKEN_A}")
            self.assertNotIn(TOKEN_A, redactado)
            resultados.append(cuenta(hallazgos).get("API_KEY", 0))
        self.assertEqual(resultados, [1, 1, 1], "la cuenta cambió según el directorio")


class D_TodosLosHallazgosDeUnaLinea(unittest.TestCase):
    """D · sin break: una línea puede contener varios y se cuentan todos."""

    def test_multiples_hallazgos_en_una_sola_linea(self):
        g = cargar(self)
        linea = f"{TOKEN_A} y {TOKEN_B} contra 10.0.0.5 desde /srv/datos/entrada"
        redactado, hallazgos = g.redactar_salida(linea)
        c = cuenta(hallazgos)

        self.assertEqual(c.get("API_KEY", 0), 2, "el segundo token se perdió")
        self.assertEqual(c.get("PRIVATE_IP", 0), 1)
        self.assertEqual(c.get("HOME_PATH", 0), 1)
        for secreto in (TOKEN_A, TOKEN_B, "10.0.0.5", "/srv/datos/entrada"):
            self.assertNotIn(secreto, redactado)

    def test_la_forma_del_hallazgo_es_policy_y_count(self):
        g = cargar(self)
        _, hallazgos = g.redactar_salida(f"{TOKEN_A} {TOKEN_B}")
        self.assertIsInstance(hallazgos, list)
        for h in hallazgos:
            self.assertEqual(set(h.keys()), {"policy", "count"})
            self.assertIsInstance(h["policy"], str)
            self.assertIsInstance(h["count"], int)
            self.assertGreater(h["count"], 0, "un hallazgo con cuenta cero no es un hallazgo")


class E_LaFirmaRechazaLoQueNoEsTexto(unittest.TestCase):
    """E · TypeError ante kwargs inesperados o un objeto con atributo de ruta."""

    def test_kwargs_inesperados(self):
        g = cargar(self)
        for kwargs in ({"ruta": "/home/alice"}, {"path": "/home/alice"}, {"base_dir": "/srv"}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(TypeError):
                    g.redactar_salida("texto cualquiera", **kwargs)

    def test_objeto_con_atributo_de_ruta(self):
        g = cargar(self)

        class ConRuta:
            ruta = "/home/alice/proyecto"

            def __str__(self):
                return "texto cualquiera"

        class ConPath:
            path = "/home/alice/proyecto"

            def __str__(self):
                return "texto cualquiera"

        for objeto in (ConRuta(), ConPath(), Path("/home/alice"), b"bytes", 42, None):
            with self.subTest(objeto=type(objeto).__name__):
                with self.assertRaises(TypeError):
                    g.redactar_salida(objeto)


class F_SinDependenciasNiRutasAjenas(unittest.TestCase):
    """F · el módulo no importa ni nombra nada del proyecto que lo vio nacer."""

    def test_solo_importa_libreria_estandar_permitida(self):
        arbol = ast.parse(fuente(self))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    raiz = alias.name.split(".")[0]
                    self.assertIn(raiz, IMPORTS_PERMITIDOS, f"import no permitido: {alias.name}")
            elif isinstance(nodo, ast.ImportFrom):
                self.assertEqual(nodo.level, 0, "sin imports relativos: el módulo es autónomo")
                raiz = (nodo.module or "").split(".")[0]
                self.assertIn(raiz, IMPORTS_PERMITIDOS, f"import no permitido: {nodo.module}")

    def test_el_codigo_no_menciona_el_lexico_vigilado(self):
        codigo = fuente(self).lower()
        for termino in lexico(self):
            self.assertNotIn(termino, codigo, f"el código menciona un término ajeno: {termino}")

    def test_el_codigo_no_lleva_identificadores_de_regla_ajenos(self):
        arbol = ast.parse(fuente(self))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                self.assertIsNone(
                    FORMA_ID_REGLA.search(nodo.value),
                    f"cadena con forma de ID de regla ajeno: {nodo.value!r}",
                )


class G_InterfazVisibleLimpia(unittest.TestCase):
    """G · nada de lo que el usuario ve nombra una regla ajena."""

    def cadenas_visibles(self, g):
        visibles = []
        visibles += list(g.CORE_POLICIES) + list(g.CUSTOM_POLICIES)
        visibles += [str(v) for v in g.MASCARAS.values()]
        visibles += list(json.loads(Path(g.POLICIES_PATH).read_text(encoding="utf-8")).keys())
        visibles.append(g.__doc__ or "")
        visibles.append(g.redactar_salida.__doc__ or "")
        visibles.append(g.preparar_envio.__doc__ or "")

        respuesta = g.preparar_envio(f"{TOKEN_A} en 192.168.1.9 y /var/log/app.log")
        visibles.append(json.dumps(respuesta, ensure_ascii=False, sort_keys=True))

        with mock.patch.object(g, "POLICIES_PATH", RAIZ / "no_existe_policies.json"):
            with self.assertRaises(g.EnvioBloqueado) as capturado:
                g.preparar_envio("hola")
            visibles.append(str(capturado.exception))
        with mock.patch.object(g, "redactar_salida", side_effect=RuntimeError("fallo interno")):
            with self.assertRaises(g.EnvioBloqueado) as capturado:
                g.preparar_envio("hola")
            visibles.append(str(capturado.exception))
        return visibles

    def test_ninguna_cadena_visible_nombra_el_lexico_vigilado(self):
        g = cargar(self)
        terminos = lexico(self)
        for cadena in self.cadenas_visibles(g):
            for termino in terminos:
                self.assertNotIn(termino, cadena.lower(), f"fuga de léxico en: {cadena!r}")

    def test_ninguna_cadena_visible_lleva_id_de_regla_ni_ruta(self):
        g = cargar(self)
        for cadena in self.cadenas_visibles(g):
            self.assertIsNone(FORMA_ID_REGLA.search(cadena), f"ID de regla ajeno en: {cadena!r}")
        for cadena in self.cadenas_visibles(g):
            if cadena.startswith("{") or cadena.startswith("["):
                continue  # la respuesta serializada se examina en el caso I
            self.assertIsNone(
                RUTA_EN_MENSAJE.search(cadena), f"ruta absoluta en un mensaje: {cadena!r}"
            )


class H_HomePathContraLosSeisPrefijos(unittest.TestCase):
    """H · un caso por prefijo, más los controles negativos declarados."""

    def test_un_caso_por_prefijo_cubierto(self):
        g = cargar(self)
        for ruta in PREFIJOS_CUBIERTOS:
            with self.subTest(ruta=ruta):
                redactado, hallazgos = g.redactar_salida(f"se abrió {ruta} sin error")
                self.assertEqual(
                    cuenta(hallazgos).get("HOME_PATH", 0), 1, f"prefijo sin cubrir: {ruta}"
                )
                self.assertNotIn(ruta, redactado)

    def test_tmp_queda_fuera_por_decision_firmada(self):
        g = cargar(self)
        texto = "se abrió /tmp/trabajo/borrador.txt sin error"
        redactado, hallazgos = g.redactar_salida(texto)
        self.assertEqual(cuenta(hallazgos).get("HOME_PATH", 0), 0)
        self.assertEqual(redactado, texto, "/tmp no se redacta: decisión firmada")

    def test_users_y_windows_no_estan_cubiertos_todavia(self):
        # Hueco declarado, no olvidado: entran cuando tengan su test explícito,
        # y C:\ con su propio caso de escapado. Este test cae el día que se cubran.
        g = cargar(self)
        for ruta in ("/Users/alice/proyecto/notas.txt", r"C:\Users\alice\proyecto\notas.txt"):
            with self.subTest(ruta=ruta):
                _, hallazgos = g.redactar_salida(f"se abrió {ruta} sin error")
                self.assertEqual(cuenta(hallazgos).get("HOME_PATH", 0), 0)


class I_ElTokenNoViajaEnLaRespuesta(unittest.TestCase):
    """I · la cadena del token no aparece en ninguna parte de la respuesta."""

    def test_el_token_no_esta_en_la_respuesta_serializada(self):
        g = cargar(self)
        prompt = (
            f"revisa esto por favor: OPENAI_API_KEY={TOKEN_I}\n"
            f"lo lancé desde /home/alice/proyecto contra 10.1.2.3"
        )
        respuesta = g.preparar_envio(prompt)
        serializada = json.dumps(respuesta, ensure_ascii=False, sort_keys=True)

        self.assertNotIn(TOKEN_I, serializada, "el token viaja en la respuesta")
        self.assertNotIn(TOKEN_I[-16:], serializada, "viaja una cola del token")
        self.assertNotIn("/home/alice/proyecto", serializada)
        self.assertNotIn("10.1.2.3", serializada)

        for h in respuesta["hallazgos"]:
            self.assertEqual(set(h.keys()), {"policy", "count"})
        self.assertGreaterEqual(cuenta(respuesta["hallazgos"]).get("API_KEY", 0), 1)


class J_FailClosedDeError(unittest.TestCase):
    """J · si el redactor falla, el envío no sale."""

    def test_fallo_en_la_funcion_publica_bloquea(self):
        g = cargar(self)
        with mock.patch.object(g, "redactar_salida", side_effect=RuntimeError("fallo inyectado")):
            with self.assertRaises(g.EnvioBloqueado):
                g.preparar_envio(f"texto con {TOKEN_A}")

    def test_fallo_en_el_motor_interno_bloquea(self):
        g = cargar(self)
        with mock.patch.object(g, "_aplicar", side_effect=RuntimeError("fallo inyectado")):
            with self.assertRaises(g.EnvioBloqueado):
                g.preparar_envio(f"texto con {TOKEN_A}")

    def test_el_bloqueo_no_filtra_el_texto_original(self):
        g = cargar(self)
        with mock.patch.object(g, "_aplicar", side_effect=RuntimeError(TOKEN_A)):
            with self.assertRaises(g.EnvioBloqueado) as capturado:
                g.preparar_envio(f"texto con {TOKEN_A}")
        self.assertNotIn(TOKEN_A, str(capturado.exception))


class K_FailClosedDeConfiguracion(unittest.TestCase):
    """K · sin configuración válida no hay envío."""

    def test_policies_ausente_bloquea(self):
        g = cargar(self)
        with mock.patch.object(g, "POLICIES_PATH", RAIZ / "no_existe_policies.json"):
            with self.assertRaises(g.EnvioBloqueado):
                g.preparar_envio("hola")
            with self.assertRaises(g.PoliticasInvalidas):
                g.redactar_salida("hola")

    def test_policies_corrupto_bloquea(self):
        g = cargar(self)
        corruptos = [
            "{ esto no es json",
            "[]",
            '{"PRIVATE_IP": "sí"}',
            '{"POLITICA_QUE_NO_EXISTE": {"activa": true}}',
            '{"API_KEY": {"activa": false}}',
        ]
        for i, contenido in enumerate(corruptos):
            with self.subTest(caso=i):
                sucio = RAIZ / f".policies_corrupto_{i}.json"
                sucio.write_text(contenido, encoding="utf-8")
                try:
                    with mock.patch.object(g, "POLICIES_PATH", sucio):
                        with self.assertRaises(g.EnvioBloqueado):
                            g.preparar_envio("hola")
                finally:
                    sucio.unlink()


class G2_FicherosDeInterfazLimpios(unittest.TestCase):
    """G · la interfaz también es superficie visible: se audita como tal."""

    def ficheros(self):
        directorio = RAIZ / "interface"
        if not directorio.is_dir():
            self.fail("no hay interfaz que auditar: rojo esperado antes de escribirla")
        encontrados = sorted(
            p for p in directorio.rglob("*") if p.suffix in {".html", ".css", ".js"}
        )
        if not encontrados:
            self.fail("la interfaz no tiene ningún fichero auditable")
        return encontrados

    def test_la_interfaz_no_menciona_el_lexico_vigilado(self):
        terminos = lexico(self)
        for fichero in self.ficheros():
            contenido = fichero.read_text(encoding="utf-8").lower()
            for termino in terminos:
                self.assertNotIn(
                    termino, contenido, f"fuga de léxico en {fichero.name}: {termino}"
                )

    def test_la_interfaz_no_lleva_ids_de_regla_ni_rutas_locales(self):
        for fichero in self.ficheros():
            contenido = fichero.read_text(encoding="utf-8")
            self.assertIsNone(
                FORMA_ID_REGLA.search(contenido), f"ID de regla ajeno en {fichero.name}"
            )
            self.assertIsNone(
                RUTA_EN_MENSAJE.search(contenido), f"ruta local en {fichero.name}"
            )

    def test_la_interfaz_solo_nombra_politicas_que_existen(self):
        g = cargar(self)
        conocidas = set(g.CORE_POLICIES) | set(g.CUSTOM_POLICIES)
        for fichero in self.ficheros():
            contenido = fichero.read_text(encoding="utf-8")
            for nombrada in re.findall(r"\b[A-Z][A-Z_]{3,}\b", contenido):
                if nombrada.startswith("REDACTED") or nombrada in {"DOCTYPE", "UTF"}:
                    continue
                self.assertIn(
                    nombrada, conocidas, f"la interfaz nombra algo que no es política: {nombrada}"
                )

    def test_la_interfaz_no_recalcula_el_contador(self):
        # El contador es el valor de retorno del endpoint. Si la interfaz
        # cuenta por su cuenta, puede discrepar de lo que de verdad se filtró.
        prohibido = re.compile(
            r"(?i)(\.match\(|\bregexp?\b|new RegExp|\.test\(|"
            r"\bcount\s*\+\+|\bcount\s*\+=|\.filter\([^)]*policy)"
        )
        for fichero in self.ficheros():
            if fichero.suffix not in {".js", ".html"}:
                continue
            contenido = fichero.read_text(encoding="utf-8")
            self.assertIsNone(
                prohibido.search(contenido),
                f"{fichero.name} parece recalcular el contador en el cliente",
            )


class BB_NombresDeClaveConPrefijo(unittest.TestCase):
    """TANDA B · hallazgo de la verificación manual, no de la tanda A.

    El nombre de una variable casi nunca es la palabra desnuda: es `db_password`
    o `OPENAI_API_KEY`. Un `\\b` delante de la palabra clave no ve ninguno de los
    dos, porque el guion bajo es carácter de palabra.
    """

    CON_PREFIJO = [
        ('db_password: "correcto-caballo-bateria"', "ASSIGNED_SECRET"),
        ("USER_PASSWORD=tapon-de-corcho-2024", "ASSIGNED_SECRET"),
        ("mi_client_secret = 7f3a9b2c4d6e8f0a", "ASSIGNED_SECRET"),
        ("OPENAI_API_KEY=Ab12Cd34Ef56Gh78Ij90", "API_KEY"),
        ("MY_AUTH_TOKEN=Zz9Yy8Xx7Ww6Vv5Uu4Tt3", "API_KEY"),
    ]

    SIN_SECRETO = [
        "notpassword: abcdefghij",
        "passwordless login habilitado en el equipo",
    ]

    def test_el_prefijo_no_esconde_el_secreto(self):
        g = cargar(self)
        for texto, politica in self.CON_PREFIJO:
            with self.subTest(texto=texto):
                redactado, hallazgos = g.redactar_salida(texto)
                self.assertGreaterEqual(
                    cuenta(hallazgos).get(politica, 0), 1, f"secreto no visto: {texto}"
                )
                valor = texto.split("=")[-1].split(":")[-1].strip().strip('"')
                self.assertNotIn(valor, redactado)

    def test_una_palabra_pegada_no_dispara(self):
        g = cargar(self)
        for texto in self.SIN_SECRETO:
            with self.subTest(texto=texto):
                redactado, hallazgos = g.redactar_salida(texto)
                self.assertEqual(hallazgos, [], f"falso positivo en: {texto}")
                self.assertEqual(redactado, texto)


class CC_CorpusDeFalsosNegativos(unittest.TestCase):
    """TANDA C · el corpus.

    El agujero del prefijo lo encontró una mirada humana, no la suite. Esto
    convierte esa mirada en algo que no depende de que alguien mire: muestras
    con la forma que tienen de verdad los ficheros de configuración, los logs y
    las trazas. Todo el contenido es inventado.
    """

    CORPUS = RAIZ / "corpus" / "muestras.json"

    def corpus(self):
        if not self.CORPUS.exists():
            self.fail("no hay corpus que ejecutar: rojo esperado antes de escribirlo")
        datos = json.loads(self.CORPUS.read_text(encoding="utf-8"))
        if not datos.get("casos"):
            self.fail("el corpus no tiene casos")
        return datos

    def test_cada_caso_detecta_lo_que_declara(self):
        g = cargar(self)
        for caso in self.corpus()["casos"]:
            with self.subTest(caso=caso["id"]):
                redactado, hallazgos = g.redactar_salida(caso["texto"])
                c = cuenta(hallazgos)
                for politica, minimo in caso["espera"].items():
                    self.assertGreaterEqual(
                        c.get(politica, 0),
                        minimo,
                        f"{caso['id']}: {politica} esperaba >={minimo}, salió {c.get(politica, 0)}",
                    )
                for fragmento in caso.get("no_sobrevive", []):
                    self.assertNotIn(
                        fragmento, redactado, f"{caso['id']}: sobrevivió un fragmento"
                    )
                for politica in caso.get("no_dispara", []):
                    self.assertEqual(
                        c.get(politica, 0), 0, f"{caso['id']}: {politica} no debía disparar"
                    )

    def test_los_limites_declarados_siguen_siendo_limites(self):
        # Estos casos deben salir intactos. El día que uno se cubra, este test
        # cae y obliga a mover la línea a mano, que es lo que se quiere: una
        # cobertura que crece sin que nadie se entere no es cobertura, es azar.
        g = cargar(self)
        for caso in self.corpus()["limites_declarados"]:
            with self.subTest(caso=caso["id"]):
                redactado, hallazgos = g.redactar_salida(caso["texto"])
                self.assertEqual(
                    hallazgos, [], f"{caso['id']}: disparó, y estaba declarado como límite"
                )
                self.assertEqual(redactado, caso["texto"])

    def test_el_corpus_no_lleva_lexico_vigilado(self):
        terminos = lexico(self)
        contenido = self.CORPUS.read_text(encoding="utf-8").lower()
        for termino in terminos:
            self.assertNotIn(termino, contenido, f"fuga de léxico en el corpus: {termino}")

    def test_el_corpus_no_lleva_credenciales_de_esta_maquina(self):
        # Un corpus de muestras es el sitio más fácil del mundo para pegar sin
        # querer algo real. Se comprueba que no coincida con lo que hay en disco.
        contenido = self.CORPUS.read_text(encoding="utf-8")
        for sospechoso in (str(Path.home()), Path.home().name):
            if len(sospechoso) > 3:
                self.assertNotIn(sospechoso, contenido, "el corpus nombra esta máquina")


if __name__ == "__main__":
    unittest.main(verbosity=2)
