# Instalação das ferramentas do garimpo no Windows

A skill `butler:garimpo` vem com o plugin Butler e depende do plugin do `/watch` (`watch@claude-video`, repositório github.com/bradautomates/claude-video), que faz o Claude **assistir a um vídeo**: baixa com o `yt-dlp`, extrai frames com o `ffmpeg`, transcreve o áudio e lê tudo. Funciona em sessões do Claude Code (aba Code do Claude Desktop, terminal ou VS Code), não no Chat nem no Cowork.

O `scripts/assistir.py` da skill chama o `watch.py` do plugin com `--engine gemini` por padrão (o Gemini assiste ao vídeo: ele vai ao Google e é apagado de lá depois da resposta; precisa de `GEMINI_API_KEY`) e `--cookies-from-browser firefox`. Com `--engine local` (vídeo privado), passa `--whisper whisperx`: frames e transcrição na máquina, nada vai ao Google, à Groq nem à OpenAI. O WhisperX só é preciso para esse motor.

Pré-requisitos: Windows 10 ou 11, Claude Code instalado e `winget`. O Python precisa ser 3.10 ou mais novo: confira com `py -3 --version`. Se `python` abrir a Microsoft Store, é o alias do Windows, não um Python instalado (desligue em Configurações → Aplicativos → Aliases de execução de aplicativo).

## Opção A: prompt para colar no Claude Code

```text
Instale neste PC Windows as ferramentas da skill butler:garimpo e o plugin do /watch do repositório bradautomates/claude-video (o original, não um fork).

1. Detecte o sistema e me diga o que falta entre Python 3.10+, ffmpeg, yt-dlp, Deno, uv, gh e Firefox, antes de instalar.
2. Instale o que faltar com winget: Python.Python.3.12, Gyan.FFmpeg, yt-dlp.yt-dlp, DenoLand.Deno, astral-sh.uv, GitHub.cli e, se eu for ler Reels do Instagram, Mozilla.Firefox. Depois disso, abra um terminal novo para o PATH valer. O gh precisa de login: me peça para rodar "gh auth login" eu mesmo.
3. Instale o plugin: claude plugin marketplace add bradautomates/claude-video e claude plugin install watch@claude-video.
4. Transcrição local com WhisperX (sem chave de API): ache o setup.py do plugin em %USERPROFILE%\.claude\plugins\cache\claude-video\watch\<versão>\skills\watch\scripts\ (se houver mais de uma versão, a maior) e rode-o com --install-whisperx, SEM a flag -I do Python (senão ele não acha os módulos vizinhos). Se o uv falhar com "Missing expected target directory for Python minor version link", rode "uv python install 3.12" e o setup de novo; não crie o ambiente à mão, porque o setup apaga e recria o dele.
5. Em %USERPROFILE%\.config\watch\.env deixe WATCH_WHISPER_BACKEND="whisperx", WATCH_WHISPERX_MODEL="small", WATCH_WHISPERX_LANGUAGE=pt e WATCH_ENGINE=local. A GEMINI_API_KEY (motor padrão do garimpo) eu mesmo ponho nesse arquivo: me diga onde criar a chave (aistudio.google.com), mas nunca imprima nem me peça chaves.
6. Rode o setup.py com --check e me mostre o resultado.
7. Teste o plugin com um vídeo público do YouTube e me mostre transcrição, o que aparece na tela e um resumo de 3 linhas.

Regras: nunca me peça senha, cookie ou token no chat. Se algo falhar, me diga o erro exato e as opções, sem tentar de várias formas.
```

## Opção B: passo a passo manual (PowerShell)

1. Instalar as ferramentas e **reabrir o terminal**. O Python só se `py -3 --version` não mostrar 3.10 ou mais; o Firefox só para o Instagram. Qualquer pacote de ffmpeg serve (`Gyan.FFmpeg` ou `yt-dlp.FFmpeg`):

```powershell
winget install --id Python.Python.3.12 --exact
winget install --id Gyan.FFmpeg --exact
winget install --id yt-dlp.yt-dlp --exact
winget install --id DenoLand.Deno --exact
winget install --id astral-sh.uv --exact
winget install --id GitHub.cli --exact
winget install --id Mozilla.Firefox --exact
```

2. Entrar no GitHub pelo `gh` (a skill usa para pesquisar repositórios):

```powershell
gh auth login
```

3. Instalar o plugin (no terminal comum, ou com `/plugin ...` dentro do Claude Code):

