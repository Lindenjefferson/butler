# Histórico do plugin `butler`

O que cada versão entregou e o que muda para quem atualiza. O arquivo vai junto com cada versão instalada: a skill `atualizar` lê o **Ao atualizar** de cada versão pulada, da mais antiga para a mais nova. Termine o pedido em andamento no vault antes de atualizar (a skill `atualizar` confere). As ideias que ainda não viraram versão estão no [roadmap](../../docs/roadmap.md). O que é major, minor e patch está no [`CLAUDE.md`](../../CLAUDE.md).

## 0.7.0 — modo sem supervisão: trava com prazo, perguntas que não se perdem, diário de pedidos

Pedido do dono, na mesma rodada da revisão do Fable (0.6.1): pensando em rodar o Butler sem ninguém no terminal por longos períodos (um serviço de pé, tipo um bot do Duet), pediu para desenhar e construir o que fosse possível dos pontos que mudam "quem decide o quê" sem comprometer "parar pelo risco" — deixando o que precisa mesmo da decisão dele, caso a caso, documentado no [roadmap](../../docs/roadmap.md).

- **Melhoria — perguntas pendentes não se perdem entre pedidos:** o `fim` substituía as `perguntas` do `estado.json` pelas do pedido que terminou agora; as de um pedido anterior, ainda sem resposta, saíam da foto que um painel lê (a nota com a dúvida continuava no Inbox, só não aparecia mais ali). Agora `fim` mantém as perguntas de pedidos anteriores que ainda não foram respondidas, e só as tira quando a nota que elas citam deixa de existir (foi fichada, fundida ou apagada) — vale sempre, não só no modo sem supervisão, porque é uma correção e não uma mudança de política.
- **Melhoria — `## Modo sem supervisão` na nota de regras, com prazo para a trava:** declarando `- trava abandonada depois de: \`<N> min\``, uma trava mais velha que isso é liberada sozinha pelo próprio `inicio`, sem o `--forcar` de um sim — pensado para quando não há ninguém para dar esse sim. Sem a seção (o caso comum, alguém acompanhando), nada muda. A resposta do `inicio` traz `trava_abandonada_por_prazo` quando isso acontece, para constar.
- **Melhoria — diário de pedidos:** `lib/diario.py` grava, na pasta de estado (fora do vault), uma linha por `inicio`, `fim`, trava ocupada, trava abandonada por prazo e `fim` recusado por `sem_ponto` — o que hoje só existe na tela da conversa e se perde sem alguém olhando na hora. Novo comando `B diario [--limite N]`, só leitura.
- **Não entrou:** "pedido explícito já é o aval" (gerente, §4) ainda não distingue canal nem identidade de quem pediu — útil para o dono corrigindo na hora, arriscado num bot onde qualquer mensagem que chega é "o usuário". Isso é desenho de quem pode pedir o quê por qual canal, não dá para decidir sozinho; ficou em "Não triadas" no roadmap para o dono decidir com calma.

**Ao atualizar:** nada muda sozinho para quem não declarar `## Modo sem supervisão` na nota de regras — a trava continua exigindo `--forcar` com um sim, como sempre. As perguntas pendentes passam a acumular automaticamente, sem precisar de nada novo na nota de regras. O diário começa vazio: eventos de antes desta versão não aparecem nele.

## 0.6.1 — `--continuando` evita que a retomada leve o próprio pedido para "mudança de fora"

Pedido do dono: depois da 0.6.0, mandou outra revisão de um agente sem contexto do projeto (Fable), desta vez pensando num uso autônomo (sem alguém no terminal, tipo um bot de pé). Achou um defeito reproduzível e deixou mais pontos (trava sem jeito de saber se quem a pegou ainda está de pé, perguntas pendentes de um pedido somem quando o pedido seguinte termina, nada registra o que falhou fora da conversa) que mudam quem decide o quê — ficaram no [roadmap](../../docs/roadmap.md), em "Não triadas", para o dono decidir antes de entrarem numa versão.

