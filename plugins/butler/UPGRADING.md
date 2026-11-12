# Histórico do plugin `butler`

O que cada versão entregou e o que muda para quem atualiza. O arquivo vai junto com cada versão instalada: a skill `atualizar` lê o **Ao atualizar** de cada versão pulada, da mais antiga para a mais nova. Termine o pedido em andamento no vault antes de atualizar (a skill `atualizar` confere). As ideias que ainda não viraram versão estão no [roadmap](../../docs/roadmap.md). O que é major, minor e patch está no [`CLAUDE.md`](../../CLAUDE.md).

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
