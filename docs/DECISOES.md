# Decisões do projeto

- **D001 (híbrido):** código faz transcrição, segmentação, pontuação, validação e corte;
  o LLM só julga candidatos e redige textos, com saída estruturada.
- **D002 (sem automação de login):** não automatizamos o claude.ai nem outros chats. Usamos
  "pacotes" manuais (arquivo .md com instruções e dados; resposta colada de volta e validada)
  e, depois, APIs de camada gratuita com chave de cada pessoa.
- **D003 (estado em arquivos):** o estado do projeto vive em arquivos do repositório, nunca só
  em conversa de chat, para qualquer pessoa ou conta continuar sem perda.
- **D004 (contrato editorial):** o prompt original do dono do projeto (`prompts/`) é a fonte
  das regras editoriais. Mudanças só com aprovação.
- **D005 (testes com gabarito):** o vídeo `tuVNNEO-NKc` e os cortes aprovados são o teste de
  regressão (`tests/fixtures/`).
- **D006 (Python 3.12, Windows):** caminhos com `pathlib`, arquivos em UTF-8.
- **D007 (dados pesados fora do Git):** vídeos, cache e modelos ficam em `DATA_DIR`.
- **D008 (direitos autorais):** o conteúdo é de terceiros. Crédito não equivale a autorização.
  Antes de publicar ou de investir em compilações longas, definir a estratégia (autorização,
  licenciamento ou comentário próprio substancial). Registrar a decisão aqui.
