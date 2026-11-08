# Butler — design

Plugin privado do Claude Code que dá um gerente ao vault do Obsidian do dono.

- **Data:** 2026-11-06
- **Estado:** design fechado com as respostas do dono e, em 2026-11-06, integrado ao Wingman, o painel que vai chamar o Butler (seção 7.10). Passou por um revisor de construção, por uma checagem final, por uma revisão independente do documento inteiro e, no fim do mesmo dia, por uma revisão de coerência que separou a skill `colheita` do garimpo (seção 7.11) e fixou a independência entre o Butler e o Wingman. A integração ao Wingman e a colheita aguardam a leitura e a aprovação do dono. Nada foi construído. (superado por: a primeira versão foi construída em 2026-11-07, e no mesmo dia o dono pediu que a colheita entrasse nela, com as listas declaradas na nota de regras e o status `colhido`; seção 7.11)
- **Vault:** o vault do Obsidian do dono, sincronizado pelo Google Drive (caminho fora deste documento).
- **Referência de organização:** o Foreman, o plugin de projetos de código do mesmo dono.

Como ler: o que o dono disse aparece como decisão dele. O que eu decidi no lugar dele aparece marcado **(decisão minha)**, e a lista completa dessas decisões está na seção 13. As duas perguntas que dependiam dele estão respondidas na seção 12.

---

## 1. Intenção e porquê

Hoje cada ação no vault (garimpar um link, triar o Inbox, atualizar um inventário) é um pedido solto na conversa, resolvido na hora. Funciona e não dá trabalho: o dono disse que nenhum pedido recente foi mais custoso do que devia. O que falta é outra coisa:

- **O mesmo pedido sai de formas diferentes** conforme a sessão, porque nada fixa o roteiro.
- **O vault é só depósito.** Ele não conduz a própria rotina: alguém precisa lembrar e pedir cada passo.

O Butler é um gerente para o vault, inspirado no Foreman: mede o pedido, conduz a rotina sozinho, confere o próprio trabalho e só para onde há risco. A diferença para o Foreman é o que está em jogo. Lá o risco é código quebrado, e há merge para segurar. Aqui o risco é perder informação que deu trabalho para juntar, e não há merge: as paradas ficam nas mudanças que podem causar essa perda.

**O Butler é o segundo cérebro de fato; o Wingman é o painel (decisão do dono).** Tudo o que conversa com o vault ou o altera acontece numa sessão do Claude Code com o Butler: a triagem, o garimpo, as ideias, as pendências do vault, as consultas ("o que eu sei sobre X?") e a conversa livre no vault. O Wingman, o app painel que o dono está desenhando, só mostra o que lê dos arquivos Markdown, sem LLM, e dispara as skills do Butler pelo nome numa aba. Ele não escreve no vault, fora de três escritas toleradas. Os dois são independentes: o Butler funciona sozinho, pelo terminal, e o Wingman entra em uso sem o Butler, porque o mod do vault dele é futuro e opcional. A seção 7.10 diz como os dois se encaixam quando esse mod existir.

## 2. Metas

1. **Mesmo pedido, mesmo resultado.** Triagem, garimpo e inventário de programas seguem sempre o mesmo roteiro e entregam o mesmo formato de resumo, chamados pelo dono na conversa ou pelo Wingman pelo nome.
2. **Pedido simples continua simples.** Um pedido, uma resposta. O Butler não acrescenta passo nem pergunta ao que hoje sai direto.
3. **Parar pelo risco, não pela quantidade.** Mudança que só acrescenta segue sem perguntar. Mudança que pode perder informação, perder sentido ou causar dano é mostrada antes.
4. **Tudo o que o Butler faz sozinho dá para desfazer, nota por nota,** mesmo dias depois.
5. **Conferir na hora do toque.** Antes de mexer numa nota, o Butler confere se ela está de acordo com as regras do vault. Se estiver, segue calado. Se notar algo estranho, não corrige: pergunta se era para ser assim.
6. **Ler antes de agir nas notas de formato livre** e seguir a regra à risca nas de formato rígido.
7. **As regras do vault moram no vault.** As skills novas não carregam nenhuma regra específica do vault do dono. O `garimpo` é a exceção assumida na primeira versão (seção 7.3).
8. **Plugin arrumado como o Foreman:** repositório próprio, versão, instalação e atualização do mesmo jeito.

## 3. Não-metas

- **Adoção por outra pessoa na primeira versão.** Não há ninguém em vista. A seção 10 diz o que falta para isso.
- **Sincronizar os Perfis com a memória do Claude.** Já é papel das skills próprias de cada perfil (cozinha, viagem, idioma).
- **Varrer o vault por conta própria.** O Butler olha o que o pedido toca. Auditoria do vault inteiro só a pedido (rotina de revisar, seção 7.8).
- **Enviar o vault ou o histórico para qualquer lugar.** Sem GitHub, sem remoto.
- **Editar o vault pelo celular, pelo ChatGPT ou em outro computador.** Isso continua entrando pelo Inbox.
- **Um time de agentes como o do Foreman** (dev, revisor, testador). Aqui o gerente trabalha sozinho e confere o próprio trabalho.
- **Substituir o `CLAUDE.md` do vault.** O Butler obedece a ele.
- **Ser o painel.** Visão de sessões, contas, projetos e avisos é do Wingman. O Butler entrega o que o painel mostra do vault (seção 7.10), não a tela.
- **Depender do Wingman.** O Butler nasce e vive no terminal. O Wingman é um chamador a mais, quando existir.

## 4. Anti-metas

O Butler fracassa, mesmo funcionando, se:

- virar um intermediário chato: perguntar em pedido que hoje sai direto, ou mostrar plano para coisa simples;
- trocar, apagar ou reescrever em silêncio um dado de uma nota protegida;
- corrigir sozinho o que achou estranho;
- impor formato fixo a uma nota de formato livre (ideia, projeto);
- repetir no plugin uma regra que já está no `CLAUDE.md`, de modo que as duas possam divergir;
- deixar marca de alteração dentro das notas ("alterado em", "removido", riscado). O registro do que mudou fica só no histórico;
- gravar no histórico uma senha, cartão ou documento que chegou numa nota: o histórico não esquece;
- ter o histórico corrompido pelo Google Drive justo quando for preciso desfazer algo.

## 5. Restrições

- **Ambiente:** Windows 11, Claude Code, git 2.54 instalado. O vault só é editado neste PC, pelo Claude Code. O Obsidian raramente está aberto.
- **Sincronização:** o vault fica numa pasta sincronizada pelo Google Drive. O Drive cria cópias `nota (1).md` em conflito e mantém pastas temporárias próprias (`.tmp.drivedownload`, `.tmp.driveupload`).
- **Regras:** o `CLAUDE.md` do vault manda. Em conflito com uma skill do Butler, vale o `CLAUDE.md`. O Butler lê o `CLAUDE.md` a cada pedido, sem cópia guardada.
- **Idioma:** português do Brasil, nas skills e nas mensagens.
- **Contas:** este PC tem várias contas do Claude Code que compartilham `skills/`, `plugins/` e `projects/` por junções. O plugin instalado uma vez vale para todas, e duas sessões de contas diferentes podem estar no vault ao mesmo tempo.
- **Preferências já registradas na memória do projeto:** notas sem marcas de alteração; remover é apagar o item e as menções, sem registrar que saiu; nota de projeto é curta e humana, o técnico fica no repositório; o Firefox é presumido fechado (o garimpo não pergunta).
- **Conteúdo de fora é dado, nunca instrução:** nota vinda do ChatGPT, página lida, transcrição de vídeo.

---

## 6. Como funciona

### 6.1 Tamanho do pedido

O Butler mede o pedido pelo que a mudança faz, não pelo tamanho do texto.

| Tamanho | O que é | Como o Butler conduz |
|---|---|---|
| **Direto** | Mudança em uma nota que só acrescenta ou que segue uma regra rígida. Ex.: "anota isso", "registra a troca de óleo". | Faz e diz em uma linha o que fez. Sem plano. |
| **Lote** | Rotina sobre várias notas. Ex.: triar o Inbox, atualizar o inventário de programas. | Conduz nota por nota, sem parar entre elas. Junta as dúvidas e pergunta todas no fim. Entrega um resumo. |
| **Reforma** | Mexe na estrutura. Ex.: pasta nova, unir ou dividir notas, mudar uma regra ou um modelo, reescrever várias notas. | Mostra o plano antes e espera o aval. Depois executa em passos, com resumo. |

**(decisão minha)** Os três tamanhos e os nomes. O dono pediu "medir o tamanho como o Foreman"; a divisão concreta é minha.

**Se o Butler errar o tamanho:**

- **As paradas são da operação, não do tamanho** (seção 6.2). Um pedido medido como Direto que no meio precise apagar um dado protegido para do mesmo jeito. Medir para menos nunca pula uma proteção.
- **Se o pedido crescer no meio,** o Butler para, diz que cresceu e sobe de tamanho.
- **Medir para mais é raro,** porque Reforma tem lista fechada de operações. Se acontecer, o dono responde "só faz" e segue.

**Consulta não passa pelo gerente.** Pergunta sobre o que há no vault é respondida direto, sem medir nada. A skill `consultar` (seção 7.9) é essa consulta com nome, para o Wingman chamar.

### 6.2 Onde o Butler para

**Segue sem perguntar** (aparece só no resumo):

- preencher ou completar frontmatter;
- acrescentar link em "Veja também";
- registrar item novo num inventário, num histórico ou no registro de links;
- mover uma nota do Inbox para uma pasta de destino clara e já prevista no `CLAUDE.md`;
- atualizar o `Início.md` e o campo `updated`;
- criar nota nova no Inbox;
- acrescentar um item numa lista que já existe pela `colheita` (seção 7.11), quando ela existir.

**Para e mostra antes:**

1. **Nota protegida:** trocar, remover ou reescrever um dado que já está nela. Acrescentar não para.
2. **Perda de informação ou de sentido em qualquer nota:** apagar uma nota, unir duas, sobrescrever conteúdo, substituir um dado confirmado. A única nota apagada sem parada é o arquivo `<nota> - atualização.md` do Inbox depois de aplicado, porque o `CLAUDE.md` manda apagar e o conteúdo já está na original.
3. **Dúvida de dono ou de destino:** campo `pessoa` ambíguo, ou pasta de destino incerta.
4. **Achado estranho na conferência do toque** (seção 6.4).
5. **O que o `CLAUDE.md` já manda avisar:** dado contraditório ou ambíguo (regra 9), senha ou documento numa nota (regra 7), arquivo `nota (1).md`.
6. **Pasta nova** que não esteja na lista de destinos previstos do `CLAUDE.md`.
7. **Veredito de ideia** (`viavel`, `nao-viavel`): só o dono dá.
8. **Plano de uma Reforma.** O aval do plano cobre as operações que o plano lista. O que aparecer fora dele durante a execução para de novo.