- **Defeito — `inicio` na retomada podia gravar o trabalho do próprio pedido como "mudança de fora":** escrever uma nota e, antes do `B ponto` dela, precisar chamar `inicio` de novo (retomada, por uma compactação da conversa ou um serviço que resume o pedido) fazia essa escrita entrar na varredura de "mudanças de fora" junto com qualquer mudança de fato externa — o git não distingue as duas, e `registrar_fora` rodava para as duas igual. O `B ponto` seguinte não achava mais nada para gravar (a nota já estava num ponto, só do tipo errado) e o `B desfazer --pedido` desse pedido saía com "nenhum ponto com esse pedido": o trabalho ficava preso num ponto que o desfazer do pedido não alcança. Como o git não tem como adivinhar de quem é uma mudança sem ponto, a correção não é automática: `inicio` ganhou `--continuando "<nota>" ...`, para quem está retomando avisar quais notas sem ponto são do próprio pedido. Sem o aviso, a retomada continua varrendo tudo como mudança de fora, exatamente como antes — por isso dois testes que já cobriam essa varredura (edição por fora entre um ponto e a retomada, nota nova por fora durante o pedido) continuam passando sem mudar. `gerente/SKILL.md` já instrui a passar `--continuando` nesse caso.

**Ao atualizar:** nada muda sozinho — o comportamento padrão da retomada é o mesmo de antes. Quem seguir o `gerente/SKILL.md` novo (ou pedir para o Claude reler a skill) passa a usar `--continuando` na hora certa; sem isso, continua como estava, sem regressão.

## 0.6.0 — revisão de fresh-eyes da 0.5.0

Pedido do dono: depois de instalar a 0.5.0, mandou uma revisão de um agente sem contexto do projeto (Fable) olhar o plugin e o uso real do dia no vault de teste. Achou que a própria 0.5.0 tinha furos (ver abaixo) e mais pontos de atrito num dia pesado de `garimpo`. Branch `fix/colheita-so-na-triagem` (mesma do PR anterior, continuada).

- **Defeito — a 0.5.0 não bastava sozinha:** o "Ao atualizar" dela dizia "nada muda", mas a nota de regras e o `CLAUDE.md` de um vault preparado antes da 0.5.0 continuam com o texto antigo da colheita (grava direto, sem Inbox nem triagem) — e "as regras moram no vault" faz uma sessão fiel reproduzir o bug de novo. Esta versão não muda o texto do `preparar`: ele já gera a seção nova (`## Listas para fichar`) para quem preparar um vault do zero. Quem já tinha o vault preparado precisa editar a `CLAUDE.md` e a nota de regras à mão (ou pedir para o Claude fazer), não tem automação para isso ainda.
- **Defeito — `garimpo` grava um ponto por lote, não por nota:** contrariava a regra geral do gerente ("um ponto por nota concluída"). Virou um `B ponto` por nota, logo após escrevê-la; o `B fim` continua sendo um só, no final do lote.
- **Defeito — o status do registro nascia `triado` antes da triagem rodar:** um link que só virou nota no Inbox não foi triado ainda, mas o status dizia que sim, e o registro não conseguia responder "o que ainda está esperando?". O garimpo agora usa o status que a nota do registro definir para esse estado (sugestão: `no Inbox`), com `triado` como nome antigo de fallback para quem não tiver essa distinção.
- **Melhoria — triagem passa a ler subpastas do Inbox e aceita escopo:** "Liste as notas do Inbox" agora é recursivo, e um pedido pode vir com escopo ("tria só `Inbox/Viagens`"). Subpasta dentro do Inbox virou acréscimo (nunca para, nem para criar nem para tirar quando esvaziar) nas regras do gerente — antes, criar qualquer subpasta era parada.
- **Melhoria — `triagem` infere `classificacao` ausente:** nota com cara de garimpo (tem "Vale investigar?") mas sem o campo (de antes da 0.5.0, ou de outra origem) agora entra numa dúvida agrupada no fim, propondo a classificação inferida, em vez de ser sempre tratada como referência comum.
- **Melhoria — `garimpo` ganha formato mais leve pra conteúdo pessoal:** a seção "Aprofundamento" com as quatro etiquetas de confiança agora é opcional quando não há nada de fato pesquisado fora do próprio vídeo (receita, treino, viagem, casa, filme); "Veja também" sem nota relacionada fica só com o título da seção, sem frase de preenchimento; vários vídeos do mesmo assunto no lote passam para formato de lista (não uma seção cheia por vídeo) acima de ~10 itens.
- **Melhoria — `fundir` cita as exceções aprendidas:** uma fusão do mesmo tipo já confirmada antes (`## Exceções aprendidas` na nota de regras) dispensa perguntar nas próximas vezes, o que já era verdade na prática mas não estava escrito na skill.
- **Skill nova `fila`:** conduz uma fila grande de links (ex.: a exportação dos "Salvos" do Instagram, já colada numa nota com blocos por coleção) pelo `garimpo`, lote por lote — acha o próximo lote comparando a fila contra o registro de links (`scripts/fila.py`, com teste), acompanha bloqueio do Instagram, mostra o progresso e oferece uma triagem com escopo de tempos em tempos, para o Inbox não acumular como aconteceu nesse uso real. Pedida pelo dono depois da revisão do Fable, no mesmo pedido.

