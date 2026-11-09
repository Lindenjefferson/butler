# Butler

> *In English:* a Claude Code plugin that manages an Obsidian vault: it sizes each request, runs the vault's routines (inbox triage, link harvesting, follow-ups, project and idea notes), stops only where information could be lost, and undoes any change with one sentence, backed by a local git history kept outside the synced folder. The docs and the skills are in Portuguese.

Um gerente para um vault do [Obsidian](https://obsidian.md), dentro do [Claude Code](https://code.claude.com). Ele mede o tamanho de cada pedido, conduz a rotina do vault sozinho (triagem do Inbox, garimpo de links, pendências, notas de projeto e de ideia), confere o próprio trabalho e só para onde há risco de perder informação. Tudo o que ele faz sozinho dá para desfazer, nota por nota, mesmo dias depois.

Sem o Butler, cada ação no vault é um pedido solto na conversa: funciona, mas o mesmo pedido sai de formas diferentes em cada sessão, e o vault é só depósito. Com ele, o mesmo pedido sai sempre do mesmo jeito, no mesmo formato de resumo.

## Propósito e princípios

- **As regras moram no vault.** O plugin não traz nenhuma regra de um vault: ele lê o `CLAUDE.md` do vault a cada pedido e a nota `Sistema/Regras do Butler.md`, que a pessoa lê e edita no Obsidian. Em conflito, vale o vault.
- **Parar pelo risco, não pela quantidade.** O que só acrescenta segue sem perguntar. O que pode perder informação, perder sentido ou causar dano é mostrado antes.
- **Tudo dá para desfazer.** O histórico git do vault fica fora dele e fora de qualquer pasta sincronizada. Sem esse histórico funcionando, o Butler volta a mostrar antes de alterar várias notas.

As premissas e as regras para mudar o plugin estão no [`CLAUDE.md`](CLAUDE.md).

## Como funciona

```
pedido → mede (Consulta | Direto | Lote | Reforma) → preâmbulo: trava + mudanças de fora + histórico
       → nota por nota: confere → muda → ponto de retorno → dúvidas juntas no fim ✋ → resumo
```

✋ espera você; Consulta não passa pelo gerente.

1. **Mede o pedido** pelo que a mudança faz: uma pergunta é respondida direto; uma mudança que só acrescenta é feita e dita em uma linha; uma rotina sobre várias notas segue nota por nota e junta as dúvidas no fim; uma mudança de estrutura mostra o plano antes.
2. **Preâmbulo.** Pega a trava (um pedido por vez no vault), grava num ponto próprio o que mudou por fora (Obsidian, outra sessão, o celular) e avisa em uma linha se uma nota protegida perdeu dados por fora, se apareceu uma cópia de conflito do sincronizador ou se um arquivo tem cara de dado sensível.
3. **Confere na hora do toque.** Antes de mexer numa nota, confere se ela está de acordo com as regras. Se notar algo estranho, não corrige: pergunta se era para ser assim.
4. **Grava um ponto de retorno por nota concluída** e termina com um resumo: o que mudou, o que ficou esperando você e como desfazer.
5. **Desfaz por frase.** "Desfaz a última triagem" tira só o que aquele pedido mudou; uma mudança posterior em outro trecho da mesma nota fica. "Volta a nota X como estava ontem" mostra as duas versões antes.
6. **Aprende com o uso.** "Isso eu queria ter visto antes" vira uma proteção nova; "isso não precisa perguntar" vira uma exceção. As duas só são gravadas na nota de regras depois do seu sim.

O passo a passo de um pedido, com o que você digita e o que vê, está em [Como é um pedido](docs/como-e-um-pedido.md).

## Vocabulário

- **Vault**: a pasta do Obsidian, com as notas em Markdown.
- **Histórico**: o repositório git do vault, guardado fora dele (por padrão em `%LOCALAPPDATA%\Butler\<vault>-<código>` no Windows e em `~/.local/share/butler/` no Linux), sem remoto, nunca enviado para lugar nenhum.
- **Ponto de retorno**: um commit desse histórico, com o rótulo do pedido.
- **Mudanças de fora**: tudo o que mudou no vault sem passar pelo Butler, gravado num ponto próprio antes de cada pedido.
- **Nota protegida**: uma nota que deu trabalho para montar (um inventário, um histórico de manutenção, um perfil); trocar ou remover um dado dela sempre mostra antes.
- **Formato rígido**: uma nota cujo formato vem de uma regra; o Butler segue a regra e não sugere nada.
- **Trava**: o arquivo que garante um pedido por vez no vault, mesmo com várias sessões do Claude abertas.

## Começo rápido

**Você precisa de:**

- [Claude Code](https://code.claude.com);
- Python 3 e git no `PATH` (o Python como `python` ou `python3`);
- Windows (com o Git Bash, onde rodam os hooks e os comandos) ou Linux; o macOS não foi testado;
- para o garimpo de vídeos, as ferramentas de [`references/instalacao.md`](plugins/butler/skills/garimpo/references/instalacao.md); para o inventário de programas, o `winget`.

**Instalar:**

```bash
# uma vez por máquina
claude plugin marketplace add Lindenjefferson/butler

# na pasta do vault, só nele
cd "<pasta do vault>"
claude plugin install butler@butler --scope local
```

O escopo local grava a ativação em `.claude/settings.local.json` dentro do vault. Para usar em vários vaults, instale com `--scope user`: fora de um vault do Butler (sem histórico nesta máquina e sem a nota de regras), ele fica calado.

**Usar:** abra o Claude Code na pasta do vault e peça:

1. `prepara este vault` (ou `/butler:preparar`): uma vez por máquina. Cria o histórico, a nota de regras e a de pendências, e propõe as mudanças no `CLAUDE.md` do vault.
2. O que você quer: `tria o Inbox`, `guarda esse link: <url>`, `anota isso: …`, `ficou algo pendente?`, `atualiza a nota do projeto X`, `desfaz a última triagem`, `revisa se tá tudo ok`.

O vault precisa de um `CLAUDE.md` na raiz com as regras dele (pastas, frontmatter, onde cada nota vai). O Butler segue o que estiver lá.

## Componentes

| Componente | Função |
|---|---|
| [`gerente`](plugins/butler/skills/gerente/SKILL.md) | Entrada de todo pedido que altera o vault: mede, conduz, para nos pontos de risco, resume e desfaz; rotinas de revisar, registrar, remover e arquivar |
| [`preparar`](plugins/butler/skills/preparar/SKILL.md) | Cria o histórico, a nota de regras e a de pendências; refaz só o que falta |
| [`triagem`](plugins/butler/skills/triagem/SKILL.md) | Tria o Inbox pelas regras do vault, nota por nota |
| [`garimpo`](plugins/butler/skills/garimpo/SKILL.md) | Assiste ao vídeo ou lê a página de um link, investiga o que ele cita e grava a nota no Inbox |
| [`colheita`](plugins/butler/skills/colheita/SKILL.md) | Chamada pelo garimpo: grava um filme, um lugar de viagem ou uma receita direto na lista declarada, em uma linha, sem nota no Inbox |
| [`pendencias`](plugins/butler/skills/pendencias/SKILL.md) | Guarda o que ficou para depois e responde o que está pendente |
| [`consultar`](plugins/butler/skills/consultar/SKILL.md) | Responde "o que eu sei sobre X?" com os links das notas; só lê |
| [`projeto`](plugins/butler/skills/projeto/SKILL.md) | Cria ou atualiza a nota curta de um projeto a partir do repositório dele |
| [`ideia`](plugins/butler/skills/ideia/SKILL.md) | Desenvolve uma nota de ideia: pesquisa, funcionalidades, furos, veredito, promoção a projeto |
| [`ideia-para-inbox`](plugins/butler/skills/ideia-para-inbox/SKILL.md) | Grava uma ideia curta (texto ou áudio transcrito) como nota nova no Inbox, sem pesquisar; feita para um serviço chamar, como um bot |
| [`programas`](plugins/butler/skills/programas/SKILL.md) | Atualiza o inventário de programas da máquina e o JSON do winget |
| [`atualizar`](plugins/butler/skills/atualizar/SKILL.md) | Atualiza o plugin e aplica as notas de cada versão |
| [`butler.py`](plugins/butler/skills/gerente/butler.py) | O que se confere sem modelo: histórico, trava, pontos, desfazer, renomear, conferência, revisão, dado sensível, `estado.json` |
| [`hooks`](plugins/butler/hooks/hooks.json) | Aviso de uma linha no início da sessão num vault do Butler; guarda que nega escrita no vault fora de um pedido do gerente e pergunta antes da que perde linhas; trava solta no fim |

## O que sai da sua máquina

Nada além do que o Claude Code já envia na conversa. O histórico do vault fica só nesta máquina, sem remoto: o script recusa trabalhar com um remoto configurado. Arquivos com cara de dado sensível (senha, cartão, CPF, RG, token) e binários (imagens, PDFs) ficam fora do histórico até você liberá-los, e o script nunca mostra o valor achado, só o tipo e a linha.

## Painel

O Butler funciona sozinho, pelo terminal. Um painel (o autor usa o dele, o Wingman) pode mostrar o vault lendo o `estado.json` que o Butler grava na pasta do histórico (o formato está na docstring de [`lib/estado.py`](plugins/butler/skills/gerente/lib/estado.py)) e chamar as skills pelo nome (`/butler:triagem`, `/butler:garimpo <links>`, `/butler:consultar <pergunta>`, `/butler:gerente arquiva <nota>`).

## Para onde vai

As ideias em avaliação e as recusadas estão no [roadmap](docs/roadmap.md); o que cada versão entregou, no [histórico](plugins/butler/UPGRADING.md).

## Para contribuir

Nesta ordem:

1. [Como é um pedido](docs/como-e-um-pedido.md): o caminho de um pedido do começo ao resumo.
2. O [mapa](CLAUDE.md#mapa-onde-cada-informação-mora) do `CLAUDE.md`: em que arquivo mora cada comportamento, e as premissas e regras que valem para toda mudança.
3. [CONTRIBUTING.md](CONTRIBUTING.md): clonar, instalar o hook de segredos, rodar os testes e abrir o PR.

## Licença

[MIT](LICENSE). Feito e usado no dia a dia pelo autor no próprio vault; issues e sugestões são bem-vindas, sem garantia de suporte.
