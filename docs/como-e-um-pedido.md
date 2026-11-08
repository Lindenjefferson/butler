# Como é um pedido

O caminho de um pedido do começo ao resumo, para quem chega pelo [README](../README.md) e ainda não leu o [`gerente`](../plugins/butler/skills/gerente/SKILL.md), que é a fonte de cada passo.

## 1. Preparar o vault (uma vez por máquina)

Na pasta do vault, com o plugin instalado, você digita:

> prepara este vault

(ou `/butler:preparar`). O `preparar` cria o histórico git fora do vault (por padrão em `%LOCALAPPDATA%\Butler\<vault>-<código>`), grava a primeira foto do vault, cria `Sistema/Regras do Butler.md` com as notas que ele sugere proteger e a nota de pendências, e propõe as mudanças no `CLAUDE.md` do vault. Nada no `CLAUDE.md` muda sem o seu sim.

Num computador novo, o mesmo pedido cria um histórico novo para aquela máquina: o vault chega pelo sincronizador, o histórico não.

## 2. Abrir uma sessão

Ao abrir o Claude Code na pasta do vault, o hook do início da sessão diz em uma linha que este é um vault do Butler e o que mudou desde a última vez (por exemplo, "Butler: Inbox com 4 notas · 2 pendências · 3 arquivo(s) mudaram por fora · cópia de conflito nova: Casa/Geladeira (1).md · histórico ok"). Fora de um vault do Butler, ele fica calado.

## 3. Pedir

> tria o Inbox

O `gerente` mede o pedido. Uma pergunta ("o que eu sei sobre o carro?") é respondida direto. Uma anotação é feita e dita em uma linha. Triar o Inbox é um **Lote**: várias notas, uma rotina conhecida.

Antes de tocar em qualquer nota, o preâmbulo:

- pega a trava, para que outra sessão (ou o painel) não escreva no vault ao mesmo tempo;
- grava num ponto próprio tudo o que mudou por fora, para que o desfazer nunca leve junto uma edição sua no Obsidian;
- avisa em uma linha se uma nota protegida perdeu dados por fora, se há cópia de conflito, se um arquivo tem cara de dado sensível.

## 4. Nota por nota

Para cada nota do Inbox, a `triagem` confere a nota contra as regras do vault, decide o destino pelo `CLAUDE.md`, move, completa o frontmatter e o "Veja também", atualiza o índice e grava um ponto de retorno só daquela nota.

Se uma nota tem dúvida (de quem é, para que pasta vai, um dado que contradiz outro), ela fica no Inbox e a triagem segue com as outras. Não há pergunta no meio.

## 5. As dúvidas juntas no fim (✋)

> Ficaram 2 dúvidas:
> 1. *Receita de pão.md*: é sua, da Ana ou do casal? Eu poria "casal".
> 2. *Furadeira nova.md*: entra em `Casa/Ferramentas` ou no projeto `Reforma da Varanda`? Eu poria em `Casa/Ferramentas`, que já tem as outras.

Você responde e a triagem aplica. Se você mudar de assunto sem responder, cada dúvida vira uma linha da nota de pendências, e "ficou algo pendente?" a traz de volta.

## 6. O resumo

Todo Lote termina no mesmo formato:

- **O que mudou**, nota por nota: de onde para onde, o que foi completado;
- **O que ficou esperando você**;
- **Como desfazer**: "diga *desfaz a triagem do Inbox*".

## 7. Desfazer, se precisar

> desfaz a última triagem

O `gerente` acha o pedido no histórico e tira só o que ele mudou. Se depois você editou outro trecho de uma das notas, essa edição fica; se editou o mesmo trecho, ele mostra as duas versões e pergunta.

> volta a nota do carro como estava ontem

Mostra a diferença antes e só aplica depois do seu sim.

## 8. Aprender

Se o resumo mostrar algo que você queria ter visto antes, diga isso: o Butler propõe uma linha nova em "Notas protegidas". Se uma pergunta for desnecessária, "isso não precisa perguntar" vira uma exceção. As duas só entram na nota de regras depois do seu sim, e você pode editá-las no Obsidian quando quiser.