**O que não está em nenhuma das duas listas para.** Se o Butler, por iniciativa própria, for fazer algo que não aparece nem em "segue" nem em "para" (mover uma nota que não está no Inbox, criar uma subpasta de ideia, criar fora do Inbox a lista que a `colheita` não achou), ele mostra antes.

**O que conta como acréscimo numa nota protegida:**

- **Item novo** (uma entrada na linha do tempo do carro, um equipamento, um programa) é acréscimo.
- **Campos derivados que o formato da nota exige** (no histórico do carro: "Última troca de cada item", a referência mais recente, as garantias em vigor) são atualizados junto com a entrada só quando ela é a mais recente, e a resposta mostra o antes e o depois de cada um. Entrada antiga não mexe neles. Tirar um item de uma lista derivada, como uma pendência do carro que foi resolvida, mostra antes.
- **Preencher um "Não informado"** é acréscimo só em dois casos: pedido explícito do dono, ou a rotina de registrar a partir de um documento (seção 7.8). Vindo de qualquer outro lugar, como um arquivo de atualização escrito por outra IA, é troca e mostra antes: o `CLAUDE.md` proíbe inferir modelo, voltagem, data ou loja.

**Pedido explícito já é o aval (decisão minha).** As paradas existem para o que o Butler decide por conta própria. Quando o dono pede a mudança nomeando o dado ("troca a voltagem da geladeira para 220V", "registra que desinstalei o X"), o pedido é a aprovação: o Butler faz e responde com o antes e o depois. Ele só para se o pedido contradisser um dado confirmado de um jeito que pareça engano, ou se, para cumprir o pedido, precisar mexer em algo que o dono não citou. Um clique do dono num botão do Wingman que nomeia a ação ("feito" numa pendência, "Começar projeto", "Arquivar") é pedido explícito do mesmo jeito (seção 7.10).

**Como o Butler pergunta num Lote (decisão minha):** ele não interrompe a cada nota. A nota com dúvida fica como está, as outras seguem, e as perguntas vêm juntas no fim, cada uma com o que ele faria. É o equivalente à lista a VALIDAR do Foreman. Na triagem, a nota com dúvida simplesmente continua no Inbox, que é a fila da própria triagem. Pergunta de qualquer outro pedido vai para a nota de pendências (seção 7.5) quando o dono seguir para outro assunto sem responder, para não se perder.

**Sem histórico, vale a regra de hoje (decisão do dono).** Enquanto o histórico da seção 6.5 não estiver funcionando, o Butler volta ao comportamento atual da regra 8 do `CLAUDE.md`: mostra antes de mover ou alterar várias notas. Isso vale em qualquer máquina e por qualquer motivo: antes da preparação, git não instalado, pasta do histórico apagada ou corrompida, PC formatado, notebook, ou `Sistema/Regras do Butler.md` ausente ou ilegível.

- **"Funcionando" tem um teste só (decisão minha):** o Butler conseguiu gravar o ponto de retorno das mudanças de fora no começo deste pedido. Se não conseguiu, está no modo sem histórico, e diz isso em uma linha. Um arquivo deixado de fora por suspeita de dado sensível (seção 6.4) não conta como falha.
- **As paradas da lista acima continuam valendo nos dois modos.** O modo sem histórico só acrescenta a regra de mostrar antes; não tira nenhuma proteção. A autonomia depende de dar para desfazer. O texto novo da regra 8 (seção 11) precisa dizer isso: parar pelo risco vale só com o histórico funcionando; sem ele, mostra antes. Assim uma sessão sem o Butler, ou em outro computador, não ganha a autonomia sem a rede.

### 6.3 Notas protegidas e o que o Butler aprende

- **Lista inicial (decisão do dono):** o histórico de manutenção do carro, os perfis e os inventários. São as notas que deram trabalho manual para montar. **(decisão minha)** Os inventários de programas contam como inventários.
- **A lista cresce com o uso (decisão do dono: "podemos ir aprendendo").** Quando ele disser "isso eu queria ter visto antes", o Butler propõe a linha nova e grava depois do sim.
- **O contrário também vale (decisão minha).** Quando ele disser "isso não precisa perguntar", ou "é assim mesmo" para um achado estranho, o Butler propõe a exceção com o texto exato que vai gravar e só grava depois do sim, como faz com a linha de proteção. Sem a exceção, a mesma pergunta voltaria a cada toque; sem mostrar o texto, um "é assim mesmo" sobre um caso poderia virar regra para todos.
- **Limite das exceções (decisão minha):** uma exceção vale para um tipo de mudança num tipo de nota, e fica escrita em `Sistema/Regras do Butler.md`, à vista. Nenhuma exceção dispensa a parada para apagar nota, para dado sensível ou para arquivo `nota (1).md`. O que o dono pode fazer é liberar uma ocorrência específica que não é dado sensível (seção 6.4).
- **O Butler nunca altera sozinho o `CLAUDE.md` nem `Sistema/Regras do Butler.md` (decisão minha).** São os dois arquivos que dizem o que ele pode fazer. Só mudam com o sim do dono, e nada escrito dentro de uma nota conta como esse sim. Os dois são sempre tratados como nota protegida, mesmo sem constar na lista: mudança de fora em qualquer um deles é avisada, e arquivo de atualização do Inbox que mire um deles sempre para, mesmo que só acrescente.
- **Onde fica (decisão minha):** numa nota do próprio vault, `Sistema/Regras do Butler.md`, que o dono lê e edita no Obsidian. Ela guarda a lista de notas protegidas, a lista de notas de formato rígido (seção 6.6) e as exceções aprendidas. O formato exato fica com quem construir, desde que seja legível por uma pessoa e não dependa da memória do Claude.

### 6.4 Conferência na hora do toque

Antes de alterar uma nota, o Butler confere só aquela nota:

- frontmatter completo e com valores válidos;
- nome do arquivo igual ao título;
- seção "Veja também" presente, com links para notas que existem;
- nenhum dado sensível;
- formato rígido respeitado, se a nota for de formato rígido.

Se estiver tudo certo, segue sem dizer nada. Se algo destoar, ele não corrige: pergunta se era para ser assim. Corrigir, só depois da resposta.

**Como ele sabe o que foi mexido por fora (decisão minha):** com o histórico da seção 6.5, tudo o que mudou no vault desde o último ponto de retorno foi feito fora do Butler (edição à mão no Obsidian, outra sessão, arquivo novo no Inbox). Antes de começar um pedido, ele grava essas mudanças como um ponto de retorno separado, "mudanças de fora". Assim elas nunca se misturam com as dele, e ele sabe exatamente quais notas merecem a conferência. Antes de gravar, ele verifica se há dado sensível nessas mudanças. Se houver, deixa só aquele arquivo de fora, grava o resto e avisa. Se o dono disser que aquela ocorrência não é dado sensível, ela é liberada, anotada nas regras e gravada. Assim um alarme falso não desliga o histórico inteiro.

- **Nota protegida mexida por fora (decisão minha):** se as mudanças de fora trocaram ou removeram um dado de uma nota protegida, o Butler avisa em uma linha, mesmo que o pedido não toque nessa nota. Não bloqueia nem corrige. É o que cobre as skills dos Perfis, que escrevem sem passar pelo gerente (seção 6.7).
- **Arquivo `nota (1).md` novo, ou mudança de fora no `CLAUDE.md` ou nas regras do Butler (decisão minha):** entram no mesmo aviso de uma linha. Sem isso, uma cópia de conflito do Drive seria gravada em silêncio e o pedido seguinte editaria a versão velha.
- **Sem histórico,** a conferência acontece do mesmo jeito em cada nota tocada. O Butler só não sabe dizer o que mudou por fora.

### 6.5 Histórico para desfazer

**Decisão do dono:** o vault ganha um histórico git só local, sem GitHub. As notas continuam sincronizando pelo Drive como hoje.

**Decisão minha, informada a ele e sem objeção:** a pasta do histórico fica fora do Drive, neste PC. Motivo: o Drive lida mal com a pasta `.git` (milhares de arquivos pequenos que mudam juntos) e pode criar cópias "(1)" ou subir um histórico pela metade. O preço: o histórico existe só neste PC. Como o vault só é editado aqui, o preço não pesa.

O que isso exige:

- **Nenhum arquivo do git dentro do vault (decisão minha).** Nem a pasta `.git`, nem um arquivo apontador, nem `.gitignore`. O Butler informa ao git onde está o histórico e onde está o vault a cada comando, e a lista do que ignorar fica dentro da pasta do histórico. Onde o histórico fica é configuração de cada máquina, guardada fora do vault. Motivo: um apontador dentro do vault seria sincronizado pelo Drive com um caminho que só existe neste PC, e o notebook, que já tem a nota de programas dele no vault, poderia quebrá-lo.
- **A pasta do histórico fica fora de qualquer pasta sincronizada ou sujeita a limpeza:** nem Google Drive, nem OneDrive (no Windows, `Documentos` pode estar no OneDrive), nem pasta temporária ou de cache que uma limpeza de disco apague. O `preparar` confere isso antes de criar.
- **Em máquina sem histórico** (o notebook, hoje), o Butler trabalha no modo da regra de mostrar antes. O que for feito lá chega a este PC pelo Drive e entra como "mudanças de fora".
- **Sem remoto, nunca.** O Butler não adiciona remoto nem faz push no vault.
- **Pontos de retorno:** um para as mudanças de fora, antes de começar; e, dentro de um Lote, um por nota concluída, todos com o rótulo do pedido **(decisão minha)**. Se a sessão cair no meio, no máximo uma nota fica pela metade, e o que já foi feito não se confunde com mudança de fora. Dentro do pedido, cada ponto grava só os arquivos que o próprio Butler alterou **(decisão minha)**: uma escrita tolerada do Wingman no meio do pedido (seção 7.10) fica de fora e entra como mudança de fora no pedido seguinte, para não ir junto num "desfaz". O garimpo grava o ponto dele ao terminar (seção 7.3), e esse ponto cobre também o que a `colheita` escreveu dentro do mesmo pedido (seção 7.11).
- **Um pedido por vez no vault (decisão minha).** A trava cobre o pedido inteiro, não cada comando. Se outra sessão quiser alterar o vault enquanto um pedido está em andamento, ela avisa e espera, ou para. Sem isso, a segunda sessão gravaria como "mudança de fora" metade do trabalho da primeira, e desfazer voltaria só uma parte. Consulta não é travada.
- **Desfazer por frase:** "desfaz a última triagem", "volta a nota X como estava ontem". O Butler mostra o que vai voltar, espera o sim e restaura. A restauração é um novo ponto de retorno, não apaga histórico. Se a nota mudou depois do ponto para o qual se quer voltar (por outro pedido, ou por fora), desfazer apagaria essa mudança posterior: o Butler mostra as duas versões e pergunta, em vez de sobrescrever. Isso vale em especial para o `Início.md` e para o registro de links, que quase todo pedido toca.
- **O que não entra no histórico:** as pastas temporárias do Drive e o estado de janela do Obsidian. A lista exata fica com quem construir.
- **O git não pode alterar os arquivos por conta própria** (fim de linha, acentos nos nomes, caminhos longos). A configuração fica com quem construir.

