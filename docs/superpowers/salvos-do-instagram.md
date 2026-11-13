# Importar os Salvos do Instagram

**Ainda não implementado.** São as decisões já tomadas pelo dono para o modo "importar salvos" do `garimpo`, trazidas da skill solta que veio antes do plugin. O item está no [roadmap](../roadmap.md). Quando for construído, este texto vira uma referência da skill `garimpo` e sai daqui.

- **Caminho:** a exportação oficial da Meta (Central de Contas → Suas informações e permissões → Baixar suas informações → só **Salvos**, formato **JSON**) dá a lista de posts. Os vídeos são baixados pelo `assistir.py`, como hoje. Nada de instaloader, gallery-dl para listar o feed, extensões ou API não oficial.
- **Conta:** os salvos estão na conta do Instagram do dono, a mesma logada no navegador que baixa os vídeos. Sem conta secundária para baixar: o dono recusou.
- **Dono da nota:** o dono da conta, por padrão, em todas as notas importadas. Ele muda depois, se precisar.
- **Volume e coleções:** o volume ainda é desconhecido, mas os salvos costumam estar organizados em coleções. A importação lê as coleções do `saved_collections.json` e, no plano, mostra a contagem por coleção para o dono escolher quais importar.
- **Coleção no vault:** cada coleção vira uma tag `colecao-<nome>` (minúsculas, sem acento, contando no limite de tags do vault) e uma subpasta no Inbox com o nome da coleção, onde as notas dela são gravadas. A tag fica na nota depois da triagem; a subpasta some quando esvaziar. Sem nota índice por coleção, a não ser que o dono peça.
- **Ritmo (recomendação aceita para começar):** até 20 posts por dia, em 2 rodadas de 10, com `--pausa 40`. Para o dia inteiro no primeiro sinal de limite ("login required", "rate-limit", "429", "Please wait a few minutes"), grava o ponto e avisa. Depois de uma semana sem sinal de limite, pode subir para 30 por dia. O Instagram não publica limite: esses números são prudência, não regra conhecida.
- **Ordem:** mais recentes primeiro (pela data em que o post foi salvo), dentro das coleções escolhidas.
- **Posts sem vídeo (carrosséis): pendente.** O dono vai decidir entre ler pelo Claude in Chrome, mandar prints ou instalar o gallery-dl. Até lá, os posts `sem_video` ficam listados como pendentes no plano, sem nota.
- **Com o plugin** (novo, não estava na skill solta): cada post importado passa pelo registro de links, como um link colado, e vira nota no Inbox com a classificação no frontmatter; um post de filme, lugar de viagem ou receita (ou outra classificação declarada) só vai para a `fichar` depois, na triagem, se o vault declarar a lista.
