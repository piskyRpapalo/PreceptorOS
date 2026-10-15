"""Molde binario del preceptor: 150 bytes exactos."""
import copy
import unittest

from estado_compacto import ZONAS, codificar, decodificar


def vector_base():
    return {
        "zona": "conversacion", "frescura": "LIVE", "tau": 1_000_000,
        "origen": "conversacion", "tick": 77, "id_sesion": bytes(range(16)),
        "hue": 210, "saturacion": 40, "luminosidad": 65,
        "carga": 250_000, "confianza": 900_000, "escudo": 700_000,
        "edad_tics": 0, "ttl_tics": 10_000, "nonce_secuencial": 42,
        "atestacion_termica_publica": bytes(range(16, 32)),
        "causa_no_data": None,
        "entropia_temporal": 0x0102030405060708090A0B0C0D0E0F10111213141516,
        "propuesta_pendiente_firma": True, "error": False,
    }


class MoldeST(unittest.TestCase):
    def test_serializa_roundtrip_a_150_bytes_con_offsets_firmes(self):
        estado = vector_base()
        datos = codificar(estado)
        self.assertEqual(len(datos), 150)
        self.assertEqual(datos[0:4], b"PST1")
        self.assertEqual(datos[4], 1)
        self.assertEqual(datos[0x80:0x96], estado["entropia_temporal"].to_bytes(22, "big"))
        self.assertEqual(decodificar(datos), estado)

    def test_serializacion_es_determinista_y_preserva_el_rango_0x80_0x95(self):
        estado = vector_base()
        datos = codificar(estado)
        self.assertEqual(codificar(copy.deepcopy(estado)), datos)
        self.assertEqual(datos[128:150], bytes.fromhex("0102030405060708090a0b0c0d0e0f10111213141516"))

    def test_rechaza_paquetes_de_149_y_151_bytes(self):
        datos = codificar(vector_base())
        for paquete in (datos[:-1], datos + b"\0"):
            with self.subTest(longitud=len(paquete)), self.assertRaises(ValueError):
                decodificar(paquete)

    def test_rechaza_magic_version_flags_y_reservados_alterados(self):
        datos = bytearray(codificar(vector_base()))
        for posicion, valor in ((0, ord("X")), (4, 2), (7, 0x10), (97, 1)):
            paquete = bytearray(datos)
            paquete[posicion] = valor
            with self.subTest(posicion=posicion), self.assertRaises(ValueError):
                decodificar(bytes(paquete))

    def test_zonas_y_codigos_de_frescura_son_vocabularios_cerrados(self):
        self.assertEqual(len(ZONAS), 9)
        for campo, valor in (("zona", "web"), ("frescura", "EXPIRED")):
            estado = vector_base()
            estado[campo] = valor
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                codificar(estado)
        datos = bytearray(codificar(vector_base()))
        datos[5] = 0
        with self.assertRaises(ValueError):
            decodificar(bytes(datos))

    def test_no_data_por_caducidad_conserva_delta_y_no_se_disfraza_de_stale(self):
        estado = vector_base()
        estado.update(frescura="NO_DATA", edad_tics=11, ttl_tics=10,
                      causa_no_data="expired", hue=None, saturacion=None,
                      luminosidad=None, carga=None, confianza=None, escudo=None,
                      propuesta_pendiente_firma=False)
        datos = codificar(estado)
        self.assertEqual(datos[6], 0)
        self.assertEqual(datos[7] & 0b0101, 0b0001)
        self.assertEqual(decodificar(datos), estado)
        estado["frescura"] = "STALE"
        with self.assertRaises(ValueError):
            codificar(estado)

    def test_stale_exige_edad_positiva_menor_que_ttl(self):
        estado = vector_base()
        estado.update(frescura="STALE", edad_tics=2, propuesta_pendiente_firma=False)
        datos = codificar(estado)
        self.assertEqual(datos[6], 2)
        self.assertEqual(datos[7] & 0b0101, 0b0100)
        estado["edad_tics"] = estado["ttl_tics"]
        estado["frescura"] = "STALE"
        with self.assertRaises(ValueError):
            codificar(estado)

    def test_entropia_debe_caber_en_176_bits_y_no_se_trunca(self):
        estado = vector_base()
        estado["entropia_temporal"] = (1 << 176) - 1
        self.assertEqual(codificar(estado)[128:150], b"\xff" * 22)
        estado["entropia_temporal"] += 1
        with self.assertRaises(ValueError):
            codificar(estado)

    def test_bitpacking_estricto_rechaza_booleanos_firma_y_campos_desconocidos(self):
        for campo, valor in (("tau", True), ("tick", True),
                             ("propuesta_pendiente_firma", 1),
                             ("firma_privada", b"x")):
            estado = vector_base()
            estado[campo] = valor
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                codificar(estado)

    def test_codigos_y_orden_de_zona_tienen_endian_y_rango_estables(self):
        datos = codificar(vector_base())
        self.assertEqual(datos[8:12], (1_000_000).to_bytes(4, "big"))
        self.assertEqual(datos[12:16], (2).to_bytes(4, "big"))
        self.assertEqual(datos[16:24], (77).to_bytes(8, "big"))
        self.assertEqual(datos[72:80], (42).to_bytes(8, "big"))
        estado = vector_base()
        estado["tau"] = 1_000_001
        with self.assertRaises(ValueError):
            codificar(estado)


if __name__ == "__main__":
    unittest.main()