O que o histórico **não** cobre, e o documento assume:

- o que aconteceu antes do primeiro ponto de retorno;
- a perda deste PC: as notas continuam no Drive, o histórico se perde. O histórico de versões do próprio Drive segue como segunda rede, por tempo limitado;
- o que o Butler mexer fora do vault (não deve mexer);
- os estados intermediários do que muda por fora: entre dois pontos de retorno só ficam guardados o antes e o depois. Uma nota criada e apagada por fora nesse intervalo nunca entra no histórico. Para encurtar o intervalo, o aviso do início da sessão (seção 9) também grava o ponto das mudanças de fora **(decisão minha)**.

### 6.6 Formato livre e formato rígido

- **Formato rígido:** inventários, inventários de programas, histórico de manutenção do carro e o registro de links do Instagram. O `CLAUDE.md` (ou a própria nota) já dita o formato. O Butler segue a regra e não sugere nada.
- **Formato livre:** todo o resto, em especial `Ideias de Projetos` e `Projetos`. Os modelos em `Sistema/Modelos` são sugestão de roteiro. Antes de agir, o Butler lê a nota, duas ou três notas parecidas, o modelo e, nas ideias, o estágio.
- **Quais notas são rígidas** fica declarado em `Sistema/Regras do Butler.md`, apontando para a regra de cada uma. O que não está na lista é livre.

Como "propor a estrutura" acontece na prática **(decisão do dono para a nota nova; os outros dois casos são decisão minha)**:

- **Acréscimo a uma nota livre que já existe:** segue a forma que a nota já tem, sem proposta.
- **Nota livre nova:** o Butler escreve com a estrutura que julgou melhor e diz em uma linha qual escolheu e em que notas se baseou. O dono corrige se quiser.
- **Reestruturar uma nota livre que já existe:** é reescrita, então para e mostra a proposta antes.

### 6.7 Até onde a garantia vai

**(decisão minha)** As paradas valem para os pedidos que o gerente conduz. Não há trava que intercepte toda escrita no vault.

- As skills que escrevem no vault por fora do plugin (as skills de cada perfil nos Perfis; `liberar-espaco`, se escrever nas notas de programas) continuam como hoje, sem as paradas do Butler.
- O que elas mudarem entra no histórico como "mudanças de fora" no pedido seguinte. Então dá para ver e desfazer, mas ninguém mostra antes.
- As escritas toleradas do Wingman (seção 7.10) ficam de fora das paradas pelo mesmo motivo: são acréscimos ou cliques do dono, e entram no histórico como mudanças de fora.
- Uma trava em toda escrita seria outra arquitetura, mais cara e com mais chance de incomodar. Fica como evolução possível se uma dessas skills causar perda.

### 6.8 O resumo

Todo Lote e toda Reforma terminam com um resumo no mesmo formato:

- o que mudou, nota por nota (de onde para onde, o que foi completado);
- o que ficou esperando o dono, com a pergunta e o que o Butler faria;
- como desfazer.

No Direto, uma linha.

---

## 7. As skills do plugin

| Skill | Estado | O que faz |
|---|---|---|
| `gerente` | nova | Entrada de todo pedido que altera o vault: mede, conduz, para nos pontos da seção 6.2, resume, desfaz. Skill chamada pelo nome roda o preâmbulo dele (seção 7.10). |
| `preparar` | nova | Roda uma vez no vault: cria o histórico fora do Drive, a nota `Sistema/Regras do Butler.md` e o primeiro ponto de retorno. Equivale ao kickoff do Foreman. |
| `triagem` | nova | Tria o Inbox pelas regras do `CLAUDE.md`. |
| `programas` | nova | Atualiza a nota de programas da máquina e o JSON do winget. |
| `garimpo` | existe | Passa a morar no plugin e a ler e escrever o registro de links. Classifica cada link; quando a `colheita` existir, passa a mão para ela nos links de filme, lugar de viagem ou receita. |
| `colheita` | nova | Resumo curto de um link de vida pessoal (filme, lugar de viagem, receita) gravado direto numa lista que já existe, sem Inbox nem triagem (seção 7.11). Entrou na primeira versão a pedido do dono. |
| `pendencias` | nova | Guarda numa nota do vault o que ficou para depois e responde o que está pendente. |
| `projeto` | nova | Cria ou atualiza a nota curta de um projeto a partir do repositório dele. |
| `ideia` | nova | Desenvolve uma nota de ideia: pesquisa, funcionalidades, casos difíceis, enxugamento e, com o veredito do dono, promoção a projeto. |
| `consultar` | nova | Responde "o que eu sei sobre X?" com os links das notas usadas. Só lê. |
| `atualizar` | nova | Atualiza o plugin, como no Foreman. |

Além das skills, o `gerente` tem quatro rotinas sem skill própria (seção 7.8): **revisar**, **registrar**, **remover** e **arquivar**.

As skills `pendencias`, `projeto` e `ideia` e as rotinas de revisar, registrar e remover saíram do histórico de pedidos do dono neste vault: são coisas que ele pede repetidamente. Ele aprovou a entrada de todas no design. A divisão entre skill e rotina, e o comportamento de cada uma, são **decisão minha**. A skill `consultar` e a rotina de arquivar entraram com a integração ao Wingman (seção 7.10). O que era "modo leve do garimpo" virou a skill `colheita`, separada de `garimpo`, porque o contrato das duas é diferente (uma pesquisa e usa o Inbox, a outra não). São onze skills, dez na primeira versão: a `colheita` fica para depois (seção 7.11).

**Como o gerente entra em cena** fica com quem construir (descrição da skill, uma linha no `CLAUDE.md` do vault, um aviso no início da sessão). O requisito: o dono não precisa digitar comando, e consulta não aciona o gerente. Além disso, cada skill atende pelo nome (`/butler:triagem`, `/butler:garimpo`, …), menos a `colheita`, que só o garimpo chama (seção 7.11), e as rotinas atendem pelo gerente (`/butler:gerente arquiva <nota>`): é assim que o Wingman as chama, e o dono também pode.

### 7.1 Triagem

Aplica as regras 4 e 5 do `CLAUDE.md`, nota por nota:

- decide o destino pelo PARA, completa o frontmatter, acrescenta "Veja também", move e atualiza o `Início.md`;
- arquivo `<nota> - atualização.md`: compara com a original e aplica só as diferenças, mantendo a formatação. Se a atualização só acrescenta, aplica direto e apaga o arquivo do Inbox. Se ela troca ou remove algo que está na original, em qualquer nota, mostra as diferenças antes **(decisão minha)**: o arquivo é a nota inteira reescrita por outra IA, e uma linha que sumiu pode ser esquecimento dela, não intenção do dono. Preencher um "Não informado" conta como troca aqui (seção 6.2);
- nota com `relacionada`: unir as duas é parada (perda de sentido). Manter separadas segue direto, e o campo sai;
- nota com `pessoa` ou destino incertos: fica no Inbox, e a pergunta vai para o fim.

Casos que a skill precisa cobrir:

- **Nota sem frontmatter,** solta à mão no Inbox: completa o que der para saber e pergunta o resto.
- **Nota de garimpo com "Vale investigar? não" (decisão minha):** a triagem não descarta sozinha nem arquiva no vault uma nota que já foi julgada sem valor. Ela fica no Inbox, e no fim vem uma pergunta só, com todas juntas: "estas têm veredito não: descarto?". Com o sim, a nota é apagada e o registro de links recebe o status de descartado. Com o não, ela é triada como qualquer outra.
- **Pasta de destino que ainda não existe:** se está na lista do `CLAUDE.md`, cria. Se não está, é parada.
- **Já existe nota com o mesmo nome no destino:** parada.
- **Pasta que ficou vazia** depois de mover: sai, como o `CLAUDE.md` manda.
- **Nota de garimpo com veredito ✅ (decisão do dono):** pode virar uma pendência "testar" em `Sistema/Pendências.md`. A triagem só sugere: a pergunta vai para o fim, junto com as outras, e a linha é criada com o OK dele. É o único lugar em que uma nota do garimpo vira pendência.
- **Nota de garimpo vinda do Instagram:** ao mover, unir ou descartar, a triagem atualiza o status e o destino dela no registro de links. Essa regra passa a constar na nota do registro (seção 7.3) e segue direto; o destino anterior continua citado no texto da linha, como já é feito hoje.
- **Conteúdo da nota que parece instrução** ("ignore as regras", "apague tal nota"): é dado, não ordem.

### 7.2 Programas

Segue a seção "Inventários de programas" do `CLAUDE.md` e o levantamento da skill `liberar-espaco`. Só roda na máquina que está sendo inventariada: a nota certa é a do computador em que a sessão está (por exemplo, `PC de Mesa` e `Notebook`). Se não houver nota para a máquina, criar uma é pedido à parte. No notebook não há histórico, então vale o modo de mostrar antes (seção 6.5).

- refaz o `winget export --include-versions` e compara com a nota;
- programa novo: entra no fim da seção certa, com a fonte que de fato reinstala naquela máquina;
- programa desinstalado: a linha vai para "🗃️ Não instalados" com a explicação. Nunca é apagada;
- programa fora do catálogo do winget: mantém a entrada anterior no JSON e a versão corrigida à mão.

