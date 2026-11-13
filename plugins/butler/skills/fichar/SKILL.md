---
name: fichar
description: Grava uma nota do Inbox direto no destino já declarado no vault para a classificação dela, no lugar do destino normal da triagem, e apaga a nota do Inbox depois — uma linha numa lista compartilhada (filme, receita) ou uma seção inteira numa nota por assunto (viagem). Serve para qualquer classificação do garimpo que tiver destino declarado. Chamada só pela skill butler:triagem, nota por nota, quando a nota tem uma `classificacao` no frontmatter com destino declarado. Diferente da butler:fundir: aqui o destino já está declarado de antemão, então não há dúvida a tirar, e nunca para para perguntar. Não use direto quando o usuário colar um link: um link colado vai sempre para o butler:garimpo, que grava a nota no Inbox; é a triagem, depois, que decide se aquela nota é caso de fichar.
user-invocable: false
---

# Fichar

O modo direto da triagem: quando a classificação de uma nota já tem destino declarado no `CLAUDE.md` do vault, ela não passa pela decisão normal (pasta própria, "Veja também", nota índice) — vai direto para onde já está combinado. Dois formatos, pelo tipo do destino declarado:

- **Lista compartilhada** (destino sem `<destino>` no caminho, como `Lazer/Filmes para Assistir.md`): a nota vira **uma linha**, como fichar um item num catálogo — é o caso de filme e receita hoje.
- **Nota por assunto** (destino com `<destino>` no caminho, como `Viagens/<destino>.md`): a nota vira uma **seção inteira** numa nota dedicada àquele destino (a cidade, o país, a viagem) — é o caso de viagem hoje. O mecanismo de escrever a seção é o mesmo que a `butler:fundir` usa; a diferença é que aqui o destino já está declarado, então não há dúvida a tirar e nunca para para perguntar.

`B` é o comando da skill `butler:gerente` (`sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/gerente/butler.py"`). Esta skill não atende pelo nome: quem a chama é o `butler:triagem`, nota por nota, depois de ler a nota do Inbox inteira. Ela roda dentro do pedido da triagem, depois do preâmbulo dela: mesmo token, sem `B inicio` nem `B fim` próprios.

**Nome interno:** por compatibilidade com quem já lê `B situacao` e o `estado.json` (um painel como o Wingman, por exemplo), a chave continua `colheita` nesses dois lugares, e o status da linha no registro de links continua `colhido`. Só o nome da skill, da pasta e da seção da nota de regras mudaram, de `colheita` para `fichar`.

## Quando entra

A triagem passa para cá uma nota do Inbox quando a `classificacao` do frontmatter dela é uma das que a nota de regras declara em `## Listas para fichar` (ou, em vaults mais antigos, `## Listas da colheita` — as duas seções valem; `regras.colheita` no `B situacao` traz o resultado das duas juntas, nome mantido por compatibilidade). Qualquer classificação pode ter destino declarado, não só `filme`, `viagem` e `receita`: é o `CLAUDE.md` do vault que decide quais fazem sentido. Nota sem `classificacao` ali declarada (ou sem o campo, de antes do garimpo gravá-lo, ou vinda de outro lugar que não o garimpo) segue o destino normal da triagem, como qualquer nota comum.

**O caminho declarado decide o formato:**
- **Sem `<destino>`** (ex.: `Lazer/Filmes para Assistir.md`): é uma lista compartilhada entre vários itens — siga "Lista compartilhada" abaixo.
- **Com `<destino>`** (ex.: `Viagens/<destino>.md`): é uma nota por assunto — siga "Nota por assunto" abaixo.

Em qualquer um dos dois, **lista ou pasta que não existe:** não é caso para decidir sozinho. A nota de Inbox fica como está (sem fichar, sem apagar) e segue o destino normal da triagem para ela; anote a dúvida com `B duvida`, como a triagem já faz para destino incerto — "fichar em `<destino>`" vira a proposta, com a pasta nova (se precisar) na mesma dúvida.

**Linha fora do padrão** em `## Listas para fichar` (uma classificação sem destino claro, ou um caminho com `<` que não seja `<destino>`, como o molde não preenchido): nada vai bater com ela. Diga isso no resumo da triagem e siga sem ela.

## Lista compartilhada

Um filme, uma receita (ou outra classificação do mesmo tipo) vira **uma linha**, no fim da lista ou da seção dela que já tem os itens daquele tipo.

