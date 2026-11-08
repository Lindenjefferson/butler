# Butler, primeira versão: plano de construção

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** construir o plugin `butler` do design (etapas 1 a 8 da seção 14), pronto para o GitHub no molde do Foreman, sem aplicar nada ao vault real.

**Architecture:** um script Python sem dependências (`butler.py`, com módulos em `lib/`) faz tudo o que é conferível: histórico git fora do vault, trava, pontos de retorno, desfazer, estado para o Wingman, conferência do toque, detecção de dado sensível e a revisão do vault. As skills, em português, conduzem o que só um modelo faz (medir o pedido, decidir destino, escrever nota) e chamam o script em cada passo que dá para conferir. Um hook de início de sessão dá o aviso de uma linha e diz à sessão que o vault é do Butler.

**Tech Stack:** Python 3 (biblioteca padrão), git 2.x, Claude Code plugins (skills, hooks), Git Bash no Windows.

**Spec:** `docs/superpowers/specs/2026-11-06-butler-design.md`

## Global Constraints

- Português do Brasil nas skills e nas mensagens (design, seção 5). Diferença assumida do Foreman, que tem prompts em inglês.
- Nenhum caminho de vault, nome de pessoa ou regra do vault do dono dentro do plugin (metas 7 e seção 10). A lista inicial de protegidas é escrita pelo `preparar` lendo o `CLAUDE.md` do vault.
- Nenhum arquivo do git dentro do vault: `git --git-dir=<histórico>/git --work-tree=<vault>` em todo comando (seção 6.5).
- Sem remoto e sem push no histórico, nunca. O script recusa trabalhar com remoto configurado.
- O script nunca imprime o valor de um dado sensível; só o tipo, o arquivo, a linha e uma impressão digital.
- Arquivos em UTF-8 e LF; os testes Python rodam sozinhos, sem pytest, e terminam em `ALL PASS`.
- O vault real não é tocado nesta construção: os testes usam vaults sintéticos e uma cópia do vault real na área temporária.
- Merge na `main`, push, criação do repositório no GitHub, instalação do plugin e retirada do `~/.claude/skills/garimpo` só com pedido explícito do dono.

## Decisões de construção (seção 14 do design)

- **Configuração da máquina:** `~/.butler/maquina.json` (ou o caminho em `BUTLER_CONFIG`), `{"versao": 1, "vaults": {"<caminho do vault>": {"historico": "<pasta>"}}}`. O Wingman lê o mesmo arquivo.
- **Pasta do histórico:** padrão `%LOCALAPPDATA%/Butler/<nome do vault>` (no Linux, `~/.local/share/butler/<nome>`). Dentro: `git/`, `estado.json`, `trava.json`. Recusada se ficar dentro do vault, dentro de `OneDrive`/`Google Drive`/`My Drive`/`Dropbox`/`iCloud`, ou numa pasta temporária ou de cache.
- **Git:** `core.autocrlf=false`, `core.safecrlf=false`, `core.quotepath=false`, `core.longpaths=true`, `core.precomposeunicode=true`, identidade própria (`Butler`, `butler@localhost`), `core.hooksPath` apontando para uma pasta vazia dentro do histórico, `info/exclude` com `.obsidian/workspace*.json`, `.tmp.drivedownload/`, `.tmp.driveupload/`, `.trash/`, `desktop.ini`, `~$*`, `*.tmp`.
- **Pontos de retorno:** mensagem `[<tipo>] <rótulo>` com os trailers `Butler-Pedido: <id>` e `Butler-Tipo: fora|nota|fim|desfaz|preparar`.
- **Trava:** `trava.json` com `pedido`, `token`, `rotulo`, `inicio`, `atualizado`. Não expira sozinha: com mais de 2 h sem atualizar, o script a marca como `provavelmente_caiu` e a skill mostra ao dono antes de liberar (`liberar-trava --forcar`).
- **Gatilho do gerente:** a descrição da skill e a linha do hook de início de sessão, que diz que pedidos que alteram o vault passam pelo `butler:gerente` e consultas não.
- **Formato de `Sistema/Regras do Butler.md`:** seções com títulos fixos (`## Notas protegidas`, `## Formato rígido`, `## Escritas toleradas do Wingman`, `## Exceções aprendidas`, `## Liberações de dado sensível`); cada item é uma linha `- \`<caminho ou glob>\` — <explicação>`; liberações são `- \`<impressão digital>\` — <arquivo e motivo>`.
- **Dado sensível:** CPF formatado com dígito válido, ou 11 dígitos com a palavra CPF na linha; cartão em grupos de 4 com Luhn válido, ou 13 a 19 dígitos com Luhn válido e palavra de cartão na linha; `senha`/`password`/`pin` seguido de `:` ou `=` e um valor; RG com a sigla e número. Números de série, MAC, placa e valores em reais não casam.

