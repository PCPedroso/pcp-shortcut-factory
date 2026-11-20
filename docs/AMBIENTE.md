# Ambiente de desenvolvimento

PC do dono do projeto: Windows 64 bits, Intel Core i5-9400F (6 núcleos), 32 GB de RAM,
GTX 1650 de 4 GB, SSD de 112 GB (provável disco do sistema) e SSD de 447 GB.

Implicações (a validar por benchmark quando chegarmos lá)
- **Disco:** código no SSD de 447 GB; `DATA_DIR` também lá. Evitar o de 112 GB.
- **Transcrição local (faster-whisper):** começar por modelos pequenos/médios em modo
  quantizado (int8), que devem caber nos 4 GB de VRAM. O modelo "large" provavelmente não
  cabe com folga; testar antes de decidir. Há opção de rodar na CPU (mais lento).
- **LLM local (Ollama):** só modelos pequenos, para tarefas auxiliares. O julgamento
  editorial fica com Claude (modo manual) ou com provedores de API.
- **Vídeo (ffmpeg):** a GTX 1650 tem encoder NVENC; testar para acelerar exportações.
- **Memória:** 32 GB é folgado para transcrições longas e cache.
