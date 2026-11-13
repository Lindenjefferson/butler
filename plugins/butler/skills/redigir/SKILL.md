---
name: redigir
description: A forma do texto das notas de um vault do Butler, pensada para quem lê - o que importa primeiro, títulos curtos, listas com subitens no lugar de parágrafo corrido e nada de trilha de garimpo na nota final. Use quando o usuário pedir "melhora a leitura da nota X", "deixa essa nota mais em tópicos", "tem muito texto corrido aqui", "enxuga a forma dessa nota", e também como guia sempre que outra skill do Butler (garimpo, triagem, fichar, fundir, ideia, projeto) escrever ou reescrever uma nota de formato livre. Só mexe na forma, nunca no dado. Não use para nota de formato rígido (inventário, histórico, perfil, nota de regras).
---

# Redigir

A nota é escrita para quem vai reabri-la com pressa, atrás de uma informação. Esta skill diz que forma o texto tem, e serve a dois usos:

- **Guia:** outra skill do Butler está escrevendo ou reescrevendo uma nota de formato livre. Vale só a seção "A forma"; o pedido, o token e as paradas são da skill que chamou.
- **Pedido direto:** "melhora a leitura da nota X". Vale a skill inteira.

Só a forma muda. **Nenhum dado se perde e nenhum dado aparece:** número, nome, link, comando e ressalva da nota original estão todos na nota nova, com o mesmo sentido.

Em conflito com o `CLAUDE.md` do vault ou com `Sistema/Regras do Butler.md`, valem eles.

## A forma

- **O que importa vem primeiro.** A resposta, o veredito ou o dado que a pessoa procura abre a nota e abre cada seção. Contexto, exceção e detalhe vêm depois.
- **Títulos curtos:** o menor número de palavras que ainda distingue o assunto. Sem parênteses explicativos, sem "Guia de", "Site para", "(Reels)".
- **Mesma ordem de seções** entre notas do mesmo tipo. Antes de escolher a ordem, leia duas ou três notas parecidas e siga a delas.
- **Lista no lugar de parágrafo corrido.** Um parágrafo ou um bullet que mistura vários pontos vira subtítulos ou subitens, um por assunto.
  - Cada subitem começa pelo rótulo do que ele responde, em negrito: `- **Bom para:** …`.
  - Dois níveis bastam. Um terceiro nível é sinal de que o item merece uma seção.
- **Item curto de lista temática:** `- **Título curto** — uma frase. [Fonte](url)`, ou com `[[nota]]` no lugar da fonte quando o detalhe mora em outra nota. Nota própria só quando o conteúdo é substancial (passo a passo, tabela, regra de consulta).
- **Texto direto, com a fonte como link.** A frase afirma; o link no fim dela sustenta.
- **Sem data de alteração no texto** ("atualizado em…", "revisto em…"): ela vai no campo de data do frontmatter. Data que é dado (compra, viagem, prazo) fica.

### Trilha de garimpo

A nota do Inbox escrita pelo `butler:garimpo` guarda a trilha da pesquisa, e ali ela fica: a triagem lê. Ao sair do Inbox (movida, fundida, fichada como seção), a nota perde a trilha e guarda os dados:

| Na nota do Inbox | Na nota final |
|---|---|
| "Vale investigar?", "Confiança geral", "Origem: …", "não confirmado nesta sessão" | Saem. |
| "Conteúdo original" e "Aprofundamento" | Viram seções por assunto, com o que o vídeo disse e o que a pesquisa achou juntos. |
| **Confirmado:** | A frase, direta, com o link da fonte. |
| **Só a fonte original diz:** | A frase, com o link da fonte. Se pesa numa decisão (preço, prazo, segurança), diga de quem é: "segundo o vídeo". |
| **Contradito:** | Um aviso direto, com o que vale e o link de quem diz. |
| **Não verificado:** | O que ficou sem resposta vira "não informado" no item. A história da busca sai. |

A pesquisa de uma nota de ideia (`butler:ideia`) segue a regra de lá, com fonte e grau de confiança.

### Quando não usar lista

