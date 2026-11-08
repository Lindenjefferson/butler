# Desfazer

Vale só com o histórico funcionando. Sem ele, diga que não há ponto de retorno e lembre do histórico de versões do sincronizador (o Google Drive guarda versões por um tempo).

## Achar o que desfazer

- `B pedidos` lista os pedidos do mais novo ao mais velho, com rótulo, data, número de pontos e arquivos. `--nota "<nota>"` filtra pelos que tocaram aquela nota. `--todos` inclui os pontos das mudanças de fora.
- "A última triagem", "o último garimpo": o pedido mais novo com aquele rótulo. Se houver dúvida entre dois, mostre os dois e pergunte.
- `B mostrar --pedido <id>` devolve o diff do pedido, para mostrar o que vai voltar.
- O pedido citado não aparece na lista: diga isso e mostre os mais recentes. Ele pode ser de antes do histórico, de outra máquina ou feito sem o Butler; nesses casos, lembre do histórico de versões do sincronizador.

## Desfazer um pedido

1. Preâmbulo do gerente (`inicio`) com o rótulo "desfaz <rótulo do pedido>" (o `rotulo` que o `pedidos` mostra, não o id).
2. `B desfazer --token <token> --pedido <id>` devolve o plano, sem mexer em nada: cada arquivo, a ação (`restaurar`, `recriar`, `apagar` ou `nada`) e se há `conflito`.
3. Mostre o plano em linguagem de gente: "volta a nota X para o Inbox, apaga a nota Y que a triagem criou, tira a linha Z do índice". Espere o sim.
4. `B desfazer --token <token> --pedido <id> --aplicar`. A restauração vira um ponto novo; o histórico não perde nada.

O desfazer tira só o que o pedido mudou. Uma mudança posterior em outro trecho da mesma nota (outra triagem que mexeu no índice, por exemplo) fica.

## Conflito

Conflito é um trecho que o pedido mudou e que mudou de novo depois, por outro pedido ou por fora; uma nota que o pedido criou e que alguém editou depois; ou uma nota apagada cujo nome já está ocupado. O `--aplicar` pula esses arquivos (`pulados_por_conflito`). Para cada um:

1. Mostre as duas versões: a de agora (o arquivo) e a que o desfazer deixaria (`B desfazer --token <token> --pedido <id> --conteudo "<arquivo>"`, no campo `conteudo` do plano; `null` quando o desfazer apagaria o arquivo; num item `nada`, o próprio arquivo de agora).
2. Pergunte. Nunca sobrescreva a mudança posterior sem o sim.
3. Com o sim, `B desfazer --token <token> --pedido <id> --aplicar --aceitar "<arquivo>"` restaura aquele arquivo inteiro como estava antes do pedido.

`nome_ocupado` é diferente de conflito: o nome que o desfazer quer usar já é de outro arquivo, com outra grafia de maiúsculas (`Nota.md` e `nota.md` são o mesmo nome no Windows). Aceitar não resolve. Diga qual arquivo ocupa o nome e pergunte o que fazer com ele (renomear ou unir); depois de resolvido, rode o desfazer de novo.

## Voltar uma nota a uma data

"Volta a nota X como estava ontem":

1. `B desfazer --token <token> --nota "<nota>" --ate "<AAAA-MM-DD HH:MM>"` (um dia sem hora, como "ontem", é o fim daquele dia: `23:59`) devolve o ponto escolhido e os `mudancas_posteriores`, os pedidos e mudanças de fora que mexeram na nota depois dele.
2. Mostre as duas versões e o que se perderia de cada mudança posterior. Espere o sim.
3. `--aplicar --aceitar "<nota>"`.

Antes do primeiro ponto do histórico não há para onde voltar: diga isso e lembre do histórico de versões do sincronizador.

## Resumo

O resumo do desfazer segue o formato do gerente: o que voltou, o que ficou por conflito e como desfazer o desfazer (é um pedido como outro qualquer). No JSON do `fim`, cada arquivo restaurado é `alterada`, cada recriado é `criada` e cada apagado é `apagada`; os pulados por conflito vão em `perguntas`.
