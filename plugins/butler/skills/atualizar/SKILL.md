---
name: atualizar
description: Atualiza o plugin Butler para a versão mais nova do marketplace e aplica as notas de atualização de cada versão pulada. Use quando o usuário pedir "atualiza o Butler", "atualizar o plugin do vault", ou quando quiser saber se há versão nova.
---

# Atualizar o Butler

1. **Ponto de parada.** `sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/gerente/butler.py" situacao`. Com uma trava ativa (um pedido em andamento no vault), pare: diga qual e peça para terminar o pedido antes.
2. **Versões.** A que está rodando está em `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. O escopo e o marketplace vêm de `claude plugin list --json` (a entrada `butler@<marketplace>`).
3. **Buscar.** `claude plugin marketplace update <marketplace>`, depois `claude plugin update butler@<marketplace> --scope <escopo>`. Se nada mudou, diga que já está na mais nova e pare.
4. **Notas.** Leia `${CLAUDE_PLUGIN_ROOT}/UPGRADING.md` da versão nova (depois do update, o caminho do plugin muda: ache-o pelo `claude plugin list --json`): o parágrafo **Ao atualizar** de cada versão depois da antiga até a nova, da mais antiga para a mais nova.
5. **Aplicar.** Faça o que cada **Ao atualizar** pede. Quando ele pedir uma nova rodada do `butler:preparar`, diga isso e ofereça rodar. Mudança em nota do vault segue o `butler:gerente`.
6. **Recarregar.** Peça `/reload-plugins` (ou uma sessão nova) para a versão nova valer.
7. Resuma: de qual versão para qual, o que cada nota pediu e o que foi feito.