**Ao atualizar:** veja o primeiro item acima — edite a `CLAUDE.md` e a `Sistema/Regras do Butler.md` do seu vault para tirar a exceção antiga da colheita e declarar `## Listas para fichar` no formato novo (o `fichar`/`garimpo`/`triagem` já aceitam o nome antigo da seção, `## Listas da colheita`, então essa parte não quebra; é só o texto da `CLAUDE.md` que fica desatualizado se não for revisado). Nada mais muda sozinho: pontos por lote já gravados continuam válidos, e o status `triado` de notas que só estão no Inbox (de antes desta versão) só vira `no Inbox` se você pedir para o Claude migrar as linhas.

## 0.5.0 — a colheita virou fichar, com fundir ao lado, e só rodam na triagem

Pedido do dono: um uso real do `garimpo` (vários lotes de links de Reels, num vault de teste) mostrou a skill mesclando conteúdo direto em nota fora do Inbox e rodando a colheita dentro do próprio garimpo, pulando a triagem — um desvio das regras já escritas em "Onde cada nota vai", que o dono pediu para corrigir na raiz. No mesmo pedido, o nome `colheita` se mostrou confuso na prática (o dono achou que a skill fazia outra coisa, reaparecer notas antigas) e só cobria três classificações; virou `fichar`. Ao comparar `fichar` com a fusão de nota do mesmo assunto que a triagem já fazia por conta própria, ficou claro que eram quase a mesma operação com formatos diferentes (lista de uma linha vs. nota por destino) — o dono pediu para separar em duas skills nomeadas, cada uma com seu critério de quando entra: `fichar` para destino já declarado (nunca para), `fundir` para mesmo assunto achado por busca (sempre para). Branch `fix/colheita-so-na-triagem`.

