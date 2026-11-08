---
name: preparar
description: Prepara um vault do Obsidian para o Butler, uma vez por máquina, ou refaz só o que falta. Cria o histórico git fora da pasta sincronizada, a nota Sistema/Regras do Butler.md e a nota de pendências, e propõe as mudanças no CLAUDE.md do vault. Use quando o usuário pedir "prepara este vault", quando o aviso do início da sessão disser que o vault está sem histórico, depois de formatar o PC, numa máquina nova ou quando a skill atualizar pedir uma nova rodada.
---

# Preparar o vault

Roda na pasta do vault. `B` é o comando da skill `butler:gerente` (`sh "${CLAUDE_PLUGIN_ROOT}/hooks/python.sh" "${CLAUDE_PLUGIN_ROOT}/skills/gerente/butler.py"`). Nada aqui altera o `CLAUDE.md` nem outra nota que já existe sem o sim do usuário.

Diga sempre, antes de mais nada (primeira vez ou rodando de novo, seção 4 incluída): o `butler:garimpo` só consegue **assistir vídeo** (Reels do Instagram, YouTube, TikTok) se este PC tiver o plugin `watch@claude-video` e as ferramentas externas dele instaladas (`yt-dlp`, `ffmpeg` etc.) — passo a passo em `plugins/butler/skills/garimpo/references/instalacao.md`, nesta skill. Sem isso, o garimpo ainda funciona normalmente para links de texto (artigo, repositório, PDF); só a parte de vídeo fica indisponível até instalar. É algo por máquina, não por vault: repita o aviso ao preparar noutra máquina. Não instale nada agora — só avise e, se o usuário quiser, aponte o arquivo de instalação.

## 1. Conferir antes de qualquer coisa

1. `B situacao`: se o histórico já está ok, vá para a seção 4 (rodar de novo).
2. Pergunte onde guardar o histórico só se o usuário quiser outro lugar; o padrão é `%LOCALAPPDATA%\Butler\<nome do vault>-<código>` no Windows (`~/.local/share/butler/...` no Linux; o código separa dois vaults com o mesmo nome). Ele precisa ficar fora do vault, de qualquer pasta sincronizada (Google Drive, OneDrive, Dropbox, iCloud) e de pasta temporária ou de cache.
3. `B preparar-historico --so-conferir [--historico <pasta>]` relata, sem criar nada:
   - `pasta_proibida`: a pasta não serve; diga por quê e proponha outra;
   - `copias_conflito`: cópias `Nota (1).md` do sincronizador. Confira com o usuário qual versão vale antes de seguir: a foto inicial guardaria as duas;
   - `fora_do_historico`: arquivos com dado sensível (tipo e linha, nunca o valor) ou binários, que ficariam fora da foto. Mostre e pergunte: dado sensível de verdade sai da nota antes (o usuário decide como); alarme falso vira liberação na nota de regras (seção 2); binário que pode entrar também vira liberação. Esses arquivos ficam fora da foto inicial e entram no histórico no primeiro pedido depois da liberação, como mudança de fora: diga isso.
4. Com tudo respondido, `B preparar-historico [--historico <pasta>]`. Ele cria o histórico, registra o vault na configuração da máquina (`~/.butler/maquina.json`), grava a foto inicial e o primeiro `estado.json`. Diga em uma linha onde o histórico ficou e quantos arquivos entraram (`arquivos_na_foto`).

## 2. A nota de regras

1. Preâmbulo do gerente (`B inicio --rotulo "preparar o vault" --sessao "${CLAUDE_SESSION_ID}"`). Se a nota de regras ainda não existe, ele responde `historico_ok: false` com esse motivo: é o esperado aqui, não ofereça o `preparar` de novo. O `ponto` só grava com a nota de regras no lugar: grave as duas notas no passo 4, com o mesmo token, depois de criá-las.
2. Crie `Sistema/Regras do Butler.md` a partir de `${CLAUDE_PLUGIN_ROOT}/skills/preparar/templates/Regras do Butler.md`. Preencha lendo o `CLAUDE.md` do vault e a estrutura de pastas, nunca de memória:
   - **Notas protegidas:** as que deram trabalho manual para montar e que o `CLAUDE.md` trata como fonte de referência: inventários, históricos (de manutenção, de saúde), perfis. Proponha a lista e confirme com o usuário.
   - **Formato rígido:** as notas cujo formato o `CLAUDE.md` (ou a própria nota) dita: inventários, históricos, registros de links, a nota de pendências.
   - **Caminhos:** a pasta do Inbox, a nota índice, a nota de pendências, a de registro de links (se houver) e o título da seção de links do fim das notas, como o `CLAUDE.md` os chama.
   - **Listas da colheita:** as listas em que o `CLAUDE.md` manda gravar direto um link de vida pessoal (filme, lugar de viagem, receita), se ele tiver essa regra. Lista que ainda não existe fica declarada assim mesmo: a colheita propõe criá-la no primeiro link daquele tipo. Sem a regra no `CLAUDE.md`, pergunte se o usuário quer a colheita; com o não, tire as linhas.
   - **Escritas toleradas do Wingman:** deixe as três do molde se o usuário usa o Wingman; senão, a seção fica com "Nenhuma".
   - **Liberações:** as que saíram da seção 1.
   - O frontmatter e o "Veja também" seguem as regras do `CLAUDE.md` do vault, inclusive os campos que o molde não traz (o de dono da nota, por exemplo): se o valor não for claro, pergunte.