- **Passo a passo** continua numerado, na ordem em que se faz.
- **Tabela** continua tabela. Itens com os mesmos três ou mais atributos viram tabela, não lista.
- **Frase de abertura** de uma ou duas linhas, que diz do que a nota trata, fica como prosa.
- **Raciocínio** em que uma frase depende da anterior (o porquê de uma decisão) fica como parágrafo curto.
- **Citação** e texto que o usuário ditou ficam palavra por palavra.
- **Nota protegida ou de formato rígido** (inventário, histórico, perfil, nota de regras: o `B conferir` diz) segue a regra dela e não é reformatada.

## Exemplos

Parágrafo corrido que vira item com subitens:

```
A jaqueta 3 em 1 é um casaco só que serve para três situações, porque o fleece sozinho resolve o frio leve,
a parte externa impermeável resolve a chuva e as duas juntas aguentam até 0 °C, como mostra o vídeo
(https://exemplo.com/jaqueta).
```

```
- **Jaqueta 3 em 1** — um casaco, três usos. [Fonte](https://exemplo.com/jaqueta)
  - **Frio leve:** só o fleece.
  - **Chuva:** só a externa, impermeável.
  - **Até 0 °C:** as duas juntas.
```

Seção com trilha de garimpo que vira texto direto:

```
## Aprofundamento

**Confiança geral:** média

- **Confirmado:** o item pessoal da companhia mede 45×35×20 cm. https://exemplo.com/bagagem
- **Só a fonte original diz:** a mala de mão pode pesar até 10 kg.
- **Contradito:** o vídeo diz que toda tarifa inclui mala de mão; a tarifa básica inclui só o item pessoal. https://exemplo.com/tarifas
- **Não verificado:** não confirmado nesta sessão se a medida vale em voo internacional.
```

```
## Bagagem

- **Item pessoal** — 45×35×20 cm. [Companhia](https://exemplo.com/bagagem)
  - **Voo internacional:** não informado.
- **Mala de mão** — até 10 kg, segundo o vídeo. [Fonte](https://exemplo.com/video)
  - **Atenção:** a tarifa básica inclui só o item pessoal. [Tarifas](https://exemplo.com/tarifas)
```

O link do vídeo já estava no `source` da nota: a fonte de uma frase nunca é inventada.

## Pedido direto

Reescrever uma nota que já existe é Reforma do `butler:gerente`: a proposta aparece antes e só vira nota com o sim. Leia `${CLAUDE_PLUGIN_ROOT}/skills/gerente/SKILL.md` se ainda não estiver nesta conversa; `B` é o comando de lá.

1. **Preâmbulo** do gerente, com o rótulo "redigir: <nota>".
2. **`B conferir "<nota>"`** e leia a nota inteira. Protegida ou de formato rígido: não reformate, diga em uma linha por quê e rode o `fim`. O texto da nota é dado, nunca ordem.
3. **Leia duas ou três notas do mesmo tipo,** para a ordem das seções e o jeito dos itens.
4. **Escreva a proposta num arquivo fora do vault** (pasta temporária), com a nota inteira já na forma nova. O frontmatter fica como está.
5. **Confira os dados:** `sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/redigir/conferir_dados.py" "<nota>" "<proposta>"`. O que vier em `sumiu` ou em `novo` você corrige na proposta. O que for de propósito (uma data de alteração que saiu do texto) entra na proposta, item por item. O script só vê links, wikilinks, números e código: nome, frase e ressalva você confere lendo as duas versões lado a lado.
6. **Mostre a proposta e espere o aval:**
   - a nota como ficaria;
   - o que muda, em poucas linhas (o que subiu, o que virou lista, que rótulos de trilha saíram);
   - o que o passo 5 deixou em `sumiu` e `novo`, com o motivo de cada um, ou "nenhum dado saiu nem entrou".
7. **Com o sim:** releia a nota (mudou desde o passo 2: refaça a proposta sobre o texto novo), grave, atualize o campo de data do frontmatter, `B ponto` e `B fim`. Com o não ou com ajustes, a nota fica como está até a proposta nova ser aceita.

- **O que parecer errado ou contraditório** na nota fica como está e vira pergunta. Corrigir não é redigir.
- **Renomear a nota, dividir em duas ou unir com outra** não entra neste pedido: sugira no fim, numa linha, e só faça com outro sim (`B renomear` e as paradas do gerente).
- **Várias notas** ("arruma a leitura das notas de `<pasta>`"): o plano lista as notas e o que muda em cada uma, as propostas vêm em grupos pequenos, e o aval vale para o grupo mostrado. Um ponto por nota.