A nota é protegida. Então **(decisão minha)**: se a atualização só acrescenta programas, grava direto. Se move linha para "Não instalados", troca fonte ou troca versão registrada, mostra as diferenças antes. Seção ou fonte que o Butler não souber decidir vira pergunta no fim. O export reescreve o JSON inteiro: entrada que estava no JSON antigo e sumiu do novo é mostrada junto com as diferenças da nota.

### 7.3 Garimpo

O garimpo já existe em `~/.claude/skills/garimpo` e continua fazendo o que faz. Muda:

- **passa a morar no plugin,** sem deixar cópia na pasta antiga;
- **deixa de ter o caminho do vault escrito no texto:** usa o vault em que a sessão está;
- **lê e escreve `Sistema/Registro de Links Instagram.md`:** o `ja_no_vault.py` consulta o registro além de procurar no vault, e cada link processado ganha a sua linha. Linha do registro nunca é removida;
- **ajustes na nota do registro,** que estavam na fila: status para link descartado e para link que falhou ou é carrossel pendente; citar `/reels/` e que maiúsculas contam no código; tirar a frase sobre conferência "por busca do código";
- **regra nova na nota do registro:** o status e o destino de uma linha são atualizados quando a nota de destino é movida, unida, descartada, renomeada ou removida, mantendo o destino anterior no texto. Hoje o "Como o Claude usa" do registro não diz isso;
- **classifica cada link** (ideia de projeto, viagem, filme, receita, referência…) e mostra a classificação no OK do lote, para o dono corrigir o que errar (decisão do dono). A classificação e o destino sugerido de cada nota nova vão para o `estado.json` (seção 7.10), de onde o Wingman os lê: a regra do PARA fica num lugar só;
- **passa pelo preâmbulo do gerente** (seção 7.10): trava e ponto das mudanças de fora antes de gravar. As paradas do próprio garimpo continuam.

Escrever uma linha no registro é acréscimo e segue direto. O garimpo continua gravando só no Inbox e no registro, e não move nota. A frase da skill que hoje diz que ela nunca altera nota fora do Inbox ganha essa exceção. Quando a `colheita` existir, a escrita numa lista fora do Inbox é dela, não do garimpo (seção 7.11).

Ao terminar, o que o garimpo gravou recebe um ponto de retorno com o rótulo do pedido. Ele não vira um Lote do gerente, mas passa pelo preâmbulo dele: sem a trava e sem esse ponto, as notas dele entrariam como "mudança de fora" e "desfaz o último garimpo" não teria o que achar.

**O que não muda na primeira versão (decisão minha):**

- **As paradas do próprio garimpo ficam como estão:** o plano antes de gravar vários links, a pergunta sobre atualizar um link que já está no vault, a pergunta de `pessoa` e a oferta da nota índice. O garimpo funciona e o dono está acostumado com ele.
- **O formato da nota de garimpo continua dentro da skill,** com o frontmatter, os valores de `pessoa` e os links para os Perfis. Tirar isso de lá é trabalho da seção 10, não desta versão. A migração é mover a skill e fazer os ajustes listados acima, não reescrevê-la.
- **A skill `colheita` fica para depois** (seção 7.11). (superado por: entrou na primeira versão; o garimpo passa a mão para ela, seção 7.11) Na primeira versão, todo link vira nota no Inbox, com a classificação, e o `garimpo` ainda não chama a `colheita`. A classificação já sai certa desde o começo, para a colheita entrar depois sem mudar o garimpo.

### 7.4 Preparar

No vault do dono, roda uma vez:

1. confere se há arquivo `nota (1).md` ou dado sensível antes de qualquer coisa;
2. cria o histórico fora do Drive, o primeiro ponto de retorno, que é a foto do vault como está, e o primeiro `estado.json` na pasta do histórico (seção 7.10);
3. cria `Sistema/Regras do Butler.md` com a lista inicial de notas protegidas e de notas de formato rígido;
4. propõe as mudanças no `CLAUDE.md`, no `Início.md` e no `Como Usar com IA` (seção 11), para o aval dele.

Se rodar de novo, confere e oferece refazer, com o aval do dono, só o que estiver faltando:

- o histórico, se foi apagado ou se a máquina é outra;
- as regras do Butler, restauradas do histórico quando ele existir, para não perder as proteções e exceções aprendidas. Só voltam à lista inicial se não houver histórico, e o Butler diz isso;
- a nota de pendências e a passagem da fila que está na memória do Claude, que chegam numa etapa posterior da construção (seção 14).

O `atualizar` avisa quando uma versão nova pede uma nova rodada do `preparar`.

### 7.5 Pendências

Hoje o que o dono manda "deixar na fila" fica na memória do Claude, onde ele não vê, e perguntas feitas no meio de uma sessão longa se perdem.

- **Onde fica:** numa nota do vault, `Sistema/Pendências.md`, de formato rígido e de dono único: é do Butler, e só ele e as escritas toleradas do Wingman (seção 7.10) mexem nela.
- **Formato (decisão do dono):** o mesmo que o Wingman definiu para todas as listas de pendências. Uma linha por item, `- [ ] [eu] texto` para o que é do dono ou de terceiros e `- [ ] [claude] texto` para um próximo passo do Claude, com o contexto mínimo para retomar no próprio texto e marcadores opcionais no fim, entre parênteses: `(até AAAA-MM-DD)` para prazo, `(lembrar AAAA-MM-DD HH:MM)` para gatilho, `(depois de: …)` para dependência, `(de: projeto)` para recado, `(trava)` para o que trava outra coisa e `(desde AAAA-MM-DD)` para a data em que o item entrou **(decisão minha: o marcador `desde`, que a nota do Wingman já incorporou ao formato único; os outros são do Wingman)**.
- **Dono único:** a skill de pendências do plugin do Wingman cuida só dos repositórios (`docs/pendencias.md`, fora do vault e fora do Butler). Na pasta do vault, ela cede ao `pendencias` do Butler.
- **O que entra:** o que o dono mandar deixar para depois ("deixa na fila", "depois a gente faz"), e as perguntas do Butler que ficaram sem resposta. Uma pergunta do Butler só entra na fila quando o dono segue para outro assunto sem responder, ou diz "depois". Enquanto a conversa ainda está nela, não entra.
- **Entrar na fila é acréscimo** e segue direto, com uma linha de confirmação.
- **Consultar** ("ficou algo pendente?", "o que ficou pra trás?") é leitura: responde a lista, agrupada por assunto.
- **Sair da fila:** quando o dono disser que foi feito ou que desistiu, a linha sai sem deixar marca, como ele prefere. No vault não existe `[x]`: o `[x]` do Wingman vale só nos repositórios. O histórico guarda o que saiu. O Butler nunca tira um item por achar que foi resolvido: pergunta. A exceção é a pergunta dele mesmo: quando o dono responde, a linha dela sai. O clique "feito" no Wingman é pedido explícito, e a linha sai pela escrita tolerada dele, sem passar pelo Butler (seção 7.10).
- **Aviso no início da sessão:** a contagem de pendências entra na linha do aviso (seção 9).
- **O que já está na memória do Claude** (hoje, a fila do registro do Instagram): o `preparar` propõe passar para a nota o que ainda valer. A memória só é apagada com o sim do dono. Dos quatro itens dessa fila, três são cobertos por este design (seção 7.3) e o quarto já foi feito: o link aparece como triado no registro.
- **Não é lista de tarefas da vida.** Guarda só o que nasceu de um pedido no vault ou de uma conversa sobre ele.

### 7.6 Projeto

Cria ou atualiza a nota curta de um projeto em `Projetos`, a partir do repositório dele. Resolve notas defasadas: a do Foreman cita a versão 1.34.0 e o repositório está na 1.38.1.

- **O que lê:** o README, o arquivo de versão e os dados do GitHub (nome, link, descrição). Só lê. Nunca altera o repositório.
- **Onde acha o repositório:** pelo link em "Onde está" da nota. Sem link, ou com link que não abre, pergunta quando o dono pedir para atualizar. Nota sem link é normal: o projeto nascido pelo "Começar projeto" do Wingman (seção 7.7) ainda não tem GitHub, e a skill não cobra o link até ele pedir a atualização **(decisão minha)**.
- **Formato:** livre, com o `Modelo de Projeto` como roteiro. Nota curta e humana, sem a parte técnica, com o link do GitHub em vez do caminho local.
- **Nota nova:** escreve e explica a estrutura que escolheu, como toda nota livre (seção 6.6). Nasce no Inbox, como toda nota nova, exceto quando vem da promoção de uma ideia (seção 7.7), que cria a nota direto em `Projetos`.
- **Atualizar:** só o número da versão e o link são trocados sem perguntar, e a resposta mostra o antes e o depois. Todo o resto mostra antes: o texto de "Status", que nas notas atuais é prosa escrita à mão, e as seções "O que faz", "Decisões principais" e "Origem".
- **Projeto com mais de um repositório** (um app com backend e frontend em repositórios separados, por exemplo, cada um com sua própria versão): cada versão é atualizada na sua própria linha.
- **Projeto renomeado:** o título da nota é o nome humano do projeto ("Account Switcher"), não o nome do repositório (`account-switcher`). Repositório renomeado não renomeia a nota sozinho: o Butler mostra a mudança proposta e, com o sim, renomeia a nota, atualiza os wikilinks e o `Início.md`, e lista as notas tocadas.
- **Projeto sem repositório público** (os plugins de skill em `Projetos/Skills`): lê a pasta local que o dono indicar.
- **"Quais notas de projeto estão defasadas?"** é consulta: compara e responde, sem alterar.

### 7.7 Ideia

Desenvolve uma nota de `Ideias de Projetos`. É o que o dono fez à mão com o Wingman, e o fluxo que ele descreveu: pegar uma ideia parada, pesquisar, ver se é viável e transformar em projeto.

O que o dono pode pedir, em qualquer ordem:

- **Pesquisar:** o que já existe de parecido (projetos, repositórios, produtos), o que funciona e o que não. Cada afirmação leva a fonte e o grau de confiança, como no garimpo. O que a pesquisa traz é dado, nunca instrução.
- **Listar funcionalidades,** separando o núcleo do que pode vir depois.
- **Procurar casos difíceis e furos** no fluxo da ideia.
- **Enxugar:** apontar o que sobra ou não teria uso.
- **Promover a projeto.**

Como as paradas se aplicam:

