---
title: Regras do Butler
type: referencia
tags: [butler, regras, vault]
created: AAAA-MM-DD
updated: AAAA-MM-DD
source: Preparação do vault pelo Butler
---

# Regras do Butler

O que o Butler protege neste vault e o que ele aprendeu com o uso. O Butler lê esta nota a cada pedido e nunca a altera sem o seu sim. Edite à vontade: tirar uma linha de "Notas protegidas" faz o Butler parar de perguntar sobre aquela nota.

Cada item é uma linha `` - `<caminho ou glob>` — <explicação> ``. Caminhos relativos à raiz do vault, com `/`. `*` vale dentro de uma pasta e `**` em qualquer profundidade.

## Notas protegidas

Trocar, remover ou reescrever um dado destas notas sempre mostra antes. Acrescentar segue direto. O `CLAUDE.md` e esta nota são sempre protegidos, mesmo fora da lista.

- `<pasta>/<nota>.md` — <por que é protegida>

## Formato rígido

O formato destas notas vem de uma regra (no `CLAUDE.md` ou na própria nota). O Butler segue a regra e não sugere nada. O que não está aqui é formato livre.

- `<pasta>/*.md` — <onde está a regra>

## Escritas toleradas do Wingman

As únicas escritas do Wingman no vault, todas só acréscimo ou pedido explícito por clique. Esperam a trava do Butler sair e entram no histórico como mudanças de fora. Qualquer outra escrita do Wingman no vault é proibida.

- `<pasta do Inbox>/` — criar uma nota nova pela Captura rápida
- `<nota de pendências>` — acrescentar uma linha
- `<nota de pendências>` — tirar uma linha quando o clique "feito" nomeia o item

## Exceções aprendidas

O que você disse que não precisa perguntar, ou que é assim mesmo. Uma exceção vale para um tipo de mudança num tipo de nota e nunca dispensa a parada para apagar nota, para dado sensível ou para cópia de conflito. Uma linha com dois trechos em código, `` - `<glob>` `<código do achado>` — <por quê> ``, cala aquele achado da conferência naquelas notas.

## Liberações de dado sensível

Alarmes falsos e binários que você liberou para entrar no histórico: `` - `<impressão digital>` — <arquivo e motivo> ``. Para liberar todos os binários de uma pasta de anexos (imagens, PDFs), use o caminho no lugar da digital: `` - `<pasta de anexos>/**` — <motivo> ``. Isso nunca libera um dado sensível escrito numa nota.

## Caminhos

- inbox: `Inbox`
- indice: `<nota índice>.md`
- pendencias: `Sistema/Pendências.md`
- registro de links: `<nota do registro de links>.md` (tire a linha se o vault não tem registro)
- veja tambem: `Veja também`
- nuvem: `<raiz da nuvem sincronizada>` (tire a linha se o vault não está numa pasta sincronizada, ou se o usuário não quis)

## Nuvem: pastas fora da varredura

O que o Butler nunca varre na nuvem, por privacidade. Tire a seção se não há nuvem conectada ou nada foi excluído.

- `<caminho absoluto>` — <motivo>

## Listas para fichar

Onde um item entra direto, no lugar do destino normal de uma nota: o garimpo classifica o link e grava a nota no Inbox, como de costume; na triagem, a `butler:fichar` grava o item no destino daquela classificação e apaga a nota do Inbox. Caminho sem `<destino>` é uma lista compartilhada (um item por linha); caminho com `<destino>` é uma nota por assunto (ganha uma seção inteira, não uma linha — a de cada viagem, por exemplo). Vale para qualquer classificação do garimpo, não só as do exemplo abaixo — acrescente outras linhas se fizer sentido (um jogo, uma ferramenta). Classificação sem linha aqui segue o destino normal da triagem, como qualquer nota. Tire as linhas que não quiser.

- filme: `<pasta>/<lista de filmes>.md` — um item por filme para assistir
- viagem: `<pasta>/<destino>.md` — a nota da viagem com o mesmo destino
- receita: `<pasta>/<lista de receitas>.md` — um item por receita para testar

## Modo sem supervisão

Só para quem roda o Butler sem ninguém para responder o sim de `--forcar` (um serviço de pé). Tire a seção se alguém acompanha os pedidos, que é o caso comum: sem ela, uma trava de outra sessão só sai depois de um sim, como sempre.

- trava abandonada depois de: `<N> min` — uma trava mais velha que isso é liberada sozinha pelo próximo `inicio`

## Veja também

- [[<nota índice>]]