- **`garimpo` nunca mais chama a `fichar` nem grava fora do Inbox.** Toda nota, de qualquer classificação (inclusive filme, viagem e receita), vira nota no Inbox. A classificação do passo 6 passa a ir também no frontmatter da nota, no campo novo `classificacao`.
- **A skill `colheita` virou `fichar`** (pasta, `name` e descrição), chamada pela `triagem`, nota por nota, quando a nota do Inbox tem uma `classificacao` com destino declarado — não precisa mais ser `filme`, `viagem` ou `receita`, qualquer uma que o `CLAUDE.md` do vault declarar vale. O caminho declarado decide o formato: sem `<destino>`, vira uma linha numa lista compartilhada (como antes); com `<destino>` (o caso de `viagem`), vira uma **seção inteira** numa nota por assunto, achada ou criada pelo título — antes virava só uma linha também, o que jogava fora a pesquisa do garimpo para um destino que, na prática, sempre teve nota própria. Nos dois formatos, a nota do Inbox é apagada no fim. Destino ambíguo ou que não existe: a nota segue o destino normal da triagem, com a dúvida anotada para o fim.
- **Skill nova `fundir`:** extraída do passo "nota com o campo de relacionada" da `triagem`, que antes vivia inline nela. Decide, com o usuário (sempre para, por "perda de sentido" — diferente da `fichar`, que nunca para, porque o destino dela já está declarado), se uma nota do Inbox entra como seção nova numa nota já existente do mesmo assunto, achada por busca pelo `garimpo` (campo `relacionada` no frontmatter). Propõe a dúvida durante a triagem; aplica de fato só depois do sim, num pedido de aplicar respostas.
- **A seção da nota de regras virou `## Listas para fichar`;** o título antigo, `## Listas da colheita`, continua funcionando, para não quebrar vault nenhum. A chave que `B situacao` devolve continua `colheita`, e o status do registro de links continua `colhido`, por compatibilidade com quem já lê esses dois campos (ex.: o Wingman).
- **`gerente`:** a lista de notas apagadas sem parada (seção "Onde parar") ganha a nota do Inbox que a `fichar` acabou de gravar, ao lado do arquivo de atualização do Inbox que já existia.
- **Registro de links:** o status `colhido` só é escrito pela triagem, quando a nota de fato é fichada; o que o garimpo grava para esses links agora é `triado`, como qualquer outro, até a triagem rodar.

**Ao atualizar:** se você já tinha links colhidos direto pelo garimpo (antes desta versão), nada neles muda — essas linhas do registro e esses itens das listas continuam valendo como estão, e a seção `## Listas da colheita` da sua nota de regras não precisa ser renomeada (mas pode, se quiser: `## Listas para fichar` é só o nome novo do mesmo formato). Da próxima triagem em diante, uma nota do Inbox com classificação de destino declarado passa a ser fichada ali, não mais no garimpo — e, se o destino for do tipo `<destino>` (como `viagem`), vira seção inteira em vez de linha, mesmo em listas que já tinham itens só de uma linha de antes (os itens antigos não são reformatados, só os novos). Se você tiver uma rotina (bot, Wingman) que espera `colhidos` no JSON do `B fim` do garimpo, ela deixa de vir — o campo só aparece agora no `B fim` da triagem.

## 0.4.2 — garimpo sem o motor Gemini

Pedido do dono: o motor Gemini do `garimpo` nunca funcionou para ele, sempre voltando com erro de alta demanda do serviço (HTTP 503).

- **`assistir.py` só tem o motor local:** removidas as flags `--engine` e `--pergunta`; o script sempre roda frames + transcrição WhisperX na máquina, nada vai ao Google. O campo `engine` também saiu do `resultado.json`.
- **`SKILL.md` e `references/instalacao.md` do `garimpo`** não citam mais o motor Gemini nem `GEMINI_API_KEY` como caminho padrão.

**Ao atualizar:** quem já usava `--engine local` não muda nada. Quem usava o motor Gemini (padrão antigo) passa a usar sempre o local — mais lento por vídeo, mas sem depender do Google. Se tinha `GEMINI_API_KEY` só para o garimpo, pode remover do `.env`.

## 0.4.1 — levantamento de programas fora do winget

A skill pessoal `liberar-espaco` foi dividida em três (`liberar-espaco`, `programas-sem-uso` e `desinstalar-limpo`), e o levantamento de programas que a `programas` usava saiu dela. Branch `fix/programas-levantamento`.

- **`programas` passa a usar o `auditar-programas.ps1` da skill `programas-sem-uso`** para o que o winget não vê (chaves Uninstall, portáteis e apps da loja). Antes, apontava para um levantamento da `liberar-espaco` que não existe mais. Sem a skill, a alternativa continua a mesma, agora com as pastas de programas portáteis.

**Ao atualizar:** nada muda.

## 0.4.0 — nuvem conectada no preparar

