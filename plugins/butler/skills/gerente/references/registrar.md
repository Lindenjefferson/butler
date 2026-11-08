# Registrar a partir de um documento

Lançar numa nota de formato rígido (um histórico de manutenção, um inventário) os itens de um documento: PDF, nota fiscal, print, foto de recibo.

1. Preâmbulo do gerente. Leia a regra da nota no `CLAUDE.md` (a seção que a nota aponta) e a nota inteira.
2. Leia o documento. Ele conta como fonte confirmada.
3. Para cada item do documento:
   - **Item novo**, ou dado que estava como "Não informado": é acréscimo e segue direto, no formato e na posição que a regra manda (por data, por categoria);
   - **dado que contradiz um dado já confirmado** na nota: pare e mostre os dois. Dado confirmado só é trocado por dado novo confirmado, com o sim;
   - **item que pode corresponder a mais de um item da nota**: pare e pergunte qual é;
   - **o que não der para ler com certeza:** não infira. Fica "Não informado" e entra na lista do que faltou.
4. Campos derivados da nota (a última troca de cada item, garantias em vigor): mudam só quando a entrada nova é a mais recente, com o antes e o depois na resposta.
5. **Dado sensível do documento** (CPF, cartão, senha): não copie. Diga que estava lá e não entrou. O documento não é guardado no vault.
6. `B ponto` com a nota.
7. Termine listando **cada valor que entrou, item por item**, e o que ficou sem informação. Não só a contagem: um dígito mal lido viraria dado confirmado sem ninguém ver.
