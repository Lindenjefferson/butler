#!/bin/sh
# Roda um script do plugin com o Python 3: o primeiro de python (o nome comum no Windows) e python3 (muitas vezes o
# único no Linux) que for Python 3, para pular um Python 2 ou o atalho da loja do Windows. O hooks.json e os comandos
# das skills usam este arquivo. Mesma lógica do python.sh do Foreman.
# Uso: sh python.sh <script> [args...]. Sem Python 3, avisa no stderr e sai com 1.
for py in python python3; do
  if "$py" -c 'import sys; sys.exit(sys.version_info[0] < 3)' </dev/null >/dev/null 2>&1; then
    exec "$py" "$@"
  fi
done
echo "butler: nenhum Python 3 no PATH (tentei python e python3); instale o Python 3." >&2
exit 1