3. Crie a nota de pendências a partir de `${CLAUDE_PLUGIN_ROOT}/skills/preparar/templates/Pendências.md` no caminho que a nota de regras declara, se ela ainda não existir.
4. `B ponto` com as duas notas e `B fim`.

## 3. Mudanças que dependem do usuário

Proponha, uma por uma, com o texto exato, e só grave com o sim (cada uma é uma Reforma pequena, com o preâmbulo e o ponto do gerente):

- **Regra de "mostrar antes"** do `CLAUDE.md` (a que manda mostrar antes de mover ou alterar várias notas): passa a ser "parar pelo risco", valendo só com o Butler e o histórico funcionando; em qualquer outra situação (sessão sem o plugin, outra máquina, histórico quebrado) continua mostrar antes. O texto precisa dizer as duas metades, para uma sessão sem o Butler não ganhar a autonomia sem a rede.
- **"O Inbox fica vazio depois da triagem":** com o Butler, a nota com dúvida e a nota com veredito "não" ficam no Inbox até o usuário responder. Ajuste o texto onde ele aparecer (`CLAUDE.md`, nota índice, guia de uso com IA).
- **Registro de links,** se houver: os status que o garimpo usa e a nota ainda não tem (`colhido`, `falhou`, `carrossel pendente`, além de `triado`), cada um com a explicação de uma linha.
- **Pasta `Sistema`** no `CLAUDE.md` e **nota índice:** citar a nota de regras, a de pendências e o registro de links, se houver.
- **Guia de uso com IA** do vault, se houver: o trecho da triagem passa a seguir a regra nova de "mostrar antes".
- **Memória do Claude:** o que estiver lá como fila ("deixa na fila", "depois a gente faz") vai para a nota de pendências, se ainda valer. A memória só é apagada com o sim.
- **Skill antiga fora do plugin:** se existir uma skill `garimpo` solta em `~/.claude/skills/garimpo`, ela responde ao mesmo pedido que o `butler:garimpo` e grava sem o preâmbulo. Proponha retirá-la (mover para fora da pasta de skills, não apagar) e só faça com o sim.

## 4. Rodar de novo

Rodado num vault já preparado, ou numa máquina nova, confira e ofereça refazer, com o sim, só o que falta:

- **O histórico,** se foi apagado ou se a máquina é outra (o `situacao` diz o motivo). Se o vault só mudou de pasta ou de nome nesta máquina, o histórico antigo serve: o `situacao` lista em `historicos_de_vaults_que_sumiram` os vaults registrados cuja pasta não existe mais. Confirme com o usuário qual é este e rode `B preparar-historico --historico <pasta dele>`, que o reaproveita. Numa máquina nova o histórico começa do zero: o antigo ficou na outra máquina. Diga isso.
- **A nota de regras,** se sumiu: restaure-a do histórico quando ele existir (`B pedidos --nota "Sistema/Regras do Butler.md" --todos` para achar o último ponto em que ela existia, e `B desfazer --token <token> --nota "Sistema/Regras do Butler.md" --ate "<data desse ponto>"`, mostrando a versão antes de `--aplicar --aceitar`), para não perder as proteções e exceções aprendidas. Esses comandos funcionam sem a nota de regras; o `ponto`, não. Só volte ao molde se não houver histórico, e diga isso.
- **A nota de pendências,** se sumiu, pelo mesmo caminho.
- O que a skill `butler:atualizar` disser que uma versão nova pede.
