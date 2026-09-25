"""The class table is pinned: if it moves, the doctor and the Torre de Puertos move with it."""
import ipaddress
import unittest

from clases import _TAILNET_V4, _TAILNET_V6, clase_de

# Private and overlay addresses are BUILT from their ranges, never written: no literal of
# a real-looking network sits in a public file.
_LAN = [str(ipaddress.IPv4Network((n, 16))[5]) for n in (0xC0A80000, 0x0A000000, 0xAC110000)]

TABLA = [
    ("127.0.0.1", "LOOPBACK"), ("127.0.0.53%lo", "LOOPBACK"), ("[::1]", "LOOPBACK"),
    ("0.0.0.0", "ANY"), ("[::]", "ANY"), ("*", "ANY"),
    *[(a, "LAN") for a in _LAN], ("[fe80::1]%eno1", "LAN"),
    (str(_TAILNET_V4[1]), "TAILNET"), (str(_TAILNET_V4[-2]), "TAILNET"),
    ("[" + str(_TAILNET_V6[1]) + "]", "TAILNET"),
    (str(_TAILNET_V4.broadcast_address + 2), "PUBLIC"),   # just past the /10: not the overlay
    ("8.8.8.8", "PUBLIC"), ("not-an-ip", "OTRA"),
]


class Clases(unittest.TestCase):
    def test_tabla(self):
        for direccion, clase in TABLA:
            with self.subTest(direccion=direccion):
                self.assertEqual(clase_de(direccion), clase)


if __name__ == "__main__":
    unittest.main()