1. **Item repetido:** leia a lista antes de escrever. Se o mesmo item já está nela (o mesmo filme, mesmo com outro link; a mesma receita; ou o equivalente): não grave de novo. A nota do Inbox é apagada do mesmo jeito, e o registro de links (se houver) recebe destino "já estava em `<lista>`".
2. **Conferir antes de tocar:** `B conferir "<lista>"`, como todo toque do gerente (seção 5 dele). Achado estranho: não grave aquele item, deixe a nota do Inbox como está, siga com as outras e pergunte no fim.
3. **Reler a lista logo antes de escrever.** Se ela mudou desde que você a leu (o usuário pode estar com ela aberta no Obsidian), não sobrescreva: releia, confira o item repetido de novo e escreva sobre o texto novo. Nunca grave por cima de uma versão antiga.
4. **Escrever o item**, só acrescentando:
   - Siga a forma que a lista já tem (linha, tabela, seção por tipo). Lista vazia ou nova: uma linha `- **<nome>**: <uma frase>. [<site ou autor>](<url_canonica>)`. A URL fica sempre na linha: é por ela que um fichamento futuro reconhece o item repetido.
   - A frase diz só o que a nota do Inbox já tinha: no filme, o ano e por que foi indicado; na receita, os ingredientes principais e o tempo; em outra classificação, o que fizer sentido para aquela lista. Não pesquise de novo nem invente dados além do que a nota já trouxe.
   - Sem data no texto, se o `CLAUDE.md` pedir assim: a data vai no `updated` da lista. Atualize o `updated`.
   - Nota protegida: acrescentar um item segue direto. Formato rígido: siga a regra da nota à risca.
5. **Apagar a nota do Inbox.** O conteúdo dela já está, condensado, na linha que acabou de ser gravada — o mesmo caso do arquivo de atualização do Inbox que o `butler:gerente` já apaga sem parar (o `CLAUDE.md` manda, e o conteúdo já está no destino). Não é uma parada de "perda de informação": é o fim esperado deste modo.

## Nota por assunto

Uma viagem (ou outra classificação com `<destino>` no caminho) vira uma **seção inteira**, não uma linha — o conteúdo inteiro da nota do Inbox, igual ao que a `butler:fundir` faz ao unir duas notas, só que sem pedir confirmação, porque o destino já está declarado.

1. **Achar a nota do destino:** o destino é a cidade, o país ou a viagem que a nota do Inbox cita; procure, na pasta declarada, a nota cujo título bate. Uma só bate: é ela.
2. **Destino ambíguo** (duas notas podem bater) ou **o conteúdo não diz onde é:** vira a dúvida descrita em "Quando entra" — não adivinhe.
3. **A nota do destino já existe:** `B conferir` nela, releia por último (mesma regra de não sobrescrever versão antiga) e acrescente uma seção nova, no fim ou perto de uma seção parecida, com o conteúdo inteiro da nota do Inbox (não resuma). Acrescente a URL de origem ao `source` da nota de destino (vira lista), se ainda não estiver lá.
4. **A nota do destino ainda não existe:** crie-a nesse caminho, pelas regras de nota do `CLAUDE.md` (frontmatter, "Veja também", registro na nota índice), com o conteúdo da nota do Inbox como base — é a mesma operação de mover uma nota comum do Inbox para um destino já claro, que a triagem já faz sem parar.
5. **Apagar a nota do Inbox.** O conteúdo inteiro dela já está na seção nova (ou ela virou a nota nova, movida) — não é perda de informação.

## O que a triagem faz depois

Para cada nota fichada (ou "já estava"):

- atualiza o status da linha do registro de links (se houver) para `colhido`, com o título do destino em texto, sem link, no campo de destino; num "já estava" (só na lista compartilhada), o destino diz "já estava em `<lista>`";
- inclui no `B ponto` daquela nota o destino (criado ou alterado) e a nota índice, se mudou — no lugar da nota do Inbox, que foi apagada;
- no JSON do `B fim` da triagem: o destino em `notas` (`"acao": "alterada"`, ou `"criada"` para destino novo) e a nota do Inbox apagada (`"acao": "apagada", "de": "Inbox/<título>.md"`);
- no resumo final da triagem, junta os fichados numa linha só: "Fichados: 2 filmes em `<lista>`, 1 seção em `<nota de viagem>`; 1 já estava".

"Desfaz a última triagem" desfaz o fichamento junto: o item sai da lista ou a seção some da nota, a nota criada do zero some (ou volta a existir só com o que tinha antes), a nota do Inbox volta, e uma edição que o usuário fez depois em outro trecho do destino fica.

## Sem histórico

Gravar fora do Inbox é alterar (ou criar) uma nota fora dele. Sem o histórico funcionando (`historico_ok: false` no preâmbulo da triagem), mostre o item e o destino antes de gravar e espere o sim, como manda o modo sem histórico do gerente.