```powershell
claude plugin marketplace add bradautomates/claude-video
claude plugin install watch@claude-video
```

4. Instalar a transcrição local (WhisperX). A pasta da versão muda com as atualizações, então o caminho do `setup.py` é buscado, ordenando pela versão:

```powershell
$setup = (Get-ChildItem "$env:USERPROFILE\.claude\plugins\cache\claude-video\watch\*\skills\watch\scripts\setup.py" | Sort-Object { [version]$_.Directory.Parent.Parent.Parent.Name } | Select-Object -Last 1).FullName
python $setup --install-whisperx
```

Rode o `setup.py` sem a flag `-I` do Python, porque ele importa módulos vizinhos. Baixa cerca de 1 GB de pacotes e 464 MB do modelo `small`, e pede 3 GB livres e 8 GB de RAM. No Windows o instalador usa o PyTorch de CPU, então roda na CPU mesmo com placa NVIDIA.

O instalador cria o ambiente em `%USERPROFILE%\.cache\watch\whisperx-venv` e o apaga e recria quando a instalação anterior não terminou. Se o `uv` falhar ao criar o Python 3.12 ("Missing expected target directory for Python minor version link"), instale o Python dele e rode o instalador de novo:

```powershell
uv python install 3.12
python $setup --install-whisperx
```

No PowerShell 5.1 use `$env:USERPROFILE` em vez de `~`: ele não expande `~` nos argumentos de programas externos.

5. Conferir o arquivo `%USERPROFILE%\.config\watch\.env`:

```text
WATCH_WHISPER_BACKEND="whisperx"
WATCH_WHISPERX_MODEL="small"
WATCH_WHISPERX_LANGUAGE=pt
WATCH_ENGINE=local
```

`WATCH_ENGINE=local` e `WATCH_WHISPER_BACKEND="whisperx"` garantem que o `/watch` usado direto não envie vídeo ao Gemini nem áudio à Groq ou à OpenAI, mesmo que exista uma chave dessas no ambiente (os padrões do plugin são `auto`, que usam a nuvem quando acham a chave). O `assistir.py` do garimpo passa o motor explicitamente, então essas linhas não mudam o garimpo.

Para o motor padrão do garimpo, acrescente você mesmo, no mesmo arquivo, a chave criada em aistudio.google.com (nunca cole a chave no chat):

```text
GEMINI_API_KEY=<sua chave>
```

6. Conferir a instalação (sai com código 0 se estiver tudo certo e 2 se faltar ferramenta):

```powershell
python $setup --check
```

7. Abrir uma **sessão nova** do Claude Code (o plugin e a skill só aparecem nela) e testar:

```text
/watch https://www.youtube.com/watch?v=<id> resuma este vídeo
```

## Instagram: login pelos cookies do navegador

O Instagram exige login. No Windows, `--cookies-from-browser chrome` falha com o erro abaixo, porque o Chrome atual criptografa os cookies de um jeito que o `yt-dlp` não abre:

```text
ERROR: Failed to decrypt with DPAPI.
```

**O que funciona: o Firefox.** Entre no Instagram pelo Firefox (de preferência com uma conta secundária) e **feche o Firefox** antes de usar, porque ele trava o banco de cookies enquanto está aberto:

```text
/watch https://www.instagram.com/reel/XXXX/ --cookies-from-browser firefox
```

Não fica nenhum arquivo de cookies solto no disco. Para não repetir a flag no `/watch` direto, dá para pôr `WATCH_COOKIES_FROM_BROWSER=firefox` no `.env` (vale para todos os sites). O `assistir.py` da skill já passa a flag.

**Só para uso manual, fora da skill: `cookies.txt` exportado.** A skill nunca usa nem cria arquivo de cookies. Se o Firefox não servir e você quiser rodar o `/watch` à mão, dá para exportar os cookies com a extensão **Get cookies.txt LOCALLY** no Chrome (com a aba do Instagram aberta), salvar em `C:\Users\<usuário>\cookies-instagram.txt`, fora de pastas sincronizadas, e usar `--cookies C:\Users\<usuário>\cookies-instagram.txt`. O arquivo guarda a sessão do Instagram em texto puro e o `yt-dlp` pode regravá-lo: apague logo depois do uso e nunca cole o conteúdo dele no chat.

Carrosséis de imagens não são vídeo: o `yt-dlp` responde "No video formats found" ou "There is no video in this post". Para esses, use prints ou o Claude in Chrome.
