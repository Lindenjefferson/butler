---
name: colheita
description: Grava um resumo curto de um link de vida pessoal (filme, lugar de viagem, receita) direto numa lista que já existe no vault, sem nota no Inbox nem triagem. Chamada só pela skill butler:garimpo, dentro do pedido dele, num lote depois do OK do plano e num link só direto. Não use direto quando o usuário colar um link, nem para guardar link de outro tipo: um link colado vai sempre para o butler:garimpo, que decide se ele passa para cá.
user-invocable: false
---

# Colheita

O modo leve do garimpo: um filme para assistir, um lugar para conhecer numa viagem, uma receita para testar não precisam de "vale investigar?", de aprofundamento nem de triagem. Precisam entrar na lista certa, em uma linha.

`B` é o comando da skill `butler:gerente` (`sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/gerente/butler.py"`). Esta skill não atende pelo nome: quem a chama é o `butler:garimpo`, que já leu o link e o classificou. Ela roda dentro do pedido do garimpo, depois do preâmbulo dele: mesmo token, sem `B inicio` nem `B fim` próprios.

## Quando entra

O garimpo passa para cá um link quando a classificação é uma das que a nota de regras declara em `## Listas da colheita` (`regras.colheita` no `B situacao`: a classificação e o caminho da lista). Classificação sem linha ali vira nota no Inbox, como todo link.

- **Num lote:** o plano do garimpo mostra, para cada link de colheita, a lista e a linha exata que vai ser gravada. O OK do plano é o aval: vale também como o "mostrar antes" do modo sem histórico. Se o usuário corrigiu a classificação no plano, vale a dele: com a nova classificação fora das listas, o link volta para o garimpo, que faz para ele a investigação e a nota no Inbox.
- **Num link só:** não há plano. Acrescentar numa lista que já existe segue direto, e a linha do resumo diz a classificação, a lista e como desfazer. As paradas abaixo (lista que não existe, destino ambíguo) param antes de gravar, como num lote.

## Antes do plano: achar a lista

O garimpo resolve isto antes de montar o plano, para cada link de colheita, e o resultado entra no plano:

1. **O caminho** vem de `regras.colheita`. Caminho com `<destino>` (por exemplo `<pasta>/<destino>.md`) quer dizer uma nota por destino: procure na pasta a nota cujo título é o destino do link (a cidade, o país ou a viagem que o conteúdo cita). Uma só bate: é ela.
2. **Destino ambíguo ou ausente** (duas notas podem bater, ou o conteúdo não diz onde é): o plano mostra as opções e propõe uma; sem destino no conteúdo, a proposta é a nota no Inbox, pelo caminho normal do garimpo.
3. **Lista que não existe:** o plano propõe criá-la (nome, pasta e o primeiro item). Criar fora do Inbox uma lista que não existia é parada do gerente; se a pasta também não existe e o `CLAUDE.md` pede aval para pasta nova, diga isso na mesma proposta. Com o sim, crie a lista pelas regras de nota do `CLAUDE.md` (frontmatter, "Veja também", registro na nota índice). Com o não, o link volta para o garimpo, que faz para ele a investigação e a nota no Inbox; e, se o usuário disser que não quer aquela lista, proponha tirar a linha da classificação de `## Listas da colheita`, para a pergunta não voltar a cada link (a nota de regras só muda com o sim).
4. **Item repetido:** leia a lista. Se o mesmo link ou o mesmo item já está nela (o mesmo filme, mesmo com outro link; o mesmo lugar na mesma viagem; a mesma receita), não grave de novo: o plano diz "já estava em <lista>".
5. **Linha fora do padrão** em `## Listas da colheita` (uma classificação que não é `filme`, `viagem` nem `receita`, ou um caminho com `<` que não seja `<destino>`, como o molde não preenchido): nada vai bater com ela. Avise uma vez no plano e siga sem ela.

## Gravar, depois do OK

1. **Conferir antes de tocar:** `B conferir "<lista>"`, como todo toque do gerente (seção 5 dele). Achado estranho: não grave aquele item, siga com os outros e pergunte no fim.
2. **Reler a lista logo antes de escrever.** Se ela mudou desde que você a leu (o usuário pode estar com ela aberta no Obsidian), não sobrescreva: releia, confira o item repetido de novo e escreva sobre o texto novo. Nunca grave por cima de uma versão antiga.
3. **Escrever o item**, só acrescentando, no fim da lista ou da seção dela que já tem os itens daquele tipo:
   - Siga a forma que a lista já tem (linha, tabela, seção por tipo). Lista vazia ou nova: uma linha `- **<nome>**: <uma frase>. [<site ou autor>](<url_canonica>)`. A URL fica sempre na linha: é por ela que o garimpo reconhece o link repetido depois.
   - A frase diz só o que o link trouxe: no filme, o ano e por que foi indicado; no lugar, a cidade, o que é e o preço quando o conteúdo diz; na receita, os ingredientes principais e o tempo. O que o conteúdo não diz fica de fora. Não pesquise além do necessário para escrever o nome certo (o título exato do filme, o nome do lugar), e não invente dados.
   - Sem data no texto, se o `CLAUDE.md` pedir assim: a data vai no `updated` da lista. Atualize o `updated`.
   - Nota protegida: acrescentar um item segue direto. Formato rígido: siga a regra da nota à risca.

## O que devolve ao garimpo

Para cada link: a lista em que o item entrou (e se ela foi criada), "já estava em <lista>" ou a pergunta que ficou. O garimpo então:

- escreve a linha do link no registro de links (só os do Instagram têm linha) com o status `colhido` e, no destino, o título da lista em texto, sem link; num "já estava", o destino diz "já estava em <lista>";
- inclui no `B ponto` do lote cada lista que mudou ou foi criada e a nota índice, se mudou;
- no JSON do `B fim`: cada lista em `notas` (`"acao": "alterada"`, ou `"criada"` para a lista nova) e um item em `colhidos` por link que entrou numa lista, sem veredito: `{"url": "<url_canonica>", "classificacao": "filme", "nota": "<caminho da lista>"}`. Um "já estava" não entra em `colhidos`;
- no resumo final, junta os colhidos numa linha só: "Colhidos: 2 filmes em <lista>, 1 lugar em <lista>; 1 já estava".

"Desfaz o último garimpo" desfaz a colheita junto: os itens saem das listas, a lista criada some, e uma edição que o usuário fez depois em outro trecho da lista fica.

## Sem histórico

Gravar numa lista que já existe é alterar uma nota fora do Inbox. Sem o histórico funcionando (`historico_ok: false` no preâmbulo do garimpo), mostre o item e a lista antes de gravar e espere o sim, como manda o modo sem histórico do gerente. Num lote, o plano com a linha exata de cada item já é esse "mostrar antes": não pergunte de novo. Num link só, mostre a linha e espere o sim.