## Review Focus

1. **Nome de arquivo com acento e espaço** (`Carro/Histórico de Manutenção do Sedã.md`): status, add, commit e restauração preservam o nome exato. Teste em `test_historico.py`.
2. **Sessão que caiu com a trava presa:** o segundo `inicio` não força, devolve a trava com a idade e `provavelmente_caiu`. Teste em `test_trava.py`.
3. **Desfazer com mudança posterior:** a nota mudou depois do pedido; o desfazer não sobrescreve sem `--aceitar`. Teste em `test_desfazer.py`.
4. **Dado sensível numa mudança de fora:** o arquivo fica fora do ponto, o resto entra, o valor nunca aparece na saída. Teste em `test_sensivel.py` e `test_historico.py`.
5. **`Início.md` com BOM:** a conferência lê o frontmatter depois do BOM sem acusar. Teste em `test_conferencia.py`.

---

## Arquivos

```
.claude-plugin/marketplace.json
.claude/settings.json
.gitattributes  .gitignore  LICENSE  README.md  CLAUDE.md  CONTRIBUTING.md
.github/workflows/testes.yml
docs/roadmap.md
docs/primeira-preparacao.md                  textos propostos ao vault do dono (seção 11; saiu do repositório antes de ele ficar público)
plugins/butler/.claude-plugin/plugin.json
plugins/butler/UPGRADING.md
plugins/butler/hooks/hooks.json  python.sh  session-start.py
plugins/butler/hooks/tests/test_session_start.py  test_plugin_integrity.py
plugins/butler/skills/gerente/SKILL.md
plugins/butler/skills/gerente/butler.py      CLI (subcomandos abaixo)
plugins/butler/skills/gerente/lib/           config.py historico.py trava.py estado.py regras.py sensivel.py conferencia.py revisao.py notas.py
plugins/butler/skills/gerente/references/    rotinas: revisar.md registrar.md remover.md arquivar.md; desfazer.md
plugins/butler/skills/gerente/tests/         test_*.py + apoio.py (vault sintético)
plugins/butler/skills/preparar/SKILL.md  templates/Regras do Butler.md  templates/Pendências.md
plugins/butler/skills/{triagem,programas,pendencias,projeto,ideia,consultar,atualizar}/SKILL.md
plugins/butler/skills/garimpo/               migrado de ~/.claude/skills/garimpo
```

## Interface do `butler.py`

Todo subcomando aceita `--vault <pasta>` (padrão: a pasta atual, subindo até achar um vault configurado) e imprime um JSON em UTF-8. Código de saída: 0 ok; 2 erro de uso; 3 trava ocupada; 4 sem histórico (o JSON diz o motivo).

| Subcomando | Faz |
|---|---|
| `preparar-historico [--historico DIR]` | Confere a pasta, cria o git, a configuração da máquina e a foto inicial; grava o primeiro `estado.json`. Idempotente: com histórico pronto, só confere. |
| `situacao` | Só lê: histórico ok ou motivo, trava, mudanças de fora pendentes, Inbox, pendências. Usado pelo `consultar`, pelo hook e pela skill. |
| `inicio --rotulo R` | Pega a trava, grava o ponto das mudanças de fora (sem os arquivos com dado sensível), devolve `token`, `pedido`, `historico_ok`, `mudancas_de_fora` (`arquivos`, `protegidas_com_remocao`, `copias_conflito`, `regras_mudaram`, `sensiveis`). Sem histórico: devolve `historico_ok: false` e o motivo, mas ainda pega a trava. |
| `ponto --token T --rotulo R ARQ...` | Grava só os arquivos listados (inclusive apagados e movidos: origem e destino). Recusa arquivo com dado sensível. |
| `fim --token T [--resumo ARQ.json]` | Grava o resumo no `estado.json` e solta a trava. |
| `aviso` | O do início da sessão: com a trava livre, grava as mudanças de fora com rótulo "início da sessão"; devolve a linha de aviso. |
| `liberar-trava --forcar` | Solta uma trava presa, depois do sim do dono. |
| `pedidos [--nota ARQ] [--limite N]` | Lista os pedidos gravados, do mais novo ao mais velho. |
| `desfazer --token T (--pedido ID | --nota ARQ --ate DATA) [--aplicar] [--aceitar ARQ...]` | Sem `--aplicar`, mostra o plano: cada arquivo, a ação e se há conflito (mudou depois). Com `--aplicar`, restaura o que não tem conflito e o aceito, num ponto novo. |
| `conferir ARQ...` | A conferência do toque, nota por nota: frontmatter, título igual ao nome, "Veja também" com links que existem, dado sensível, protegida, formato rígido. Os campos e valores do frontmatter ficam com a skill, que lê o `CLAUDE.md`. |
| `sensivel ARQ...` | Só a detecção. |
| `revisar` | A rotina de revisar: a conferência no vault inteiro, mais pastas vazias, cópias de conflito e notas fora do `Início.md`. |

