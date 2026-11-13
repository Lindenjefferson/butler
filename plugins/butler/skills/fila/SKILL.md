---
name: fila
description: Conduz uma fila grande de links (ex.: a exportação dos "Salvos" do Instagram) pelo garimpo, lote por lote, sem o usuário contar nem numerar na conversa. Compara a fila declarada contra o registro de links, escolhe o próximo lote, chama o garimpo para ele, acompanha bloqueio do Instagram e oferece uma triagem com escopo de tempos em tempos, para o Inbox nunca acumular sem controle. Use quando o usuário pedir para "continuar a fila", "próximo lote", "processar os salvos do Instagram" com uma lista grande, ou quando `butler:garimpo` perceber que o pedido tem uma fila declarada maior do que cabe numa resposta só.
---

# Fila

Um lote de `butler:garimpo` sozinho serve bem para um punhado de links. Uma fila (centenas de itens, várias coleções) precisa de outra coisa: saber que lote vem depois, não perder o lugar se a conversa for compactada, e não deixar o Inbox crescer sem parar enquanto os lotes passam. É isso que esta skill faz, por cima do garimpo — ela não lê vídeo nem escreve nota, só decide o próximo lote e manda o garimpo processar.

`B` é o comando da skill `butler:gerente`. O script desta skill é `${CLAUDE_PLUGIN_ROOT}/skills/garimpo/scripts/fila.py` (mora no `garimpo` porque usa o mesmo jeito de ler o registro de links).

## A fila declarada

Uma nota do vault com um ou mais blocos `### <nome> (<N> itens)`, cada um com uma linha por item: `<código>\t<url>` (código e URL separados por tab) ou só a `<url>`. É o formato que a exportação dos "Salvos" do Instagram já cai, depois de lida (a leitura da exportação em si é outra ideia, ainda não construída — ver [roadmap](../../../../docs/roadmap.md)); por ora, alguém monta essa nota à mão ou por outro script antes de chamar a fila.

- **Onde ela está:** se `B situacao` tiver `fila` em `## Caminhos`, use esse caminho sem perguntar. Sem isso declarado, pergunte uma vez qual nota é a fila, e ofereça gravar o caminho em `## Caminhos` para a próxima vez (acréscimo, segue direto).
- **De quem são as notas:** se a fila for de uma pessoa só, pergunte uma vez no começo e reaproveite a resposta em todo o pedido (como o garimpo já faz). Fila com blocos de pessoas diferentes: diga isso e trate cada bloco como um pedido separado, perguntando de novo só quando mudar de pessoa.

## Passo a passo

1. **Preâmbulo do gerente**, rótulo "fila: continuar". Mesmo pedido de sempre: trava, mudanças de fora, histórico.
2. **Achar o próximo lote:**

   ```
   sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" -I "${CLAUDE_PLUGIN_ROOT}/skills/garimpo/scripts/fila.py" "<vault>" --fila "<fila>" --registro "<registro de links>" --tamanho-lote <N> --pular "<nome>" ...
   ```

   `--pular` para cada nome que o usuário já disse para nunca processar (ex.: coleções sensíveis) — pergunte a lista uma vez por conversa, não a cada chamada, e reaproveite a resposta nos lotes seguintes dela. Tamanho do lote: pergunte uma vez (sugestão: 15 a 25, pelo ritmo que o `garimpo` já recomenda para o Instagram) e reaproveite.
3. **Fila sem pendente** (`bloco` nulo no resultado): diga isso, mostre o `progresso` final (quantos no total, quantos já foram) e pare — não há mais o que fazer aqui. Ofereça uma triagem do que sobrou no Inbox, se houver.
4. **Lote achado:** mostre o bloco escolhido e quantos itens tem (deste bloco e da fila inteira), e siga para o `butler:garimpo` com as URLs do resultado, como um lote comum dele — mesmo preâmbulo, mesmas paradas, mesmo formato de nota. O rótulo do pedido do garimpo vira "garimpo: fila — <bloco>".
5. **Bloqueio do Instagram no meio do lote** (vários `falhou` seguidos com erro de login, rate-limit, "tente mais tarde" ou desafio de verificação — o garimpo já reconhece isso): pare a fila também, não só aquele lote; diga para o usuário esperar antes de pedir o próximo lote. Não tente retomar sozinho.
6. **Depois do lote, triagem com escopo de tempos em tempos:** a cada [N] notas novas no Inbox vindas da fila (sugestão: 50, ou o que o usuário preferir — pergunte uma vez), ofereça rodar `butler:triagem` com escopo nessas notas, em vez de deixar acumular até o fim da fila inteira. Com o sim, é um pedido novo (preâmbulo próprio da triagem); com o não, só avise de novo depois de mais [N].
7. **Resumo do lote:** além do resumo que o `butler:garimpo` já dá, acrescente o progresso da fila inteira ("lote N, bloco `<nome>`: X de Y itens dele; Z de W da fila inteira") e diga a próxima ação (ofereça já encadear o próximo lote, se o usuário tinha pedido para seguir sem parar; senão, espere o próximo pedido).

## O que esta skill não faz

Não lê a exportação de um app nem baixa vídeo — isso é o `butler:garimpo`. Não decide classificação, não escreve nota, não grava o registro: tudo isso é do lote do garimpo que ela chama. Não escolhe sozinha pular uma coleção: só pula pelo que o usuário já disse.
