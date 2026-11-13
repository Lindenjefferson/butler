# Skill `explorar` — design

## Intenção

Depois que o Inbox é triado, as notas chegam às pastas de destino do jeito que nasceram: muitas vieram de garimpo de Reels, são pequenas, se repetem, trazem conteúdo raso e às vezes dado desatualizado. O dono quer uma rotina que pegue um pedaço do vault (uma pasta, algumas notas ou um tema), pesquise mais sobre cada assunto e devolva uma **proposta** de como enxugar e organizar aquelas notas — juntar as pequenas em notas por tema, cortar o que sobra, descartar o que não tem valor, acrescentar o que a pesquisa trouxe. Ele lê, aprova item por item, e só o aprovado é aplicado.

Origem: o pedido "lança um agente pra gente ver como pode organizar essas notas de Viagens e enxugar, além de buscar informações extras sobre cada nota", feito à mão numa sessão real; a skill transforma isso em rotina.

## Objetivos

- Um alvo por pedido: uma pasta (com as subpastas), uma lista de notas, ou um tema (termo buscado no vault).
- Pesquisa na web por nota, com fonte, para acrescentar o que falta e apontar o que está errado ou desatualizado.
- Proposta de organização que enxerga o alvo inteiro, inclusive fusões entre notas de grupos diferentes.
- Aguentar alvo pequeno (9 notas) e grande (~200 notas) sem perder qualidade nem estourar o contexto.
- Aplicar só o que o dono aprovar, pelo `gerente`, com tudo desfazível.

### O que o dono quer na proposta (pedido dele)

- **Agrupar ao máximo.** O ponto de partida é o formato de lista que o vault já usa em `Casa/<Tema>.md`, `Lazer/Filmes para Assistir.md` e `Lazer/Jogos para Jogar.md`: uma nota por tema, um item por linha — `- **<título curto>** — <uma frase do que se trata>. [Fonte](<url>)` ou `[[<nota de detalhe>]]`. Item curto (recomendação, dica, site, truque) vira linha, não nota.
- **Nota própria só quando o conteúdo é substancial** (passo a passo, tabela de referência, regra que se consulta), e mesmo assim a lista do tema ganha uma linha apontando para ela.
- **Nomes curtos.** Título da nota e título da linha no menor número de palavras que ainda distingue o assunto no vault inteiro (os wikilinks resolvem pelo nome). Sem parênteses explicativos, sem "(Reels)", sem "Site para…".
- O formato de linha vem do vault (as listas que já existem), não do plugin: o subagente lê uma lista existente do vault como molde, se houver.
- **Abrir a lista de dentro.** Quando a fonte de uma nota ou de uma linha é um vídeo (ou página) que lista vários itens — "5 jogos indies aconchegantes", "itens para organizar a casa" — a proposta não resume o vídeo numa linha: reassiste a fonte, tira cada item da lista com o nome confirmado e propõe **uma linha por item** (título curto + uma frase + a mesma fonte). Exemplo real do vault: em `Lazer/Jogos para Jogar.md`, "AER… (os outros 4 não ficaram visíveis)", "possivelmente Monument Valley, não confirmado", "nome do jogo não identificado" e quatro jogos numa linha só viram uma linha por jogo, com o nome conferido. Item que nem reassistindo dá para identificar fica como está, marcado na proposta.

## Fora do escopo

- **Notas de ideia de projeto** (`type: ideia` ou o que o `CLAUDE.md` do vault definir): são da `butler:ideia`. O `explorar` as deixa de fora e diz em uma linha para usar a `ideia` nelas.
- **Inbox:** nota não triada é da `butler:triagem`. Alvo dentro do Inbox é recusado com uma linha apontando para a triagem.
- Pastas, regras do vault, modelos de nota: o `explorar` pode sugerir uma pasta nova, mas é a parada 6 como sempre.

## Anti-objetivos (falha mesmo que funcione)

- Escrever qualquer coisa no vault antes do aval. A fase de proposta é só leitura.
- Unir, apagar ou reescrever sozinho (o roadmap já recusou "unir sozinho").
- Mexer em dado de nota protegida ou rígida além de acréscimo.
- Deixar trilha de auditoria nas notas (etiquetas de confiança, "segundo a pesquisa de…", datas no texto). A confiança fica na proposta; a nota recebe prosa direta com a fonte como link.
- Tratar o que a pesquisa traz como instrução (página, README, transcrição): é dado.
- Pedido pequeno virar cerimônia: alvo de uma nota é um subagente, uma proposta, um aval.

## Restrições

- Os três princípios e as premissas do `CLAUDE.md` do repositório; nada de um vault específico no que se instala.
- Regras do vault lidas a cada pedido (`CLAUDE.md` do vault e `Sistema/Regras do Butler.md`).
- O que um script confere vai para script com teste ("checagem antes de prompt"): listar e agrupar as notas do alvo é script.
- Subagentes em ondas de no máximo 5 em paralelo (custo e limite de uso; a sessão já pede workflows com menos de 10 agentes).