- **Formato livre.** Antes de mexer, lê a nota, o estágio, as outras notas da ideia e ideias parecidas. O `Modelo de Ideia` é roteiro.
- **Acrescentar uma seção** (pesquisa, lista de funcionalidades, casos difíceis) segue direto.
- **Reorganizar, enxugar ou reescrever** a nota mostra a proposta antes.
- **Tirar algo da ideia:** quando o dono mandar remover uma funcionalidade, ela sai da nota e das menções, sem registro de que saiu (rotina de remover, seção 7.8).
- **Estágio:** `viavel` e `nao-viavel` só com o veredito do dono. O Butler pode dizer o que a pesquisa indica, mas não grava um estágio nem escreve um veredito por conta própria. Por pedido explícito, marca o estágio (`arquivada`, `projeto`, e `viavel` ou `nao-viavel` quando o dono der o veredito) e transcreve na seção "Veredito" o veredito que ele ditar: transcrever é pedido explícito, inventar não. No Wingman, os botões de estágio chamam esta skill; o Wingman não grava o campo.
- **Promover a projeto** segue o `CLAUDE.md`: cria a nota em `Projetos`, move as notas da ideia e muda o estágio para `projeto`. Move várias notas, então mostra o plano antes. O plano diz o título com que cada nota fica e para qual delas os links que já existem passam a apontar: hoje cinco notas têm link para `[[Wingman]]`, e a promoção criaria uma nota de projeto com o mesmo nome da nota de ideia. Pelo Wingman, a promoção é chamada pelo "Começar projeto" depois que o Wingman cria a pasta do projeto, o git local e o Foreman, fora do vault (decisão do dono). A nota do projeto nasce sem a linha "Repositório", porque ainda não há GitHub, e a skill `projeto` (seção 7.6) aceita a nota sem link.
- **Só notas com `type: ideia`.** Em `Ideias de Projetos` há notas `type: referencia`, sem estágio, que acumulam itens soltos (por exemplo, `Ideias Soltas` e `App de Receitas`). Elas não passam por este fluxo.
- **Pesquisa longa** vai para a nota irmã "<título> - Pesquisa", como o `Modelo de Ideia` prevê. Ela nasce ao lado da ideia, não no Inbox. Como a ideia passa a ter mais de uma nota, o `CLAUDE.md` pede uma subpasta: criar a subpasta e mover a nota original para ela mostra antes.
- **Não constrói o projeto.** A skill termina na nota. Construir é assunto de outra ferramenta, como o Foreman.

### 7.8 Rotinas do gerente

Quatro pedidos pontuais que usam as paradas que o gerente já tem. Não têm skill própria: quem chama pelo nome usa o gerente (`/butler:gerente arquiva <nota>`).

**Revisar**, a saúde do vault, a pedido ("revisa se tá tudo ok", "vê se ficou algo quebrado"):

- relata links quebrados, notas sem "Veja também", frontmatter inválido, nome de arquivo diferente do título, formato rígido desrespeitado, formatação quebrada, pastas vazias, `Início.md` fora de sincronia, notas de projeto defasadas, arquivos `nota (1).md` e suspeita de dado sensível;
- só lê e relata. Corrigir é outro pedido, e o relatório já diz quais correções seguiriam direto e quais parariam;
- é a única situação em que o Butler olha o vault inteiro, e só porque o dono pediu.

**Registrar**, a partir de um documento (PDF, nota fiscal, print), numa nota de formato rígido como o histórico do carro ou um inventário:

- lê o documento e lança os itens no formato que a regra da nota manda;
- item novo, ou dado que estava como "Não informado", é acréscimo e segue direto. O documento conta como fonte confirmada;
- dado do documento que contradiz um dado já confirmado na nota para e mostra os dois;
- o que não der para ler com certeza não é inferido: fica "Não informado" e entra na lista do que faltou;
- CPF, cartão e outros dados sensíveis do documento não são copiados. O documento não é guardado no vault;
- se um item do documento puder corresponder a mais de um item que já está na nota, para e pergunta qual é;
- os campos derivados da nota seguem a regra da seção 6.2;
- termina listando cada valor que entrou, item por item, e o que ficou sem informação. Não só a contagem: um dígito mal lido num PDF viraria dado confirmado sem ninguém ver.

**Remover**, um item e as menções a ele ("remove isso, como se não tivéssemos falado"):

- procura o item e todas as menções no vault: seções, linhas, links em "Veja também", entradas no `Início.md`;
- sempre mostra a lista do que vai sair antes, porque é apagar;
- com o sim, remove sem deixar marca nem registro de que saiu;
- onde a regra de uma nota proíbe tirar linha (o registro de links, "🗃️ Não instalados"), a linha fica e o Butler avisa (aprovado pelo dono). No registro de links, o texto do destino é atualizado para não apontar para o que saiu;
- o histórico ainda guarda o que saiu, e é isso que permite desfazer. Menção na memória do Claude está fora do vault: o Butler avisa que existe e não apaga sozinho.

**Arquivar**, um projeto ou uma ideia ("arquiva o projeto X", "arquiva a ideia Y"):

- move a nota, e a subpasta quando houver, para `Arquivo`, mantendo a subpasta, como o `CLAUDE.md` manda; troca a seção da nota no `Início.md`; numa ideia, marca `estagio: arquivada`;
- move nota fora do Inbox, então sempre mostra antes;
- o Wingman propõe arquivar (ideia `nao-viavel` há 90 dias sem mexer, "Arquivar" de um projeto iniciado) e chama esta rotina pelo gerente (seção 7.10); a decisão é o clique do dono;
- o repositório do projeto nunca é tocado.

### 7.9 Consultar

Responde "o que eu sei sobre X?" a partir das notas do vault.

- **Só lê.** Não pega a trava, não grava ponto de retorno e não passa pelo gerente, como toda consulta (seção 6.1).
- **Resposta curta,** com os links das notas usadas, considerando o campo `pessoa`: diz de quem é a nota quando isso importa. Quando não acha nota sobre o assunto, diz que não achou, em vez de responder de memória.
- **Pelo Wingman,** roda em `claude -p` na pasta do vault, sem gravar sessão, carregando só o plugin do Butler.
- **(decisão minha)** É skill, não rotina do gerente: o Wingman a chama pelo nome (`/butler:consultar <pergunta>`), e uma rotina só existe dentro do gerente, que pega trava e roda o preâmbulo, o que uma consulta não pode fazer.

### 7.10 Integração com o Wingman

O Wingman é o app painel que o dono está desenhando (nota `Ideias de Projetos/Wingman.md`). A divisão é dele: **o Wingman é o painel; o Butler é o segundo cérebro de fato.** O Wingman mostra o vault lendo os arquivos Markdown direto, sem LLM, e dispara as skills do Butler pelo nome numa aba. Ele não escreve no vault, fora das três escritas toleradas abaixo.

**Independência nos dois sentidos (decisão do dono).** O Butler funciona sozinho, pelo terminal, e é assim que ele nasce e anda. O Wingman também não depende do Butler: o núcleo dele (sessões, contas, projetos, pendências dos repositórios) entra em uso sem o vault, e o mod do vault no Wingman é futuro e opcional, previsto na nota dele em "Mods futuros". Até esse mod existir, as ações do vault são feitas direto numa sessão ou pelo `/butler:...`, no terminal. Tudo o que esta seção descreve é o encaixe para quando o mod entrar.

**Invocação explícita (decisão do dono).** O Wingman abre uma aba com uma sessão do Claude Code na pasta do vault e manda a skill pelo nome: `/butler:triagem`, `/butler:garimpo <links>`, `/butler:ideia <nota> <ação>`, `/butler:consultar <pergunta>`, `/butler:gerente arquiva <nota>` e assim por diante. Nunca um pedido em prosa. O acionamento sem comando, pelo dono digitando na conversa, continua valendo como antes (seção 7).

**Preâmbulo obrigatório (decisão minha).** Toda skill que altera o vault, chamada direto pelo nome (pelo Wingman ou pelo dono), roda antes o preâmbulo do gerente: pega a trava, grava o ponto das mudanças de fora e checa se o histórico está funcionando; e termina com o resumo da seção 6.8. Assim chamar a skill pelo nome não pula nada do que o gerente faria se tivesse recebido o pedido em prosa. O garimpo continua com as paradas dele (seção 7.3), mas também passa pelo preâmbulo (trava e mudanças de fora) e mantém o ponto de retorno próprio ao terminar.

**Arquivo de estado para o Wingman (decisão minha).** O Butler grava um `estado.json` dentro da pasta do histórico, fora do vault e do Drive, com:

- a trava ativa (pedido, sessão, início);
- se o histórico está funcionando;
- nota protegida mexida por fora, e arquivo `nota (1).md` achado;
- as perguntas que ficaram esperando o dono;
- o resumo do último pedido em forma legível por máquina: as notas tocadas, de onde para onde; no garimpo, cada nota nova com o veredito ✅/🤔/❌, a classificação do link e o destino sugerido; quando a `colheita` existir, cada link colhido com a classificação e a nota em que entrou, sem veredito (seção 7.11);
- a hora em que foi gravado.

O Wingman lê esse arquivo para os Avisos, o Agora e o resultado do lote, em vez de ler o terminal. O `preparar` cria o primeiro, junto com o histórico; o aviso do início da sessão e cada pedido o regravam. Ele não guarda conteúdo de nota nem dado sensível: só títulos, caminhos, vereditos e classificações. O formato exato fica com quem construir (seção 14). O caminho da pasta do histórico é configuração da máquina (seção 6.5); o Wingman lê essa mesma configuração para achar o arquivo.

**Destino sugerido e classificação vêm do Butler.** O Wingman nunca calcula o destino de uma nota nem a classificação de um link: lê os dois do `estado.json`, gravados pelo garimpo e pela triagem. A regra do PARA existe num lugar só.

**Escritas toleradas do Wingman (decisão do dono).** São três, declaradas em `Sistema/Regras do Butler.md`, todas só acréscimo ou pedido explícito por clique:

1. criar uma nota nova no `Inbox` pela Captura rápida;
2. acrescentar uma linha em `Sistema/Pendências.md`;
3. tirar uma linha de `Sistema/Pendências.md` quando o dono clica "feito": o clique é o pedido explícito (seção 6.2).

