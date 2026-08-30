# PreceptorOS · instalador de escritorio para Windows.
#
# ESTADO DE PRUEBAS: NO PROBADO.
# No hay ninguna maquina Windows en el rack donde se escribio esto. El guion
# esta revisado linea a linea, pero nadie lo ha ejecutado nunca. Si lo corres y
# falla, ese fallo es informacion util: reportalo con el mensaje exacto.
#
# LO QUE NO HACE: no instala nada como administrador. Comprueba que falta, te
# da el comando exacto, y hace por su cuenta solo lo que no necesita permisos.
# Un instalador bajado de internet que pide administrador y luego hace lo que
# quiera es justo lo contrario de lo que este producto intenta ser.

$ErrorActionPreference = 'Stop'
$Repo    = if ($env:PRECEPTOROS_REPO)    { $env:PRECEPTOROS_REPO }    else { 'https://github.com/piskyRpapalo/PreceptorOS' }
$Destino = if ($env:PRECEPTOROS_DESTINO) { $env:PRECEPTOROS_DESTINO } else { "$HOME\preceptoros" }

function V($m)  { Write-Host " .. $m" -ForegroundColor Magenta }
function OK($m) { Write-Host " OK $m" -ForegroundColor Green }
function NO($m) { Write-Host " XX $m" -ForegroundColor Red }
function ND($m) { Write-Host " -- $m" -ForegroundColor Yellow }

Write-Host ""
Write-Host "PreceptorOS - instalacion en Windows" -ForegroundColor Magenta
ND "Este guion NO esta probado: no hay ninguna maquina Windows en el rack."
Write-Host ""

$faltan = 0
foreach ($b in @('python','git')) {
  if (Get-Command $b -ErrorAction SilentlyContinue) {
    OK "$b - $(& $b --version 2>&1 | Select-Object -First 1)"
  } else {
    NO "falta $b  ->  winget install $(if ($b -eq 'python') {'Python.Python.3.12'} else {'Git.Git'})"
    $faltan++
  }
}

if (Get-Command ollama -ErrorAction SilentlyContinue) {
  OK "ollama - presente"
} else {
  ND "sin ollama - PreceptorOS funcionara igual: recuerda, indexa y sanea"
  ND "  para que ademas converse:  winget install Ollama.Ollama"
  ND "  ese comando NO se ejecuta aqui - lo lanzas tu si quieres"
}

if ($faltan -gt 0) {
  Write-Host ""
  NO "faltan $faltan pieza(s). Instalalas con los comandos de arriba y vuelve."
  NO "No las instalo yo: este guion no pide administrador."
  exit 1
}

Write-Host ""
if (Test-Path "$Destino\.git") {
  V "ya hay un PreceptorOS en $Destino - actualizando"
  git -C $Destino pull --ff-only
} else {
  V "clonando en $Destino"
  git clone --depth 1 $Repo $Destino
}
OK "arbol listo - $Destino"

Write-Host ""
OK "listo."
Write-Host ""
V "arrancalo:   cd $Destino ; python bin\preceptoros-pwa"
V "y abrelo en: http://127.0.0.1:8740/"
Write-Host ""
V "Dentro te espera el Instalador: te presenta a los companeros y te ayuda a"
V "elegir el que encaja con lo que quieres hacer."
Write-Host ""
