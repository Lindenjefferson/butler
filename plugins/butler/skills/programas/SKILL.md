---
name: programas
description: Atualiza a nota do inventário de programas da máquina em que a sessão está, e o JSON do winget ao lado dela, num vault do Butler no Windows. Use quando o usuário pedir "atualiza os programas", "atualiza o inventário de programas", "o que mudou nos programas instalados", depois de instalar ou desinstalar programas, ou quando o Wingman chamar `/butler:programas`.
---

# Inventário de programas

Um Lote do `butler:gerente` (preâmbulo, paradas, pontos e resumo vêm de lá; `B` é o comando de lá). Só existe no Windows, porque depende do `winget`.

## Antes

1. A regra das notas de programas está no `CLAUDE.md` do vault (formato da linha, nomes das fontes, seções na ordem, o que fica de fora, o JSON, o que fazer com programa desinstalado). Leia inteira: esta skill não repete nenhuma regra dela.
2. **Só roda na máquina inventariada:** a nota certa é a do computador desta sessão (o nome da máquina está na nota, no título ou no `source`). Se não houver nota para esta máquina, criar uma é pedido à parte: pergunte.
3. A nota é protegida e de formato rígido.
4. Preâmbulo do gerente. Numa máquina sem histórico (um notebook, por exemplo), o modo é o de mostrar antes.

## Levantar

1. `winget export -o <arquivo temporário> --include-versions --accept-source-agreements` numa pasta temporária, nunca por cima do JSON do vault. Se o winget não existir ou o export falhar, pare: diga o erro em uma linha e não mude a nota nem o JSON. Um levantamento só pelo registro do Windows deixaria o JSON sem a fonte de reinstalação.
2. `sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/programas/comparar_winget.py" "<JSON do vault>" "<export novo>"` devolve `novos`, `sumidos` e `versao_mudou`.
3. O export só vê o que o winget conhece. Para o resto (instalado pelo site, sem instalador, da loja), siga o levantamento da skill `liberar-espaco`, se ela existir nesta máquina; senão, o registro do Windows (chaves Uninstall) e `Get-AppxPackage`.
4. **Um `sumido` não quer dizer desinstalado:** o export deixa de fora o programa cuja versão instalada não está no catálogo. Confira se ele ainda está na máquina antes de tratar como desinstalado.

## Aplicar

- **Programa novo:** entra no fim da seção certa, com a fonte que de fato reinstala o programa nesta máquina. Só acréscimo: segue direto.
- **Seção ou fonte que você não sabe decidir:** pergunta no fim, com o que você faria.
- **Programa desinstalado, troca de fonte ou troca de versão registrada:** é troca numa nota protegida. Mostre as diferenças antes, todas juntas, e só aplique com o sim. O desinstalado vai para a seção de não instalados com a explicação que a regra pede; a linha nunca é apagada.
- **O JSON:** o export novo substitui o do vault, mas um programa fora do catálogo continua no JSON com a entrada anterior e a versão corrigida à mão, como a regra manda. Toda entrada que estava no JSON antigo e sumiu do novo é mostrada junto com as diferenças da nota.
- Atualize o `updated` e o `source` da nota.
- `B ponto` com a nota e o JSON.

## Resumo

No formato do gerente: os programas que entraram, os que foram para não instalados, as fontes e versões trocadas, as entradas do JSON mantidas à mão e o que ficou como pergunta.
