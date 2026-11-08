# Contribuir

O caminho mínimo para mudar o plugin e abrir um PR. As premissas e as regras completas estão no [`CLAUDE.md`](CLAUDE.md); o mapa de onde cada coisa mora, na seção [Mapa](CLAUDE.md#mapa-onde-cada-informação-mora) dele.

## Preparar o clone

```bash
git clone https://github.com/Lindenjefferson/butler.git
cd butler
```

Você precisa de Python 3, git e o [Claude Code](https://code.claude.com) no `PATH` (no Windows, os comandos rodam no Git Bash). Instale também o `pre-commit` de segredos e caracteres invisíveis do [Foreman](https://github.com/Lindenjefferson/foreman): `python <clone do foreman>/plugins/foreman/hooks/pre-commit-secret-scan.py --install-pre-commit`.

Para testar o plugin de verdade, use **uma cópia** de um vault, nunca o vault que você usa: `claude plugin marketplace add ./butler` e, na pasta da cópia, `claude plugin install butler@butler --scope local`. Rode o `preparar` com `--historico` numa pasta de teste, ou defina `BUTLER_CONFIG` para uma configuração só do teste, para não misturar com a configuração da máquina.

## Testar e validar

Os comandos do `CLAUDE.md`, rodados localmente antes de cada commit (não há CI):

```bash
for t in plugins/butler/hooks/tests/test_*.py plugins/butler/skills/*/tests/test_*.py; do sh plugins/butler/hooks/python.sh "$t"; done
claude plugin validate plugins/butler
claude plugin validate .
```

Cada suíte roda sozinha, sem pytest, e termina em `ALL PASS`. O laço inteiro leva alguns minutos, porque as suítes do gerente criam históricos git de verdade.

## Mudar

- Branch `feat/...` ou `fix/...` a partir da `main`, entregue por PR.
- **Teste primeiro** para o `butler.py`, a `lib/`, os scripts das skills e os hooks: o teste novo falha antes da mudança.
- Cada componente tem uma fonte de verdade, o próprio arquivo (skill, docstring do script). O README e o `CLAUDE.md` ganham no máximo uma linha com link.
- Nada de um vault específico no que se instala: o `test_plugin_integrity.py` barra caminho de usuário, e-mail e nome de pessoa em `plugins/butler/`.
- Ao tocar um arquivo, remova o que ficou obsoleto ou duplicado e liste no PR o que saiu.
- Arquivos em UTF-8 e LF, em português do Brasil.
- Nunca `git commit --no-verify`.
- Uma ideia nova passa pelo filtro do `CLAUDE.md` e pelo [roadmap](docs/roadmap.md) antes de virar PR.

## Versão

A `version` de [`plugin.json`](plugins/butler/.claude-plugin/plugin.json) sobe a cada release, com uma seção nova no [histórico](plugins/butler/UPGRADING.md) que diz o que entrou, o número do PR e o parágrafo "Ao atualizar" (ou "nada muda"). Quem sobe a versão e faz o merge é o dono.