Pedido do dono, depois de usar uma sessão para vasculhar o PC e a nuvem na mão. Branch `feat/nuvem-conectada`.

- **`preparar` aprende a nuvem conectada (seção 2b):** detecta se o vault vive numa pasta de nuvem sincronizada (Google Drive, OneDrive, Dropbox, iCloud) — ou pergunta direto, sem indício —, confirma com o usuário, pergunta o que fica fora da varredura por privacidade, mapeia as pastas de primeiro nível e propõe uma estrutura. Nunca move nada sozinho: é sempre proposta, e qualquer mudança na nuvem pede confirmação à parte, porque o histórico do Butler não cobre fora do vault.
- **Nota de regras com dois campos novos:** `nuvem` em `## Caminhos` (a raiz da nuvem, caminho absoluto do sistema) e a seção `## Nuvem: pastas fora da varredura` (exclusões de privacidade, uma por linha). Os dois ficam disponíveis a qualquer skill via `situacao`.
- **Rodar de novo** oferece a seção 2b para quem ainda não tem `nuvem` na nota, e confirma a raiz de novo numa máquina nova (a letra de unidade pode mudar entre PC e notebook).

**Ao atualizar:** nada muda para quem não tem nuvem conectada ou não quer o recurso — os dois campos são opcionais, e uma nota de regras sem eles continua legível. Para ganhar o mapeamento, rode o `butler:preparar` de novo (ou peça pra rodar): ele vai oferecer a seção 2b.

## 0.3.0 — aviso do garimpo sobre vídeo no preparar

- **`preparar` avisa de cara sobre o `watch@claude-video`:** antes, quem não instalava o plugin e as ferramentas externas (`yt-dlp`, `ffmpeg` etc.) só descobria a exigência ao tentar usar o `garimpo` num vídeo. Agora o `preparar` diz isso já na primeira conferência do vault (e também ao rodar de novo), apontando `garimpo/references/instalacao.md`. O `garimpo` sem vídeo (links de texto) continua funcionando normalmente sem a instalação.

**Ao atualizar:** nada muda no vault. Rode o `butler:preparar` de novo (ou peça pra rodar) só para ver o aviso; sem isso, nada quebra.

## 0.2.1 — correções da segunda revisão do código da 0.2.0

Do `/code-review` da 0.2.0 já na `main`. Branch `fix/achados-review-2`.

- **Mesmo vault de qualquer subpasta:** o `butler.py` e a guarda das escritas acham o vault pela mesma busca (registrado nesta máquina ou, sem registro, a pasta com a nota de regras). Antes, num vault ainda não preparado aqui, um `inicio` rodado de uma subpasta pegava uma trava que a guarda não reconhecia, e a escrita era negada.
- **Guarda conta palavras, não linhas:** juntar frases ou tirar linha em branco deixa de perguntar; espalhar menos texto em mais linhas passa a perguntar. O NotebookEdit numa nota protegida que apaga ou encolhe uma célula também pergunta.
- **Liberação por pasta de nome hexadecimal:** um valor com cara de digital em `## Liberações de dado sensível` vale também como caminho, e a pasta `a1b2c3d4e5f6/` passa a ser liberada.
- **Sugestão de link nunca aponta para o `CLAUDE.md`.**
- **Dúvida repetida no resumo não duplica:** a mesma pergunta sobre a mesma nota, reescrita sem acento ou com outra pontuação, aparece uma vez só.
- **Link recorrente calável:** uma exceção aprendida com o código `link_quebrado_recorrente` tira aquelas notas da contagem.
- A revisão que pede "mostra a árvore do vault" devolve a árvore completa, nota por nota.

**Ao atualizar:** nada muda.

## 0.2.0 — guarda de escrita e revisão da estrutura

Da segunda opinião sobre o plugin, comparado com outros gerentes de vault (hq, o AGENTS de Alexander Weichart, zettelvault, claudesidian, puma-vault). Branch `feat/guarda-e-revisao`.