Qualquer outra escrita do Wingman no vault é proibida: estágio de ideia, nota de projeto, `Início.md` e o resto passam pelo Butler. As três respeitam a trava: com pedido em andamento, lido do `estado.json`, o Wingman enfileira e grava depois que a trava sai **(decisão minha: a fila é do Wingman)**. Entram no histórico como mudanças de fora, no pedido seguinte, e o Butler as trata como qualquer mudança de fora (seção 6.4).

**Pontos de retorno só com o que o Butler tocou (decisão minha).** Dentro de um pedido, cada ponto de retorno grava só os arquivos que o próprio Butler alterou (seção 6.5). Uma escrita tolerada do Wingman no meio do pedido fica de fora e entra como mudança de fora depois, para não ir junto num "desfaz".

**Sem o Butler instalado (decisão do dono).** O Wingman detecta e mostra só a leitura: contagens, listas e notas. Não há caminho alternativo em prosa.

**O que continua igual.** O Butler não sabe nem precisa saber se foi chamado pelo Wingman ou pela conversa: as paradas, o resumo e o desfazer são os mesmos. Nada no Butler depende de o Wingman existir, e nada no núcleo do Wingman depende de o Butler existir.

### 7.11 Colheita

Entrou na primeira versão a pedido do dono (2026-11-07). A fonte do comportamento é a skill `plugins/butler/skills/colheita/SKILL.md`; o que segue é o design que ela implementa. As duas questões que ficaram abertas foram decididas assim: a lista de cada classificação fica declarada na nota de regras, em `## Listas da colheita` (com `<destino>` para uma nota por destino), e o status no registro de links é `colhido`. Num link só, sem plano, o item é gravado direto e o resumo diz como desfazer.

- **O que faz:** recebe um link que o garimpo classificou como filme, lugar de viagem ou receita e grava um resumo curto direto numa lista que já existe: o filme na nota de filmes para assistir em `Lazer`, o lugar na nota da viagem em `Viagens`, a receita na nota de receitas que a regra 4 indica. Sem "vale investigar?", sem aprofundamento, sem nota no Inbox e sem triagem. É a exceção da regra 4 do `CLAUDE.md`, já escrita e aprovada. Qualquer outra classificação segue pelo Inbox, como sempre.
- **Quem chama (decisão minha):** só o garimpo. É ele que lê o link, classifica e mostra a classificação no OK do lote; a colheita grava depois desse OK, já com a classificação corrigida pelo dono. A colheita não atende pelo nome: um link colado vai sempre para o garimpo, que decide. Assim o Wingman não precisa saber da colheita para chamar: continua chamando `/butler:garimpo`.
- **Paradas (decisão minha):** acrescentar um item numa lista que já existe é acréscimo e segue direto (seção 6.2). Lista de destino que não existe: criar uma nota fora do Inbox não está em nenhuma das listas da seção 6.2, então para: a colheita propõe criar, como a regra 4 manda, e a proposta entra no OK do lote, junto com a classificação, para não virar uma segunda pergunta. Destino que é nota protegida (o Perfil Culinário, se a receita for para lá): acrescentar segue direto, trocar ou remover para, como em toda protegida. Item que já está na lista não é duplicado: a colheita avisa e não grava.
- **Conferência do toque:** a lista de destino passa pela conferência da seção 6.4 antes de receber o item, como qualquer nota tocada.
- **Registro de links (decisão minha):** o link ganha a sua linha no registro como qualquer outro, escrita pelo garimpo, com um status próprio de colhido e a nota de destino. O registro ganha esse status quando a colheita entrar, além dos da seção 7.3. Mover ou renomear a nota de destino atualiza a linha, pela regra nova do registro.
- **Histórico e estado (decisão minha):** a colheita roda dentro do pedido do garimpo: mesma trava, mesmo rótulo, e o ponto de retorno que o garimpo grava ao terminar cobre o que ela escreveu (seção 6.5). "Desfaz o último garimpo" desfaz a colheita junto. No `estado.json`, cada link colhido entra no resumo do pedido com a classificação e a nota em que foi gravado, sem veredito, que ela não dá (seção 7.10). É dali que o Wingman mostra o colhido no resultado do lote e nas listas da visão Pessoal.
- **Modo sem histórico:** gravar fora do Inbox é alterar uma nota que já existe. Sem o histórico funcionando, a colheita mostra antes, como a regra 8 manda.

---

## 8. Casos difíceis

| Situação | O que o Butler faz |
|---|---|
| Mediu o pedido para menos | As paradas valem em qualquer tamanho. Se crescer, para e sobe. |
| Pedido simples | Direto: faz e diz em uma linha. Consulta nem passa pelo gerente. |
| Pedido que mistura vault e outra coisa | O gerente cuida só da parte do vault. |
| Vault sem histórico, ou histórico quebrado (antes do `preparar`, git não instalado, pasta do histórico apagada) | Avisa em uma linha, oferece refazer com `preparar` e, até lá, mostra antes de alterar várias notas. As paradas da seção 6.2 seguem valendo. |
| `Sistema/Regras do Butler.md` apagado ou ilegível | Sem a lista de protegidas, o Butler não sabe o que proteger: trabalha no modo sem histórico e avisa. Não recria a nota sozinho: o `preparar` propõe restaurá-la do histórico. |
| Senha ou documento descoberto depois, já gravado no histórico | Avisa e propõe refazer o histórico sem aquele conteúdo. Só faz com o sim. |
| Pedido para desfazer algo em nota que mudou depois | Mostra as duas versões e pergunta. Não sobrescreve a mudança posterior. |
| PC formatado, vault restaurado do Drive | Não há histórico nesta máquina. Mesmo tratamento do caso acima. O histórico antigo se perdeu. |
| Sessão aberta no notebook, ou em qualquer outra máquina | Sem histórico lá: mostra antes de alterar várias notas. No PC, o que veio do notebook entra como "mudanças de fora". |
| O dono edita uma nota no Obsidian enquanto o Butler trabalha nela | Antes de gravar, confere se a nota mudou desde que a leu. Se mudou, não sobrescreve: pergunta. |
| Duas sessões do Claude no vault ao mesmo tempo | A trava vale pelo pedido inteiro. A segunda avisa que há um pedido em andamento e espera, ou para. Não força. Trava que sobrou de uma sessão que caiu é mostrada ao dono antes de ser liberada. |
| Arquivo `nota (1).md` do Drive | Parada: confere com o dono qual versão vale, como o `CLAUDE.md` manda. |
| Senha, cartão ou documento numa nota que chegou | Não copia, deixa só aquele arquivo fora do histórico, grava o resto e avisa. |
| Alarme falso de dado sensível | O dono diz que aquela ocorrência não é sensível. Ela é liberada, anotada nas regras e gravada. |
| Sessão cai no meio de um Lote | Cada nota concluída já tem ponto de retorno. Na volta, o Butler diz onde parou. |
| O `CLAUDE.md` mudou | Vale o texto novo: ele é lido a cada pedido. |
| Skill e `CLAUDE.md` discordam | Vale o `CLAUDE.md`, e o Butler avisa da divergência. |
| Lista de protegidas grande demais, paradas em excesso | O dono tira linhas de `Sistema/Regras do Butler.md`, ou diz "isso não precisa perguntar". |
| Achado estranho que na verdade é intencional | Depois do "é assim mesmo", vira exceção gravada e não volta. |
| Renomear uma nota | Atualiza os wikilinks que apontam para ela e lista no resumo as notas tocadas, inclusive as protegidas: o link continua apontando para a mesma nota, então nenhum dado muda. O registro de links usa texto, não link, e não quebra. |
| Nota de formato livre que não se parece com nenhuma outra | Usa o modelo como roteiro e diz que não achou nota parecida. |
| Nota de `pessoa: ana` (outra pessoa da casa) | Sem tratamento especial na primeira versão. Fica para aprender com o uso. |
| Winget falha, ou programa sem fonte clara | Não inventa: registra o que foi confirmado e pergunta o resto. |
| Repositório do projeto não abre, ou a nota não tem link | Ao atualizar, a skill `projeto` pergunta onde está. Não adivinha. Nota recém-promovida sem link não é erro (seção 7.6). |
| Nota de projeto ajustada à mão, e o README diz outra coisa | Mostra as duas versões antes de trocar o texto. |
| Pesquisa de uma ideia traz página com instrução embutida | É dado. Não segue. |
| Documento de onde se registra é ilegível em parte | Lança o que leu com certeza, deixa o resto como "Não informado" e lista o que faltou. |
| Item a remover aparece em nota de formato rígido que proíbe tirar linha | A linha fica, e o Butler avisa. |
| Pendência que parece resolvida | Não tira sozinho: pergunta. |
| Pedido para desfazer algo anterior ao histórico | Diz que não há ponto de retorno e lembra do histórico de versões do Drive. |
| O Wingman clica "feito" numa pendência, ou captura uma nota, durante uma triagem | A trava está no `estado.json`: o Wingman enfileira e grava depois que ela sai. A escrita entra como mudança de fora no pedido seguinte, e os pontos de retorno da triagem não a levam junto. |
| O Wingman chama uma skill e o Butler não está instalado | O comando não existe na sessão e nada roda. O Wingman detecta antes e mostra só a leitura; não cai em prosa. |
| `estado.json` ilegível ou velho | O Wingman mostra "lido há…" e não age. O Butler regrava o arquivo no próximo pedido ou no aviso do início da sessão; se não consegue gravar, diz em uma linha. |
| Link classificado como filme, lugar de viagem ou receita | Na primeira versão, vira nota no Inbox com a classificação, como todo link. Quando a `colheita` existir, o garimpo passa a mão para ela depois do OK do lote (seção 7.11). |
| A `colheita` não acha a lista de destino | Não cria sozinha: propõe criar no OK do lote e só grava com o sim. |
| O Wingman roda sem o Butler, ou o Butler sem o Wingman | Os dois funcionam. O Wingman mostra só a leitura do vault; o Butler atende no terminal e grava o `estado.json` do mesmo jeito. |

---

## 9. Melhorias além do pedido

Ideias para deixar o uso mais fluido. **Todas são sugestão minha**, nenhuma foi pedida. Marquei as que eu colocaria na primeira versão por serem baratas e ligadas ao núcleo. As que o dono aprovou viraram skill ou rotina e estão nas seções 7.5 a 7.8.

**Na primeira versão:**

