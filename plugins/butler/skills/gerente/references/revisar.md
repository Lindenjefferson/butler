# Revisar

A saúde e a estrutura do vault, a pedido ("revisa se tá tudo ok", "vê se ficou algo quebrado", "mostra a árvore do vault", "tem nota fora do lugar?"). É a única situação em que o Butler olha o vault inteiro, e só porque o usuário pediu.

**Só lê e relata.** Não pega a trava e não grava ponto: corrigir é outro pedido.

1. `B revisar` devolve:
   - `arvore`: cada pasta (a raiz é `""`) com as notas que ficam direto nela, inclusive as vazias;
   - `notas`: cada nota com achados (`link_quebrado`, `sem_veja_tambem`, `sem_frontmatter`, `frontmatter_invalido`, `titulo_diferente`, `dado_sensivel`, `copia_conflito`, `nome_nfd`), já sem os que uma exceção aprendida cala. Um `link_quebrado` com `sugestao` tem uma nota de nome muito parecido: é um palpite, não uma correção;
   - `pastas_vazias` (menos o Inbox), `copias_conflito`, `nomes_nfd`;
   - `fora_do_indice`: notas que a nota índice não cita (só quando `## Caminhos` das regras diz qual é o índice);
   - `links_quebrados_recorrentes`: um alvo inexistente que três ou mais notas citam, candidato a ganhar nota própria;
   - `possiveis_duplicatas`: notas com o mesmo título em pastas diferentes, ou com o mesmo link em `source`;
   - `links_markdown`: `true` quando o Obsidian do vault cria links em Markdown, que a conferência e o `renomear` não leem. Diga isso: link quebrado e renomeação desses links ficam por conta do Obsidian.
2. Complete o que o script não confere:
   - o frontmatter de cada nota contra a regra do `CLAUDE.md` (campos obrigatórios, valores válidos, número de tags);
   - o formato de cada nota de formato rígido contra a regra dela;
   - formatação quebrada (tabela desalinhada, lista cortada, cabeçalho repetido) nas notas que o relatório já apontou e nas rígidas;
   - notas de projeto defasadas: para cada nota de projeto com link de repositório, compare a versão citada com a do repositório, como a skill `butler:projeto` faz;
   - se o índice está em sincronia com as pastas, como o `CLAUDE.md` pede;
   - **pastas fora do previsto:** as pastas de primeiro nível da `arvore` que o `CLAUDE.md` não declara;
   - **notas que parecem estar na pasta errada:** o `type` do frontmatter contra a pasta, quando o `CLAUDE.md` reserva uma pasta para um tipo; nota no Inbox com cara de já triada (frontmatter completo, "Veja também" preenchido), sobretudo se antiga; nota de um assunto que claramente pertence a uma área ou projeto, mas está solta em outro lugar. Diga por que estranhou.
   - **possíveis duplicatas:** leia as duas notas e diga se parecem o mesmo assunto ou só têm o mesmo nome.
3. Relate. **Pedido foi a árvore** ("mostra a árvore do vault" e parecidos): dê a árvore completa, nota por nota, num bloco de código estilo `tree` (pastas com `/`, notas em ordem alfabética dentro de cada pasta). **Pedido foi a saúde ou a estrutura** ("revisa se tá tudo ok", "tem nota fora do lugar?"): comece pela árvore resumida por pasta, com a contagem de notas (nota por nota só se o usuário pedir o detalhe depois). Em qualquer um dos dois casos, continue com os achados agrupados por tipo, com o link de cada nota, e por fim os casos de pasta errada, cada um com a pasta atual e a que pareceria mais natural. Para cada grupo, diga se a correção seguiria direto (completar frontmatter, acrescentar "Veja também", trocar um link quebrado pela `sugestao` que o usuário confirmar) ou pararia (apagar, unir, criar nota fora do Inbox para um link recorrente, mover uma nota que não está no Inbox, trocar dado de nota protegida), pelas paradas do gerente. Vault sem nada desconforme: diga isso.
4. Dado sensível: diga a nota, o tipo e a linha, nunca o valor. Se ele já está no histórico, diga isso. O plugin ainda não refaz o histórico sem um conteúdo; o caminho de hoje, só com o sim e depois de tirar o dado da nota, é apagar a pasta do histórico e rodar o `butler:preparar` de novo, o que começa um histórico novo e perde os pontos de retorno anteriores. Diga as duas coisas antes.
5. Pergunte quais correções fazer. Cada uma vira um pedido com o preâmbulo e as paradas do gerente.
