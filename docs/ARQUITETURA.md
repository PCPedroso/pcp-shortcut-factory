# Arquitetura

## Fluxo
1. **Entrada:** transcrição (JSON ou texto com tempos) [depois: yt-dlp / Whisper].
2. **Normalização:** legendas automáticas sobrepostas viram trechos com tempo efetivo
   (o fim de uma fala ≈ início da linha seguinte; margem de 1 a 3 s).
3. **Segmentação e candidatos (código):** blocos por assunto, detecção de autopromoção,
   números, marcadores de hipótese/recomendação, pontuação por heurísticas.
4. **Julgamento (LLM, saída estruturada):** recebe só os candidatos e o contrato editorial;
   devolve JSON conforme `schemas/saida_v1.schema.json`.
5. **Validação (código):** esquema, formato de tempo, durações, limites de caracteres,
   hashtags, citações literais na transcrição, números presentes nas observações de "dados",
   termos de recomendação, sobreposição e cortes consecutivos.
6. **Correção:** se a validação falhar, novo pedido ao LLM com a lista de erros.
7. **Saída:** JSON em arquivo (UTF-8) e modo leitura.
8. **Corte de vídeo (ffmpeg)** e, depois, edição, interface e vídeos longos.

## Provedores de LLM (interface comum)
- `manual`: gera "pacote" `.md` (instruções + dados + formato exato) e lê a resposta colada.
- `gemini` (opcional): API de camada gratuita, chave em `.env`.
- `local` (opcional): Ollama.
Todos passam pelos mesmos validadores. Cache por hash de entrada + versão do prompt.

## Estrutura
```
src/cortesia/   código (esquema, tempo, transcricao, validacao, candidatos, provedores...)
tests/          testes e fixtures (gabaritos)
schemas/        esquema JSON
prompts/        contrato editorial e prompts versionados
docs/           documentação, cartões e modelos
```

## Estado do projeto
Cada vídeo tem uma pasta em `DATA_DIR/projetos/<video_id>/` com `projeto.json` (metadados,
etapa, candidatos, decisões, pendências) e os pacotes/respostas. Qualquer sessão retoma dali.