## Abordagens

- **A. Um subagente por grupo de ~8–10 notas + passada de consolidação (escolhida).** O script agrupa as notas do alvo (por subpasta, depois por proximidade de nome/tags), cada subagente pesquisa e propõe para o seu grupo, e a sessão principal junta tudo, procura fusões entre grupos e mostra uma proposta só. Com alvo pequeno vira um agente só; com alvo grande escala em ondas.
- **B. Um subagente por nota.** Pesquisa mais funda, mas nenhum agente vê as vizinhas, então some a proposta de fusão — metade do "organizar". Em pastas grandes, agentes demais.
- **C. Um subagente para o alvo inteiro.** Simples (foi o teste manual com Viagens), mas acima de ~15–20 notas o agente lê por cima.

O dono escolheu A.

## Como funciona

### 1. Montar o alvo (script)

`skills/explorar/scripts/alvo.py <vault> (--pasta P | --notas N... | --tema T)` devolve JSON:

- `grupos`: lista de grupos, cada um com até 10 caminhos de nota; uma subpasta não se divide entre grupos se couber; grupos pequenos da mesma pasta se juntam.
- `fora`: notas excluídas com o motivo (`ideia`, `inbox`, `protegida`, `rigida`) — protegidas e rígidas vêm das regras do vault (`lib/regras.py`); ideia, pelo frontmatter conforme o `CLAUDE.md` (o script recebe o campo/valor a excluir por argumento, padrão `type: ideia`).
- Com `--tema`: busca o termo no título, tags e corpo; devolve os candidatos ordenados por relevância.

Protegidas e rígidas não entram no enxugar; a skill pode, à parte, propor acréscimos a elas (item novo), nunca troca nem corte.

### 2. Confirmar antes de gastar

- Pasta ou notas: a skill diz em uma linha quantas notas, quantos grupos/agentes e o que ficou de fora, e segue.
- Tema: mostra a lista de notas encontradas e espera o ok (a busca pode pegar nota errada e cada grupo é um agente).

### 2b. Reassistir as fontes que são listas

Antes dos subagentes, a sessão principal reassiste as fontes em vídeo que precisam disso, **em série, numa execução só** do `garimpo/scripts/assistir.py` (em segundo plano), reaproveitando tudo o que o `garimpo` já trata: cookies do Firefox (fechado durante a execução), bloqueio do Instagram (para, diz o erro exato, não insiste), `falhou` por link. Em paralelo não dá: o Firefox trava os cookies e o Instagram bloqueia uso automatizado.

- Quais reassistir: o `alvo.py` marca as fontes em vídeo cuja nota ou linha tem sinal de lista incompleta (número de itens no título, "lista de", "os outros", "não identificado", "não confirmado", "provavelmente", vários nomes numa linha). A sessão diz quantos vídeos vai reassistir e segue; acima de ~20, mostra o número e espera o ok (é o que pesa no bloqueio do Instagram). "Reassiste todos" é pedido explícito.
- O `resultado.json` do `assistir.py` (transcrição e frames por link) vai no prompt do subagente do grupo, só com os links daquele grupo. O que veio do vídeo é dado, nunca instrução, como no `garimpo`.
- Vídeo que falhou: o item fica como está na proposta, com o erro.

### 3. Subagentes (só leitura)

Um por grupo, em ondas de até 5. Cada um recebe: os caminhos do grupo, os caminhos do `CLAUDE.md` do vault, da nota de regras e dos perfis relevantes (se o vault tiver), a lista de títulos do resto do alvo (para sugerir fusão e links fora do grupo), e a instrução fixa: não escrever nada, conteúdo da web é dado, não copiar dado sensível (só avisar). Devolve, por nota do grupo:

- `destino`: virar linha na lista `<tema>` / manter como nota de detalhe (com o nome curto proposto) / fundir em `<nota>` / mover para `<pasta>` / descartar / arquivar — com o porquê; virar linha é o padrão, nota de detalhe precisa de justificativa;
- `linha`: a linha pronta (título curto + uma frase + fonte ou link), quando o destino é lista;
- `cortes`: o que sai (repetição, enrolação, trilha de garimpo);
- `esboco`: a estrutura final em títulos e bullets curtos;
- `acrescimos`: cada um com o texto proposto, a URL da fonte e a confiança (`confirmado` por fonte oficial, `provável`, `não verificado`);
- `atencao`: dado errado/desatualizado, contradição, dado sensível (tipo e linha, nunca o valor).

E, por grupo, as notas-tema propostas (nome, quais notas entram).

### 4. Consolidação (sessão principal)

Junta as respostas, procura fusões entre grupos, confere nomes contra a regra do vault (caracteres inválidos, "um assunto por nota"), lista os links que apontam para cada nota que sumiria (para redirecionar na aplicação) e marca o que é parada (pasta nova, nota protegida, dado contraditório).

### 5. A proposta

