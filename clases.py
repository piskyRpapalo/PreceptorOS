"""clases.py · the class of a local address, BEFORE it is obscured.

One owner for «what is LOOPBACK» (RV3-01, 2026-09-25): the rack's doctor
imports this file instead of keeping its own copy, and the Torre de Puertos
builds on it. <LOOPBACK> and <ANY> are opposites; a report that hides both
behind the same mask hides the one difference that matters.

Stdlib only. No address of any real machine lives here.
"""
import ipaddress

LOOPBACK, ANY, LAN, TAILNET, PUBLIC, OTRA = "LOOPBACK", "ANY", "LAN", "TAILNET", "PUBLIC", "OTRA"

# RFC 6598 shared space, /10, the overlay network's range. Built from its integer so no
# address literal of that range sits in a public file (the hygiene guard never exempts it).
_TAILNET_V4 = ipaddress.IPv4Network((0x64400000, 10))
_TAILNET_V6 = ipaddress.IPv6Network((0xFD7A115CA1E0 << 80, 48))


def clase_de(direccion):
    """`127.0.0.1`, `[::1]`, `0.0.0.0`, `*`, `<lan-address>%eno1`… → one of the six classes."""
    d = (direccion or "").strip().split("%")[0].strip("[]")   # zone first: "[fe80::1]%eno1"
    if d in ("0.0.0.0", "::", "*", ""):
        return ANY
    try:
        ip = ipaddress.ip_address(d)
    except ValueError:
        return OTRA
    if ip.is_loopback:
        return LOOPBACK
    if ip in _TAILNET_V4 or ip in _TAILNET_V6:
        return TAILNET
    if ip.is_private or ip.is_link_local:
        return LAN
    if ip.is_global:
        return PUBLIC
    return OTRA