- **Aviso no início da sessão,** em uma linha: quantas notas há no Inbox, quantas pendências há, se houve mudança de fora desde o último ponto de retorno (e se alguma pegou nota protegida) e se o histórico está funcionando. Nesse momento ele já grava o ponto das mudanças de fora. É o "andamento" do Foreman.
- **Desfazer por frase** (já na seção 6.5).
- **Captura rápida:** "anota isso" vira nota no Inbox, sem conversa. Se não estiver claro de quem é a nota, o campo `pessoa` fica em branco e a triagem pergunta. Pela caixa do Wingman, quem grava a nota é o próprio Wingman (escrita tolerada, seção 7.10).

**Do Wingman, não do Butler:**

- **Lembrete de coisa parada** (Inbox com nota há mais de uma semana, ideia há meses no estágio `ideia`, ideia `nao-viavel` há 90 dias): o Wingman lê os arquivos e propõe; o Butler só age quando chamado. O aviso do início da sessão (acima) continua, porque é dentro da sessão.

**Depois:**

- **Skill `colheita`:** resumo curto de um link de vida pessoal gravado direto numa lista que já existe (seção 7.11). Usa a exceção já escrita e aprovada na regra 4 do `CLAUDE.md` do vault (seção 11).
- **Registro de links para outras origens** além do Instagram (YouTube, artigos).
- **Prompt do ChatGPT gerado a partir das regras do vault,** para o `Como Usar com IA` não ficar desatualizado quando o frontmatter mudar.
- **Triagem agendada:** descartei para já. A triagem precisa do dono para as perguntas, e rodar sem ele só acumula pendência.

---

## 10. Outra pessoa começando do zero

Não é meta da primeira versão. Esta seção registra o que é do vault do dono e o que precisaria virar configurável, para que a primeira versão não feche essa porta.

**O que a primeira versão já faz para não fechar a porta:**

- nenhum caminho de vault escrito no plugin;
- todas as regras lidas do `CLAUDE.md` e de `Sistema/Regras do Butler.md` do vault em uso;
- `programas` e `garimpo` são opcionais: sem as ferramentas deles, o resto funciona;
- o Wingman é opcional: o Butler grava o `estado.json` sempre, mas nada nele depende de o Wingman existir.

**O que é específico do dono e precisaria virar configurável:**

| Pressuposto de hoje | O que seria preciso |
|---|---|
| Estrutura PARA com estas áreas (Casa, Tecnologia, Veículo...) | A pessoa escolhe as áreas, ou outro método, na preparação. |
| Campo `pessoa` com três valores (vault de casal) | Campo opcional, com os valores que a pessoa definir. |
| Frontmatter com estes campos e estes tipos | Um `CLAUDE.md` inicial gerado na preparação, editável. |
| Português do Brasil nas skills e nos modelos | Textos em outro idioma. É o item mais caro. |
| Windows: winget, PowerShell, cookies do Firefox | `programas` só existe no Windows. O garimpo depende de `yt-dlp`, `ffmpeg`, `gh` e do plugin `watch`. |
| Google Drive | Qualquer sincronizador. A regra "histórico fora da pasta sincronizada" é geral. |
| Notas rígidas: inventários, carro, registro do Instagram | A pessoa declara as dela em `Sistema/Regras do Butler.md`. Pode não ter nenhuma. |
| Perfis e as três skills que os usam | São do dono. Ficam fora. |
| Histórico em um computador só | Com dois computadores em uso de verdade, cada um teria o seu histórico, sem ligação entre eles. Precisaria de outra solução. |

**O caminho de quem começa do zero:**

1. Instala o plugin e abre o Claude Code numa pasta vazia (ou num vault do Obsidian recém-criado).
2. Pede "prepara este vault". O `preparar` faz poucas perguntas: quem usa, quais áreas da vida quer separar, que tipo de coisa pretende guardar.
3. Recebe um `CLAUDE.md` com as regras, o `Início.md`, o `Inbox`, a pasta `Sistema` com os modelos e o `Regras do Butler.md`, e o histórico já ligado.
4. Guarda a primeira coisa com "anota isso" ou colando um link.
5. Pede a primeira triagem e vê o resumo.

**Quem já tem um vault bagunçado** é um caso diferente e mais delicado: o `preparar` não reorganiza nada. Ele tira a foto inicial, lê o que existe, propõe um `CLAUDE.md` que descreve a organização atual e trata qualquer reorganização como Reforma, com plano e aval.

---

## 11. Mudanças no vault que dependem do aval do dono

O plugin não faz estas mudanças por conta própria. O `preparar` as propõe:

- **`CLAUDE.md`, regra 8:** hoje manda mostrar antes de mover ou alterar várias notas. Passa a ser parar pelo risco, valendo só com o Butler e o histórico funcionando; em qualquer outra situação (sessão sem o plugin, notebook, histórico quebrado), continua mostrar antes. O dono aprovou a mudança; o texto exato ainda passa por ele.
- **`CLAUDE.md`, pasta `Sistema`:** citar `Regras do Butler.md`, `Pendências.md` e o `Registro de Links Instagram.md` (este já estava na fila).
- **`Início.md`:** registrar `Sistema/Regras do Butler.md`, `Sistema/Pendências.md` e a nota do projeto.
- **Nota nova `Sistema/Pendências.md`,** de formato rígido, declarada em `Sistema/Regras do Butler.md`. Aprovada pelo dono. O formato é o da seção 7.5: `- [ ] [eu] texto` ou `- [ ] [claude] texto`, com os marcadores entre parênteses no fim; no vault, feito ou desistência tira a linha, sem `[x]`.
- **`Sistema/Regras do Butler.md`:** declara as três escritas toleradas do Wingman (criar nota no `Inbox` pela Captura rápida, acrescentar uma linha em `Pendências.md`, tirar uma linha de `Pendências.md` pelo clique "feito"), seção 7.10. Qualquer outra escrita do Wingman no vault é proibida.
- **Skill `colheita` (depois da primeira versão, seção 7.11):** usa a exceção já escrita na regra 4 do `CLAUDE.md` para gravar um resumo curto direto numa lista que já existe, em vez de criar nota no `Inbox`. O que ela pede ao vault quando entrar: o status de colhido no `Registro de Links Instagram.md` e, se faltar, a lista de destino de cada tipo, criada com o aval do dono. Não faz parte do `preparar` da primeira versão.
- **Memória do Claude:** passar a fila do registro do Instagram para a nota de pendências e apagar da memória. Aprovado pelo dono; acontece no `preparar`, não antes.
- **`Sistema/Como Usar com IA.md`:** o trecho da triagem diz que o Claude "mostra o que vai mover... e só então move". Ajustar para a regra 8 nova.
- **Nota `Projetos/Butler.md`:** curta, no molde das outras notas de projeto de código. Por isso a nota de regras se chama `Regras do Butler`, e não `Butler`: duas notas com o mesmo nome deixariam o link `[[Butler]]` ambíguo.
- **"A Inbox fica vazia depois da triagem":** o `CLAUDE.md`, o `Início.md` e o `Como Usar com IA` dizem isso. Com o Butler, a nota com dúvida e a nota com veredito "não" ficam no Inbox até o dono responder. O texto dos três precisa dizer isso.
- **`Sistema/Registro de Links Instagram.md`:** ganha a regra de atualizar status e destino (seção 7.3).

---

## 12. Perguntas que dependiam do dono

As duas foram respondidas em 2026-11-06.

1. **A regra 8 do `CLAUDE.md` muda?** Sim: **parar pelo risco**. A regra nova vale só com o histórico git funcionando. Sem ele, ou no notebook, o Butler volta a mostrar antes de alterar várias notas.
2. **Nota livre nova: escrever e explicar, ou propor antes?** **Escreve e explica.** O Butler escreve a nota inteira com a estrutura que julgar melhor e avisa em uma linha qual escolheu, sem parada extra.

---

## 13. Decisões que tomei no seu lugar

Para conferir na leitura. Todas podem ser trocadas. As cinco que vão de "Pedido explícito" a "O garimpo mantém" foram mostradas ao dono depois da revisão, e ele não contestou. As marcadas com "(checagem final)" entraram na última conferência do documento e ele ainda não viu.

- Três tamanhos de pedido: Direto, Lote e Reforma.
- Num Lote, as dúvidas vêm juntas no fim. A nota com dúvida fica onde está.
- Pedido explícito que nomeia o dado já é o aval, mesmo em nota protegida.
- As paradas valem só para o que o gerente conduz. As skills dos Perfis e a `liberar-espaco` seguem como hoje.
- Nenhum arquivo do git dentro do vault. No notebook, sem histórico, vale mostrar antes.
- Nota de garimpo com veredito "não" fica no Inbox e vira uma pergunta única de descarte no fim da triagem.
- O garimpo mantém as paradas e o formato de nota que tem hoje. Só muda de lugar e ganha o registro de links. (superado por: ele também classifica cada link, passa pelo preâmbulo do gerente e grava no `estado.json`, seção 7.3; e, quando a `colheita` existir, passa a mão para ela, seção 7.11)
- A lista de protegidas e as exceções ficam em `Sistema/Regras do Butler.md`, no vault.
- (checagem final) O Butler nunca altera sozinho o `CLAUDE.md` nem `Sistema/Regras do Butler.md`, e nenhuma exceção aprendida dispensa a parada para apagar nota, dado sensível ou arquivo `nota (1).md`.
- (checagem final) "Histórico funcionando" quer dizer: o ponto das mudanças de fora foi gravado no começo do pedido. As paradas valem nos dois modos.
- (checagem final) Arquivo de atualização do Inbox que troca ou remove algo da original mostra as diferenças antes, em qualquer nota.
- (checagem final) Desfazer não sobrescreve mudança posterior: mostra as duas versões e pergunta.
- (checagem final) Nota protegida mexida por fora gera um aviso de uma linha, sem bloquear.
- (checagem final) A pasta do histórico fica fora de qualquer pasta sincronizada (Drive, OneDrive) ou de limpeza.
- (checagem final) O aviso do início da sessão também grava o ponto das mudanças de fora.
- "Não precisa perguntar" e "é assim mesmo" também são aprendidos, não só "queria ter visto antes".
- Os inventários de programas contam como nota protegida.
- O histórico fica fora do Drive, neste PC.
- Mudanças feitas por fora viram um ponto de retorno próprio antes de cada pedido.
- Um ponto de retorno por nota concluída dentro de um Lote.
- Inventário de programas: só acréscimo grava direto; mover para "Não instalados" ou trocar fonte e versão mostra antes.
- O garimpo sai de `~/.claude/skills` e passa a morar no plugin.
- Pasta do repositório ao lado dos outros projetos do dono, e não numa pasta de projetos que não existe.
- Adoção por outra pessoa fica fora da primeira versão.
- `pendencias`, `projeto` e `ideia` são skills; revisar, registrar e remover são rotinas do gerente. (superado por: `consultar` e `colheita` também são skills, e arquivar também é rotina, seções 7.8, 7.9 e 7.11)
- As pendências ficam em `Sistema/Pendências.md`, e o Butler nunca tira um item por conta própria.
- Na nota de projeto, o que vem do repositório troca direto; texto que pode ter sido ajustado à mão mostra antes. (superado por: só a versão e o link trocam direto, item "Skill `projeto`" abaixo e seção 7.6)
- A skill `ideia` termina na nota e não constrói o projeto.
- Registrar: o documento conta como fonte confirmada, e dado ilegível fica "Não informado".
- Remover sempre mostra antes, e respeita a nota cuja regra proíbe tirar linha.

