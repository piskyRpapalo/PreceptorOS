#!/usr/bin/env bash
# PreceptorOS · instalador de escritorio. Linux y macOS.
#
# LO QUE ESTE GUION NO HACE, Y ES LO PRIMERO QUE HAY QUE SABER
# ------------------------------------------------------------
# NO instala nada con sudo. Ni Python, ni Ollama, ni paquetes del sistema.
#
# No es pereza: es la misma regla que ya lleva escrita `bin/instalar-pc` --
# «pedir una contrasena a mitad de un guion es como se cuelan las sorpresas».
# Un instalador descargado de internet que pide root y luego hace lo que quiera
# es exactamente la forma de la que este producto intenta ser lo contrario.
#
# Lo que SI hace: comprueba que esta y que falta, te da el comando EXACTO de tu
# sistema para lo que falte, y hace por su cuenta todo lo que no necesita root
# -- clonar, preparar la memoria y crear la puerta de entrada.
#
# ESTADO DE PRUEBAS (honesto, y por eso esta aqui arriba):
#   Linux  · PROBADO en el nodo de desarrollo.
#   macOS  · NO PROBADO. No hay ninguna maquina macOS en este rack. El ramal
#            de Homebrew esta escrito y revisado, pero nadie lo ha corrido.
#            Si lo pruebas y falla, ese fallo es informacion: repórtalo.
set -uo pipefail

REPO="${PRECEPTOROS_REPO:-https://github.com/piskyRpapalo/PreceptorOS}"
DESTINO="${PRECEPTOROS_DESTINO:-$HOME/preceptoros}"

v() { printf '\033[38;5;141m··\033[0m %s\n' "$1"; }
ok() { printf '\033[38;5;71m ✓\033[0m %s\n' "$1"; }
no() { printf '\033[38;5;167m ✗\033[0m %s\n' "$1"; }
nd() { printf '\033[38;5;179m ⬜\033[0m %s\n' "$1"; }

case "$(uname -s)" in
  Linux)  SO=linux ;;
  Darwin) SO=macos ;;
  *) no "sistema no soportado: $(uname -s). Este guion cubre Linux y macOS."
     exit 1 ;;
esac

printf '\n\033[38;5;141mPreceptorOS\033[0m · instalación en %s\n\n' "$SO"
[ "$SO" = macos ] && nd "macOS NO está probado en el rack de desarrollo. Sigues tú siendo el primero."

# --- 1 · lo que hace falta, y quien lo instala ------------------------------
faltan=0
comando_para() {   # comando_para <binario> -> imprime como instalarlo AQUI
  case "$SO" in
    macos) command -v brew >/dev/null 2>&1 \
             && echo "brew install $1" \
             || echo "instala Homebrew primero (https://brew.sh) y luego: brew install $1" ;;
    linux) if   command -v apt    >/dev/null 2>&1; then echo "sudo apt install $1"
           elif command -v dnf    >/dev/null 2>&1; then echo "sudo dnf install $1"
           elif command -v pacman >/dev/null 2>&1; then echo "sudo pacman -S $1"
           elif command -v zypper >/dev/null 2>&1; then echo "sudo zypper install $1"
           else echo "instala '$1' con el gestor de paquetes de tu distribución"
           fi ;;
  esac
}

for b in python3 git; do
  if command -v "$b" >/dev/null 2>&1; then
    ok "$b · $("$b" --version 2>&1 | head -1)"
  else
    no "falta $b  →  $(comando_para "$b")"
    faltan=$((faltan + 1))
  fi
done

# Ollama es opcional: sin él PreceptorOS recuerda y sanea, pero no conversa.
# Se dice cuál es la diferencia en vez de tratarlo como un error.
if command -v ollama >/dev/null 2>&1; then
  ok "ollama · presente"
else
  nd "sin ollama · PreceptorOS funcionará igual: recuerda, indexa y sanea"
  nd "  para que además converse:  curl -fsSL https://ollama.com/install.sh | sh"
  nd "  ese comando NO se ejecuta aquí — lo lanzas tú si quieres, tras leerlo"
fi

if [ "$faltan" -gt 0 ]; then
  echo
  no "faltan $faltan pieza(s). Instálalas con los comandos de arriba y vuelve."
  no "No las instalo yo: este guion no pide root, y no va a empezar ahora."
  exit 1
fi

# --- 2 · el árbol ----------------------------------------------------------
echo
if [ -d "$DESTINO/.git" ]; then
  v "ya hay un PreceptorOS en $DESTINO · actualizando"
  git -C "$DESTINO" pull --ff-only || nd "no se pudo actualizar; sigo con lo que hay"
else
  v "clonando en $DESTINO"
  git clone --depth 1 "$REPO" "$DESTINO" || { no "el clon falló"; exit 1; }
fi
ok "árbol listo · $DESTINO"

# --- 3 · la memoria y la puerta --------------------------------------------
echo
if [ -x "$DESTINO/bin/instalar-pc" ]; then
  v "creando la puerta de entrada"
  "$DESTINO/bin/instalar-pc" || nd "la puerta no se pudo crear; se arranca a mano igual"
else
  nd "no está bin/instalar-pc en este árbol"
fi

echo
ok "listo."
echo
v "arráncalo:      cd $DESTINO && bin/preceptoros-servicio arranca"
v "y ábrelo en:    http://127.0.0.1:8740/"
echo
v "Dentro te espera el Instalador: te presenta a los compañeros y te ayuda a"
v "elegir el que encaja con lo que quieres hacer."
echo