## Tarefas

### Tarefa 1: esqueleto do repositório e do plugin
Arquivos de raiz, manifesto (`version` 0.1.0), marketplace `butler-local` com o plugin `butler`, `python.sh`, `test_plugin_integrity.py` (manifesto válido, toda skill tem `name` e `description`, todo `${CLAUDE_PLUGIN_ROOT}/...` citado existe, nenhum caminho absoluto de usuário nem e-mail dentro de `plugins/`). Pre-commit de segredos do Foreman instalado no clone. Critério: `claude plugin validate plugins/butler` e `.` passam; `test_plugin_integrity.py` ALL PASS.

### Tarefa 2: configuração, histórico e pontos de retorno (`config.py`, `historico.py`)
Teste primeiro: vault sintético com nomes acentuados; `preparar-historico` cria o git fora do vault e nenhum arquivo dentro; pasta proibida é recusada; `ponto` grava só os listados; mudança de fora vira ponto próprio; remoto configurado derruba o `historico_ok`; CRLF e acentos voltam idênticos.

### Tarefa 3: trava e estado (`trava.py`, `estado.py`)
Teste primeiro: trava ocupada devolve 3 com a trava; token errado recusado; trava velha marcada `provavelmente_caiu`; `estado.json` gravado em todo comando, sem conteúdo de nota; `fim` solta a trava e grava o resumo.

### Tarefa 4: regras e dado sensível (`regras.py`, `sensivel.py`)
Teste primeiro: parse das seções; globs; `CLAUDE.md` e as regras sempre protegidos; casos verdadeiros e falsos de CPF, cartão, senha, RG; número de série, MAC, placa e valor em reais não casam; liberação pela impressão digital; valor nunca na saída. Medir alarmes falsos na cópia do vault real (meta: zero).

### Tarefa 5: `inicio`, `aviso`, `situacao` e o hook
Teste primeiro: protegida com linha removida aparece em `protegidas_com_remocao`; só acréscimo não aparece; cópia `nota (1).md` nova aparece; mudança no `CLAUDE.md` aparece; arquivo sensível fica fora e o resto entra. Hook: fora de vault configurado não imprime nada; dentro, uma linha e o contexto do gerente.

### Tarefa 6: desfazer e pedidos
Teste primeiro: desfazer um pedido restaura as notas, recria a apagada e apaga a criada; conflito com mudança posterior não aplica sem `--aceitar`; `--nota --ate` volta a versão daquela data; o desfazer é um ponto novo.

### Tarefa 7: conferência e revisão (`conferencia.py`, `revisao.py`)
Teste primeiro: BOM; título diferente do nome; "Veja também" ausente; link quebrado (com `|alias` e `#seção`); pastas vazias exceto `Inbox`; cópia de conflito; nota fora do `Início.md`. Rodar na cópia do vault real e conferir cada achado à mão.

### Tarefa 8: skill `gerente` e as rotinas
SKILL.md: tamanhos, paradas, preâmbulo, conferência, resumo, desfazer, pendência de pergunta; `references/` com revisar, registrar, remover, arquivar e desfazer. Critério: um subagente lê só a skill e responde certo a 12 cenários da seção 8 do design.

### Tarefa 9: `preparar` e os modelos
SKILL.md e os moldes de `Regras do Butler.md` e `Pendências.md` sem nada do vault do dono. `docs/primeira-preparacao.md` com os textos propostos da seção 11 (saiu do repositório antes de ele ficar público, por ter dados do vault do dono). Critério: ensaio na cópia do vault, do zero e rodando de novo.

### Tarefa 10: `triagem`
Critério: ensaio numa cópia com o Inbox preparado com os casos da seção 7.1 (atualização que só acrescenta, atualização que remove, `relacionada`, veredito "não", sem frontmatter, destino que não existe, nome repetido).

### Tarefa 11: `pendencias`, `consultar`
Critério: cenários por subagente; `consultar` não chama `inicio`.

### Tarefa 12: `garimpo` no plugin
Cópia adaptada: vault da sessão, preâmbulo, registro de links lido pelo `ja_no_vault.py` (teste primeiro), classificação no OK do lote e no resumo. A pasta antiga fica até a instalação.

### Tarefa 13: `programas`, `projeto`, `ideia`, `atualizar`
SKILL.md de cada uma, conforme as seções 7.2, 7.6, 7.7 e a do Foreman.

### Tarefa 14: documentação, CI e revisão final
README, CLAUDE.md (mapa), CONTRIBUTING, UPGRADING 0.1.0, roadmap, CI. Revisão independente da branch inteira e dos casos difíceis; correção numa rodada; relatório para o dono.