Entraram com a revisão independente do Fable, e o dono ainda não viu:

- A nota de regras se chama `Sistema/Regras do Butler.md`, para não repetir o nome da nota do projeto.
- Exceção aprendida é proposta com o texto exato e só gravada depois do sim.
- O `CLAUDE.md` e as regras do Butler são sempre protegidos; mudança de fora neles é avisada, e arquivo de atualização que mire um deles sempre para.
- O que não está em nenhuma das listas de "segue" e "para" mostra antes.
- Campos derivados de nota rígida só mudam quando a entrada é a mais recente, com antes e depois na resposta.
- Preencher "Não informado" só é acréscimo por pedido explícito ou na rotina de registrar.
- Dado sensível: só o arquivo suspeito fica fora do histórico, e o dono pode liberar um alarme falso.
- Arquivo `nota (1).md` novo entra no aviso das mudanças de fora.
- A trava vale pelo pedido inteiro, um pedido por vez no vault.
- O garimpo ganha um ponto de retorno próprio ao terminar.
- `preparar` rodado de novo refaz, com aval, só o que falta, e restaura as regras do histórico.
- Pergunta do Butler só vira pendência quando o dono muda de assunto sem responder.
- Skill `projeto`: só versão e link trocam direto; status, nome e o resto mostram antes.
- Skill `ideia`: não escreve a seção "Veredito"; só trata notas `type: ideia`; a nota irmã de pesquisa nasce ao lado da ideia. (superado por: ela transcreve na seção "Veredito" o veredito que o dono ditar, e continua sem inventar um, seção 7.7)
- Registrar lista cada valor que entrou, não só a contagem.
- Primeira versão inclui aviso no início da sessão, desfazer por frase e captura rápida.

Entraram com a integração ao Wingman, e o dono ainda não viu:

- Toda skill que altera o vault, chamada pelo nome, roda o preâmbulo do gerente (trava, ponto das mudanças de fora, checagem do histórico) e termina com o resumo. O garimpo passa pelo preâmbulo e mantém as paradas dele.
- As rotinas do gerente atendem por `/butler:gerente <rotina> <nota>`; `consultar` é skill porque não passa pelo gerente e não pode pegar trava.
- O `estado.json` fica na pasta do histórico, é criado pelo `preparar`, regravado a cada pedido e no aviso do início da sessão, e não guarda conteúdo de nota nem dado sensível.
- A trava que o Wingman respeita é a do `estado.json`; a fila das escritas toleradas é do Wingman, não do Butler.
- Dentro de um pedido, cada ponto de retorno grava só os arquivos que o Butler alterou.
- Um clique num botão do Wingman que nomeia a ação é pedido explícito, como uma frase do dono.
- `Pendências.md` ganha o marcador `(desde AAAA-MM-DD)` para a data em que o item entrou; os outros marcadores são os do Wingman.
- A skill `projeto` aceita nota sem link e só pergunta pelo repositório quando o dono pedir para atualizar.
- A classificação de cada link e o destino sugerido são gravados no `estado.json` pelo garimpo e pela triagem; o Wingman não os calcula.
- `consultar` e a rotina de arquivar entram na etapa 3 da ordem de construção.
- O que era "modo leve do garimpo" virou a skill `colheita`, separada de `garimpo`; fica para depois da primeira versão (seção 7.11). A exceção na regra 4 do `CLAUDE.md` já foi escrita e aprovada.
- O Butler não distingue pedido vindo do Wingman de pedido vindo da conversa: as paradas, o resumo e o desfazer são os mesmos.

Entraram com a revisão de coerência do fim do dia, e o dono ainda não viu:

- A `colheita` só é chamada pelo garimpo, depois do OK do lote; não atende pelo nome.
- Acrescentar numa lista que já existe pela `colheita` segue direto; lista que não existe vira proposta no OK do lote; destino protegido segue a regra das protegidas; item repetido não é gravado.
- A `colheita` roda dentro do pedido do garimpo: mesma trava, mesmo rótulo, e o ponto de retorno do garimpo cobre o que ela escreveu.
- O link colhido ganha linha no registro com um status próprio, e entra no `estado.json` com a classificação e a nota de destino, sem veredito.
- O mod do vault no Wingman é futuro e opcional: o núcleo do Wingman não espera nenhuma etapa do Butler (seção 14).

---

## 14. O que fica com quem construir

- **Organização do repositório,** seguindo o Foreman: `.claude-plugin/marketplace.json`, `plugins/butler/` com `plugin.json`, `skills/` e `hooks/`, `README.md`, `CLAUDE.md`, `docs/`, versão e notas de atualização.
- **Como o gerente é acionado** sem comando e sem pegar consultas.
- **Formato de `Sistema/Regras do Butler.md`,** legível por pessoa e estável para o Butler ler.
- **Mecânica do git:** onde fica a pasta do histórico e onde a máquina guarda esse caminho, o que é ignorado, o texto dos pontos de retorno, a configuração que impede o git de alterar arquivos, a trava contra remoto e push, o comportamento com o histórico ocupado.
- **O que vira script e o que fica em texto de skill.** A conferência do toque é candidata a script, como o `gate.py` do Foreman. A detecção de dado sensível precisa ser script: ela roda no aviso do início da sessão, antes de qualquer conversa.
- **Testes,** no espírito do Foreman: os scripts e a integridade do plugin.
- **Migração do garimpo** sem deixar duas cópias ativas.
- **Como detectar dado sensível** (senha, cartão, CPF, RG) com poucos alarmes falsos. Números de série, MACs, placa do carro e valores em reais são mantidos de propósito e não contam.
- **Como a trava de "um pedido por vez" expira** quando a sessão que a criou cai, e como isso aparece no `estado.json`.
- **Formato do `estado.json`** (seção 7.10): os campos da trava, do histórico, dos avisos, das perguntas pendentes e do resumo do último pedido, estável para o Wingman ler. Decidido junto com quem construir o Wingman.
- **Como o Wingman acha a pasta do histórico:** ele lê a mesma configuração da máquina em que o Butler guarda o caminho (seção 6.5). Onde essa configuração fica e em que formato é uma decisão só, para os dois.
- **A fila das escritas toleradas sob a trava:** o Wingman enfileira quando o `estado.json` mostra pedido em andamento e grava depois. O que acontece com a fila se o Wingman fechar é problema do Wingman, não do Butler.
- **O ponto de retorno só com os arquivos tocados:** o Butler precisa saber quais arquivos ele mesmo alterou dentro do pedido, para não levar junto uma escrita tolerada do Wingman.
- **Como o Wingman detecta que o Butler está instalado,** para mostrar só a leitura quando não estiver. Decidido junto com quem construir o Wingman.
- **Como a `colheita` acha a lista de destino** (a nota de filmes em `Lazer`, a nota da viagem certa em `Viagens`, o destino da receita) e onde essa correspondência fica declarada, e o nome do status de colhido no registro de links. Só quando ela for construída (seção 7.11). (superado por: decidido na construção, seção 7.11)

**Fatos do vault que quem construir vai encontrar:**

- o `Início.md` começa com uma marca de BOM antes do frontmatter. Quase todo pedido toca nele, então uma conferência de frontmatter estrita demais acusaria em quase todo pedido;
- as notas de projeto têm a seção "Status" em prosa, e um dos projetos tem dois repositórios;
- o histórico do carro tem a linha do tempo e seções derivadas dela ("Pendências", "Última troca de cada item", "Garantias em vigor", "Valores documentados");
- o inventário de eletrodomésticos tem doze campos "Não informado".

**Ordem sugerida, cada etapa já utilizável sozinha:**

1. Repositório, `preparar` (histórico e `Regras do Butler.md`) e o `gerente` com as paradas, o resumo e o desfazer.
2. `triagem`.
3. `pendencias`, `consultar` e as rotinas de revisar, registrar, remover e arquivar.
4. `garimpo` no plugin, com o registro de links e a classificação dos links.
5. `programas`.
6. `projeto`.
7. `ideia`, por último: é a mais aberta e depende de o gerente já lidar bem com notas de formato livre.
8. Melhorias da seção 9.

O `estado.json` e o preâmbulo das skills chamadas pelo nome entram na etapa 1, com o gerente. A `colheita` (seção 7.11) vem depois de tudo isso, com as outras melhorias da seção 9.

O núcleo do Wingman não espera nenhuma etapa: ele entra em uso sem o vault. O que espera é o mod do vault dele, futuro e opcional: as etapas 1, 2 e 4 (gerente, triagem e garimpo) para o mod entrar; a 3 para o "o que eu sei sobre X?" e o arquivar; a 7 para os botões de ideia. Enquanto o mod não existe, o Butler atende pelo terminal.

## 15. Como saber que deu certo

- Uma triagem em que nenhuma nota tem dúvida nem veredito "não" termina sem nenhuma pergunta, com o resumo.
- O mesmo pedido, em duas sessões, entrega o mesmo formato.
- Qualquer mudança feita pelo Butler volta atrás com uma frase.
- O dono não precisa dizer "isso eu queria ter visto antes" duas vezes para o mesmo tipo de coisa.
- Um pedido simples continua levando um pedido e uma resposta.
- O Wingman mostra o resultado de uma triagem ou de um garimpo lendo só o `estado.json`, sem ler o terminal.
- O Butler faz tudo isso numa sessão no terminal, sem o Wingman aberto.
- Quando a `colheita` existir, um link de filme, viagem ou receita entra na lista certa sem passar pelo Inbox, e "desfaz o último garimpo" o tira de lá.
