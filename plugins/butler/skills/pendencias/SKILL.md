---
name: pendencias
description: Dona da nota de pendências do vault. Guarda o que ficou para depois ("deixa na fila", "depois a gente faz", "anota pra depois") e as perguntas do Butler que ficaram sem resposta, responde o que está pendente ("ficou algo pendente?", "o que ficou pra trás?") e tira o item quando ele foi feito ou abandonado. Use num vault do Butler; nos repositórios de código, as pendências são de outra ferramenta.
---

# Pendências do vault

A nota é a de `pendencias` em `## Caminhos` de `Sistema/Regras do Butler.md`, de formato rígido. Só esta skill e as escritas toleradas do Wingman mexem nela. `B` é o comando do `butler:gerente`.

## Formato

Uma linha por item, na seção `## Itens`:

```
- [ ] [eu] texto com o contexto mínimo para retomar (desde AAAA-MM-DD)
- [ ] [claude] próximo passo do Claude (depois de: …) (desde AAAA-MM-DD)
```

- `[eu]` é do usuário ou de terceiros; `[claude]` é um próximo passo do Claude.
- Marcadores no fim, entre parênteses, nesta ordem (a do formato único do Wingman): `(até AAAA-MM-DD)` (prazo), `(lembrar AAAA-MM-DD HH:MM)` (gatilho), `(depois de: …)` (dependência), `(de: <projeto>)` (recado de outro projeto), `(trava)` (trava outra coisa) e, por último e sempre, `(desde AAAA-MM-DD)` (a data em que entrou). Os outros são opcionais.
- No vault não existe `[x]`: feito ou desistência tira a linha.

## Entrar na fila

O que entra: o que o usuário mandar deixar para depois e as perguntas do Butler que ficaram sem resposta porque ele seguiu para outro assunto ou disse "depois". Enquanto a conversa ainda está na pergunta, ela não entra. Não é lista de tarefas da vida: só o que nasceu de um pedido no vault ou de uma conversa sobre ele.

1. Preâmbulo do gerente.
2. Acrescente a linha no fim de `## Itens`. É acréscimo: segue direto.
3. `B ponto`, `B fim`, e confirme em uma linha.

## Consultar

"Ficou algo pendente?" é leitura: sem preâmbulo. Leia a nota e responda agrupado por assunto, com o prazo e o gatilho quando houver. Nota vazia: diga que não há pendências.

## Sair da fila

- Quando o usuário disser que foi feito ou que desistiu, a linha sai sem deixar marca. O histórico guarda o que saiu.
- **Nunca tire um item por achar que foi resolvido:** pergunte.
- A exceção é a pergunta do próprio Butler: quando o usuário responde, a linha dela sai.
- O clique "feito" no Wingman tira a linha pela escrita tolerada dele, sem passar por aqui.
- Mudar ou tirar a linha: preâmbulo, edição, `B ponto`, `B fim`.

## O que já estava na memória do Claude

Itens de fila guardados na memória do Claude passam para a nota na preparação do vault (skill `butler:preparar`), com o sim do usuário. A memória só é apagada com o sim.