- **Guarda de escrita (hook `PreToolUse`):** um Write ou Edit num vault do Butler sem o pedido desta sessão é negado, com o caminho para o `butler:gerente`; com o pedido, a escrita que deixa uma nota protegida (Edit) ou uma nota sobrescrita inteira (Write) com menos linhas pergunta ao usuário antes. Trocar uma linha por outra e acrescentar seguem.
- **`fim` confere o que ficou sem ponto:** arquivo mudado desde o último ponto (fora da `.obsidian`) faz o `fim` sair com 6 e a lista em `sem_ponto`, sem soltar a trava; `--sem-ponto-ok` solta mesmo assim, para o que mudou por fora.
- **`duvida`:** cada dúvida de um Lote é anotada na trava na hora em que aparece, volta na retomada depois de uma compactação e entra sozinha nas `perguntas` do `fim`.
- **Revisão da estrutura:** o `revisar` traz a árvore de pastas, a sugestão de nota parecida para cada link quebrado, os alvos inexistentes citados por três ou mais notas, as possíveis duplicatas (mesmo título ou mesmo `source`) e se o vault usa links em Markdown (o `renomear` também avisa). A rotina `revisar` passou a cobrir "mostra a árvore do vault" e "tem nota fora do lugar?", no lugar de uma skill à parte.
- **Binários liberados por pasta:** em `## Liberações de dado sensível`, um caminho ou glob (`` `Anexos/**` ``) no lugar da digital libera os binários daquela pasta; dado sensível num texto continua só pela digital.
- **`consultar`:** a pergunta que o vault não responde pode virar uma pendência "descobrir".

**Ao atualizar:** nada muda no vault, e a nota de regras e o `estado.json` da 0.1.0 continuam legíveis. Uma sessão aberta num vault do Butler passa a ter as escritas pelo Write e pelo Edit negadas fora de um pedido do gerente: se alguma rotina sua escrevia no vault sem passar por ele, ela agora para e mostra o motivo. Se você tinha uma skill `overview` solta (de um rascunho), retire-a: o pedido agora é da rotina `revisar` do gerente.

## 0.1.0 — primeira versão

Do design aprovado pelo dono (`docs/superpowers/specs/2026-11-06-butler-design.md`), etapas 1 a 8 da ordem de construção.

- **`gerente`:** mede o pedido (Consulta, Direto, Lote, Reforma), roda o preâmbulo (trava, mudanças de fora, histórico), para pelo risco e não pela quantidade, confere a nota antes de tocar, grava um ponto por nota, resume sempre no mesmo formato, aprende proteções e exceções com o sim do usuário e desfaz por frase. Rotinas de revisar, registrar, remover e arquivar.
- **`butler.py`:** histórico git fora do vault e de qualquer pasta sincronizada (nenhum arquivo do git no vault), trava de um pedido por vez com retomada pela mesma sessão, pontos só com os arquivos tocados, desfazer por mescla de três vias (mudança posterior em outro trecho fica), voltar uma nota a uma data, renomear com os wikilinks, `estado.json` versionado para o Wingman, conferência do toque, revisão do vault e detecção de dado sensível que nunca devolve o valor.
- **Skills:** `preparar`, `triagem`, `pendencias`, `consultar`, `programas` (com `comparar_winget.py`), `projeto`, `ideia`, `atualizar` e o `garimpo`, que veio de uma skill solta e passou a ler e escrever o registro de links, a classificar cada link e a gravar o resultado no `estado.json`. A `colheita`, chamada só pelo garimpo, grava um link de filme, lugar de viagem ou receita direto na lista que a nota de regras declara em `## Listas da colheita`, sem nota no Inbox.
- **Hooks:** aviso de uma linha no início de cada sessão aberta num vault do Butler e trava solta no fim da sessão.

**Ao atualizar:** primeira versão. Rode o `butler:preparar` no vault. Se houver uma skill `garimpo` solta em `~/.claude/skills/garimpo`, retire-a (o `preparar` propõe), para não haver duas respondendo ao mesmo pedido.
