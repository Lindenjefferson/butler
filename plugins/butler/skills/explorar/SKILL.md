---
name: explorar
description: Explora um pedaço já triado de um vault do Butler (uma pasta, algumas notas ou um tema), pesquisa mais sobre cada nota e propõe como enxugar e organizar — juntar notas pequenas em listas por tema, cortar o que sobra, descartar, acrescentar o que a pesquisa trouxe — e aplica só o que o usuário aprovar, bloco por bloco. Use quando o usuário pedir "explora a pasta X", "enxuga e organiza X", "pesquisa mais sobre as notas de X", "aplica a proposta", ou chamar `/butler:explorar <alvo>`; sem argumento, lista as propostas pendentes.
---

# Explorar

Uma proposta lida e aprovada pelo usuário, aplicada como Reforma do `butler:gerente`. Antes de começar, leia `${CLAUDE_PLUGIN_ROOT}/skills/gerente/SKILL.md` se ainda não estiver nesta conversa: preâmbulo, paradas, conferência, pontos e resumo vêm de lá. `B` é o comando de lá. O porquê de cada passo está no design da skill (`docs/superpowers/specs/*-explorar-design.md` do repositório do plugin); as seções citadas abaixo são as dele.

Os scripts desta skill, rodados no Bash (`A` e `P` abaixo):

```
A = sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" -I "${CLAUDE_PLUGIN_ROOT}/skills/explorar/scripts/alvo.py" "<vault>"
P = sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" -I "${CLAUDE_PLUGIN_ROOT}/skills/explorar/scripts/proposta.py" "<vault>"
```

Argumentos, saídas, formato da proposta e dos itens: docstring de cada script. Até o aval, tudo é só leitura no vault, sem preâmbulo nem trava; o que protege a proposta é a digital de cada nota.

**Sem argumento:** `P listar`. Uma linha por proposta (rótulo, itens abertos) e a pergunta de qual continuar; nenhuma, peça um alvo. Continuar ("aplica a proposta de ontem") retoma no passo 6, no primeiro bloco com item `pendente`.

## 1. Regras e limites (Restrições, Fora do escopo)

Leia o `CLAUDE.md` do vault e a nota de regras (`B situacao`). Alvo dentro do Inbox: recuse em uma linha, apontando a `butler:triagem`. O campo e o valor que marcam uma nota de ideia vêm do `CLAUDE.md` (padrão `type: ideia`).

## 2. Montar o alvo (§1, §2)

`A montar (--pasta P | --notas N ... | --tema T) --excluir-campo <campo> --excluir-valor <valor> > <pasta temporária>/alvo.json`.

- Saída 1: alvo vazio, diga em uma linha e pare. Saída 2: mostre o erro.
- Pasta ou notas: uma linha com quantas notas, quantos grupos (agentes) e o que ficou em `fora` por motivo, e siga. As de motivo `ideia` ganham a linha "use a `butler:ideia` nelas"; as de `inbox`, a `butler:triagem`.
- Tema: mostre sempre `tema_candidatos` e espere o ok. A busca pode pegar nota de sistema (o índice, o `CLAUDE.md`), que o usuário tira. Com a lista acertada, monte de novo com `--notas`.

## 3. Reassistir as fontes que são listas (§2b)

- `reassistir` vazio: pule. Até 20 vídeos: diga quantos e siga. Acima de 20: mostre o número e espere o ok. "Reassiste todos" é pedido explícito.
- Rode o `assistir.py` numa execução só, em segundo plano, com todas as URLs e `--saida <pasta temporária>`, como o passo 1 da `butler:garimpo` (avise antes que o Firefox fica fechado durante a execução). As regras de login, bloqueio e status são as de lá, em `${CLAUDE_PLUGIN_ROOT}/skills/garimpo/SKILL.md`.
- Bloqueio do Instagram: pare de assistir, mostre o erro exato e não insista. Link com `falhou`: o item dele fica como está na proposta, com o erro.

## 4. Pesquisar e propor (§3)