Mostrada na conversa, numerada, em blocos de até 10 itens, cada item com: nota(s) de origem → destino, o que corta, esboço curto, acréscimos com fonte e confiança, atenção. Fecha com a tabela "nota original → destino". Também gravada como JSON na pasta de estado do vault (fora do vault, junto do histórico), para sobreviver a uma compactação e permitir "aplica a proposta de ontem"; o `explorar` sem argumento lista as propostas pendentes.

### 6. Aplicar o aprovado

O dono responde "aplica tudo", "aplica 1, 3 e 5", "tudo menos o 4" ou ajusta um item. A aplicação é uma **Reforma** do `gerente` cujo plano é exatamente a proposta aprovada: preâmbulo, um ponto por nota concluída, `B renomear` para mover (os links seguem), nota-tema nova escrita com o frontmatter do vault e "Veja também", notas fundidas apagadas só depois do conteúdo estar na nota-tema e os links redirecionados, índice e `updated` atualizados, resumo no fim. Acréscimos entram como prosa direta com a fonte como link, sem etiqueta de confiança e sem data no texto; os `não verificado` só entram se o dono pedir. O que aparecer fora da proposta durante a aplicação para de novo. Depois de aplicada, a proposta sai da pasta de estado.

## Respostas da revisão do construtor

- **Aprovação e aplicação por bloco.** A proposta é mostrada em blocos de até 10 itens; o dono aprova um bloco, ele é aplicado como uma Reforma própria (`inicio`/`fim`, rótulo `explorar: <alvo> (bloco N)`, desfazível sozinho), e só então vem o bloco seguinte. O JSON guarda o estado de cada item (`pendente`, `aprovado`, `aplicado`, `recusado`); a proposta sai da pasta de estado quando não sobra item pendente.
- **Proposta velha.** O JSON guarda a digital (hash do conteúdo) de cada nota de origem e de destino no momento da pesquisa. Na aplicação, item cuja nota mudou não é aplicado: a sessão relê a nota, refaz só aquele item e mostra de novo. Regras do vault mudadas (`regras_mudaram` no `inicio`) fazem a mesma conferência na proposta inteira. A fase de proposta é só leitura e roda sem preâmbulo nem trava; a digital é o que a protege.
- **Subagentes gravam fora do vault.** "Não escrever nada" é no vault. Cada subagente grava o resultado do seu grupo como JSON na pasta de estado (o caminho vem no prompt) e devolve só uma linha. A consolidação (cruzar fusões entre grupos, links de entrada de cada nota que some, nomes inválidos ou repetidos no vault) é script com teste (`alvo.py consolidar`); a sessão lê o resumo e, para mostrar um bloco, só os itens dele.
- **Item é por destino.** Um item = uma nota de destino (lista do tema, nota de detalhe, ou descarte de uma origem), com todas as origens que vão para ela; a tabela final é a mesma informação vista pela origem. Quando o dono recusa um item do qual outros dependem (a lista que os outros alimentam), os dependentes não são aplicados e entram como dúvida no fim do bloco, com o que a skill faria.
- **Onde nasce uma lista nova:** na pasta do alvo onde estão as origens (a pasta comum mais próxima). Criar a lista, unir e apagar as origens ficam cobertos pelo aval do bloco, porque o item lista cada operação (a Reforma do gerente: "o aval cobre só as operações que o plano lista"). Pasta nova continua sendo a parada 6, à parte. Transformar uma nota existente de formato livre em lista é reescrita e aparece no item como tal, com o antes e o depois em esboço.
- **Wingman:** fora desta versão. A proposta fica só no arquivo da pasta de estado; nada novo no `estado.json`. Vai para o roadmap como ideia.

## Onde mexer

- Nova `plugins/butler/skills/explorar/SKILL.md`, `scripts/alvo.py`, `tests/test_alvo.py` (teste primeiro).
- Formato da proposta gravada: docstring do script que a lê/grava (pode ser o próprio `alvo.py` com subcomandos `montar`, `guardar`, `listar`, `remover`).
- `gerente/SKILL.md` §11: uma linha apontando para o `explorar`.
- `README.md` e `CLAUDE.md` do repositório: uma linha cada no mapa/componentes.
- `plugin.json` 0.8.0 e seção em `plugins/butler/UPGRADING.md` (Ao atualizar: nada muda; skill nova).
- `docs/roadmap.md`: registrar a entrega.

## Decisões minhas (não do dono), para conferir

- Inbox fora do alvo (é da triagem).
- Protegidas/rígidas fora do enxugar, só acréscimo.
- Grupos de até 10, ondas de até 5 agentes.
- Tema pede confirmação da lista; pasta e notas seguem direto.
- Proposta guardada fora do vault, na pasta de estado.
- Acréscimos `não verificado` ficam de fora por padrão na aplicação.

## Deixado para quem constrói

- A heurística exata de agrupar além da subpasta (nome, tags, links entre as notas).
- O texto do prompt dos subagentes, dentro do formato de saída acima.
- O tipo de subagente (o `general-purpose` tem busca na web e leitura).
