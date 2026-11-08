# Roadmap do plugin `butler`

As ideias para o plugin, de onde quer que venham (uso real num vault, revisão do próprio plugin, pedido do dono ou ideia adaptada de outro projeto). O que cada versão entregou está no [histórico](../plugins/butler/UPGRADING.md): ao entregar um item, ele sai daqui e vai para a seção da versão, com o PR.

Toda ideia passa pelo filtro do [`CLAUDE.md`](../CLAUDE.md) e termina numa destas seções: **Não triadas** até passar por ele; **Backlog** quando entra, dizendo antes de tudo se é **defeito** (o plugin não faz o que o arquivo dele diz) ou **melhoria**, porque defeito conferido não espera na fila; **Em espera** com o sinal que a traz de volta; ou **Recusado**, com o motivo em uma linha. Cada item diz de onde veio e o esforço estimado (P, M, G).

## Não triadas

Nenhuma no momento.

## Backlog

- **Melhoria — salvos do Instagram** (a skill `garimpo` antes do plugin): ler a exportação dos salvos e garimpar o que ainda não está no registro de links. As decisões já tomadas estão em [`salvos-do-instagram.md`](salvos-do-instagram.md). Ficou de fora da 0.1.0 porque falta uma decisão do dono: como ler os posts sem vídeo (carrosséis). Esforço: M.

## Em espera (voltam com um sinal)

- **Impressão digital com chave** (revisão do código da primeira versão): a `digital` é o SHA-256 sem chave de `<tipo>:<valor>`, e um valor curto (um PIN, um CPF) sai dela por tentativa. Ela aparece na conversa, no `estado.json` (local) e, numa liberação, na nota de regras. Quem vê a digital já tem acesso ao vault, onde o valor está (o dado sensível fica fora do histórico, não fora da nota), e numa liberação o valor é um alarme falso. Uma chave por máquina faria a liberação valer só naquela máquina. Volta se a digital passar a ir para fora da máquina (um painel na rede, um relatório compartilhado). Esforço: P.
- **`fora_do_indice` com notas ligadas por outra nota** (ensaio numa cópia do vault do autor): a revisão aponta notas que o índice alcança por uma nota intermediária (um roteiro ligado pelo roadmap de um projeto). Volta se o ruído fizer a revisão ser ignorada. Esforço: P.

- **Expurgar um dado sensível do histórico** (revisão do plano da primeira versão): refazer o histórico sem um arquivo que entrou nele com um dado sensível. Hoje o dado sensível achado não entra no histórico; um que passou antes de virar padrão conhecido fica nele, e a rotina `revisar` só avisa. Mexe em reescrever o histórico, que é o que garante o desfazer. Volta no primeiro caso real de dado sensível dentro do histórico. Esforço: M.
- **Caminhos longos no Windows** (revisão do plano da primeira versão): o prefixo `\\?\` para notas com caminho acima de 260 caracteres. Volta quando um vault real tiver uma nota assim. Esforço: P.
- **Registro de links para outras origens** (design da primeira versão): o registro hoje guarda os links que o garimpo processou; links colados à mão numa nota não entram. Volta quando um link repetido escapar da checagem "já está no vault". Esforço: P.
- **Prompt para o ChatGPT e o Claude mobile** (design da primeira versão): um texto pronto para a outra IA escrever o arquivo de atualização no formato que a triagem aplica. Volta quando um arquivo de atualização vier no formato errado. Esforço: P.
- **macOS** (README): nada foi testado no macOS; os caminhos do histórico padrão caem em `~/.local/share/butler`. Volta com o primeiro uso num Mac. Esforço: P.
- **Nota índice gerada** (segunda opinião, comparação com o AGENTS e o hq): o modelo mantém o índice à mão a cada triagem, o que gera os `fora_do_indice`. Gerar a lista pelo script, ou propor no `preparar` uma Base do Obsidian no lugar dela, tira essa escrita do modelo; mas o formato do índice é de cada vault, e trocá-lo é decisão do dono. Volta se o índice desandar num vault real (notas triadas que não entraram nele). Esforço: M.
- **Resumo da revisão no aviso do início da sessão** (segunda opinião, o reconcile semanal do AGENTS): a linha do aviso diria quantos achados novos há desde a última revisão. Custa tempo no início de toda sessão, e o aviso já precisou ficar mais rápido. Volta se a revisão passar semanas sem ser pedida e um problema crescer por isso. Esforço: P.
- **Guarda também no Bash** (versão 0.2.0): a guarda de escrita confere o Write e o Edit; um `mv`, `rm` ou `>` pelo Bash dentro do vault não passa por ela. Conferir comando de shell é adivinhação. Volta se uma escrita pelo Bash escapar da trava num vault real. Esforço: M.
- **Enxugar a skill do gerente** (segunda opinião): toda skill manda ler a `SKILL.md` do gerente inteira; "Aprender com o uso" poderia ir para `references/`, como o desfazer. Volta se o custo de contexto por pedido aparecer como problema. Esforço: P.
- **Achados da revisão como checagens uniformes** (segunda revisão do código da 0.2.0): o `revisar` monta cada achado do vault inteiro à mão numa função só; uma lista de checagens com o mesmo formato e o mesmo jeito de calar organizaria melhor. Hoje todo achado novo já é calável. Volta quando entrar o próximo achado da revisão. Esforço: P.

## Recusado

- **Vários agentes por persona com um despachante** (o hq): o "medir o pedido" do gerente já faz o mesmo roteamento em níveis, sem o custo de vários agentes.
- **Unir ou promover notas sozinho depois de um prazo** (o consolidate e o crystallize do AGENTS): contraria "parar pelo risco"; unir é sempre a parada 2.
- **Log de ações dentro do vault** (o `log.md` do AGENTS): deixaria marca de alteração no vault; o histórico fora dele já é esse registro, e o `pedidos` o lê.
- **Decompor notas em notas atômicas, Johnny Decimal, prefixos de tipo no nome** (zettelvault, puma-vault): são métodos de organização; as regras moram no vault, e o Butler não impõe método.
- **Guarda liberar as escritas toleradas do Wingman** (segunda revisão do código da 0.2.0): o Wingman grava as três escritas toleradas pelo próprio app, esperando a trava sair; elas não passam pelas ferramentas do Claude, então a guarda nunca as vê. Liberá-las na guarda abriria a escrita sem pedido para uma sessão do Claude.
