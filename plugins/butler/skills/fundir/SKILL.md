---
name: fundir
description: Decide e, com o sim do usuário, une uma nota do Inbox a uma nota que já existe sobre o mesmo assunto, fora do Inbox — a nota do Inbox vira uma seção nova na nota existente, e some. Chamada só pela skill butler:triagem, nota por nota, quando a nota do Inbox tem o campo `relacionada` no frontmatter (o `CLAUDE.md` do vault define o nome do campo). Diferente da butler:fichar: aqui o "mesmo assunto" foi descoberto por busca, não está declarado de antemão em lugar nenhum, então a decisão é sempre do usuário, nunca automática.
user-invocable: false
---

# Fundir

Quando o `butler:garimpo` acha, ao escrever uma nota nova, que o mesmo assunto já tem nota em outro lugar do vault (fora do Inbox), ele não funde sozinho: cria a nota no Inbox normalmente, com `relacionada: "[[Nome da nota]]"` no frontmatter, e deixa a decisão para a triagem. É aqui que ela é tomada.

`B` é o comando da skill `butler:gerente` (`sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/gerente/butler.py"`). Esta skill não atende pelo nome: quem a chama é o `butler:triagem`, nota por nota. Ela roda dentro do pedido da triagem, depois do preâmbulo dela: mesmo token, sem `B inicio` nem `B fim` próprios.

## Por que isso nunca é automático

A `butler:fichar` grava direto, sem perguntar, porque o destino de cada classificação já está declarado de antemão em `## Listas para fichar` — não há julgamento a fazer, só aplicar a regra. Aqui é diferente: "mesmo assunto" é uma leitura de conteúdo, por busca de nome (regra 1 de "Onde cada nota vai" do garimpo), que pode estar errada — duas notas podem parecer do mesmo assunto e não serem, ou serem do mesmo assunto mas merecerem ficar separadas (histórico diferente, pessoa diferente, nível de detalhe diferente). Por isso a regra do gerente trata unir como "perda de sentido": **sempre para antes.**

## Quando entra

A triagem passa para cá toda nota do Inbox que tiver o campo de relacionada (o `CLAUDE.md` do vault define o nome do campo, normalmente `relacionada: "[[Nome da nota]]"`). Duas chamadas possíveis:

1. **Propor** (durante a passada normal da triagem, nota por nota): monte a proposta e anote a dúvida com `B duvida`, como a triagem já faz para todo destino incerto. A nota de Inbox não é tocada ainda — ela continua lá até o usuário responder.
2. **Aplicar** (num pedido novo, depois que o usuário respondeu as perguntas do fim de uma triagem): executa de fato a decisão que o usuário deu para aquela dúvida.

## Propor

1. Leia a nota apontada por `relacionada` e a nota do Inbox inteiras.
2. Monte a proposta: qual seção a nota do Inbox viraria (o título dela, sem o "Conteúdo original"/"Aprofundamento" como títulos — adapte ao estilo da nota de destino) e onde ela entraria (fim da nota, ou perto de uma seção parecida, se houver).
3. `B duvida --token <token> --pergunta "Unir '<nota do Inbox>' com '<nota relacionada>'?" --proposta "<resumo da seção que entraria>" --nota "<nota do Inbox>"`.
4. Se a nota do Inbox também precisar de uma subpasta nova para ficar separada (um projeto que passa a ter duas notas, por exemplo), isso entra na mesma dúvida, como a triagem já faz.

## Aplicar, depois do sim

Só roda quando o usuário já respondeu que sim, nesta dúvida específica (nunca por conta própria):

1. **Conferir antes de tocar:** `B conferir "<nota relacionada>"`, como todo toque do gerente. Nota protegida ou de formato rígido: siga a regra dela à risca; nota de formato livre, mantenha o estilo que ela já tem.
2. **Reler a nota relacionada logo antes de escrever.** Mudou desde que você leu: releia e funda sobre o texto novo.
3. **Escrever a seção nova**, no fim da nota ou perto de uma seção parecida, com o conteúdo inteiro da nota do Inbox (não um resumo de uma linha — isso é o que diferencia de `butler:fichar`). Sem data no texto, se o `CLAUDE.md` pedir assim: atualize só o `updated`. Acrescente a URL de origem ao `source` da nota relacionada (vira lista), se ainda não estiver lá.
4. **Apagar a nota do Inbox.** O conteúdo dela já está, inteiro, na seção nova — não é perda de informação, é o fim esperado da fusão que o usuário acabou de confirmar.
5. **Registro de links**, se a nota do Inbox vier de um link: o destino da linha passa a ser o título da nota relacionada, status conforme a regra da nota do registro para "movida/unida".

## Com o não

A nota do Inbox segue como nota nova (tira o campo `relacionada`) e é triada pelo caminho normal — pasta pelo `CLAUDE.md`, "Veja também" com um link para a nota relacionada (as duas ficam, uma ligada à outra).

## Como desfazer

"Desfaz a última triagem" (ou o rótulo do pedido de aplicar respostas) desfaz a fusão junto: a seção sai da nota relacionada, a nota do Inbox volta, e uma edição que o usuário fez depois em outro trecho da nota relacionada fica.