`P iniciar --alvo <alvo.json> --rotulo "explorar: <alvo>"`. Guarde o `id`.

Um subagente `general-purpose` por grupo, em ondas de até 5 lançadas na mesma mensagem, com o prompt de `${CLAUDE_PLUGIN_ROOT}/skills/explorar/references/subagente.md` preenchido: os caminhos do grupo, o do `CLAUDE.md`, o da nota de regras e o dos perfis que o vault tiver para o tema; uma lista do vault (nota de um item por linha), de preferência perto do alvo, como molde de linha; os títulos do resto do alvo; o trecho do `resultado.json` só com os links do grupo; a `saida` do grupo; e o caminho do `proposta.py` (o formato do `g*.json` está na docstring dele). Cada um grava o JSON e devolve uma linha.

## 5. Consolidar (§4)

`P consolidar --id <id>`. Grupo em `faltam_grupos`: relance o subagente dele uma vez; faltando de novo, vira aviso no bloco 1. Os `avisos` de entrada ignorada (`alvo_vazio`, `fundir_em_si`) também vão para o bloco 1.

## 6. Mostrar um bloco (§5)

`P bloco --id <id> --n <N>`. Por item, numerado: origens → destino (tipo), as operações, o que corta, o esboço curto, os acréscimos com fonte e confiança, a atenção. Em destaque: `pasta_nova` (parada 6, aval à parte), `protegida` (só acréscimo), `nome_invalido`, `nome_repetido`. Acréscimo `nao_verificado` aparece marcado como "fica fora, salvo pedido". O último bloco fecha com a tabela nota original → destino.

O usuário responde "aplica tudo", "aplica 1, 3 e 5", "tudo menos o 4" ou ajusta um item. Ajuste: grave-o no `g*.json` do grupo, rode `consolidar` de novo (número e estado se mantêm) e mostre o item outra vez.

## 7. Aplicar o bloco aprovado (§6, revisão do construtor)

1. `P marcar --id <id> --itens <...> --estado recusado` para o que ele recusou e `--estado aprovado` para o resto. Os dependentes de um recusado ficam `bloqueados`.
2. Preâmbulo do gerente com o rótulo `explorar: <alvo> (bloco N)`. `regras_mudaram`: releia as regras e confira contra elas os itens aprovados.
3. `P conferir --id <id> --itens <aprovados>`. Item em `mudou` não se aplica agora: releia as notas, refaça só ele (como no ajuste), rode `P redigitar` para ele e mostre-o de novo depois deste bloco.
4. Item por item, o plano é exatamente as `operacoes` dele. Um item só se aplica depois de cada item do seu `depende_de` estar `aplicado`; o número e a posição no bloco não garantem a ordem. Se quem cria o destino está num bloco seguinte, o dependente espera e vira dúvida até lá.
   - `B conferir` em cada nota antes de tocar.
   - Lista ou nota de detalhe nova: o frontmatter do vault, as linhas no formato das listas dele e o "Veja também". Acréscimos entram como texto direto com a fonte como link, sem etiqueta de confiança nem data.
   - Mover ou renomear: `B renomear` (os links seguem).
   - Apagar uma origem só depois do conteúdo dela estar no destino e dos `links_de_entrada` redirecionados para o destino.
   - Nota índice e `updated` das notas tocadas. Origem que vem de um link do registro de links (`## Caminhos` nas regras): a linha dele ganha o destino novo, como a regra do registro manda.
   - `B ponto` por nota concluída e `P marcar --estado aplicado` por item.
5. Dependente de um recusado (`bloqueado`) ou que ainda espera um bloco seguinte: `B duvida`, com o que a skill faria. O que aparecer fora do plano para de novo.
6. Resumo no formato do gerente e `B fim`. Depois, os itens refeitos e o próximo bloco (passo 6).

## 8. Fim da proposta

Sem item `pendente` nem `aprovado` (`P listar` não traz mais o `id`), `P remover --id <id>`. O resumo final lista as notas criadas e as alteradas.
