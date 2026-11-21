# pcp-shorcut-factory: mineração de cortes (híbrido)

Aplicação local que transforma a transcrição de vídeos longos em candidatos a cortes, com
validação por código e uso de LLM apenas onde o julgamento editorial é necessário.

> Mantenha este repositório **privado**: ele contém a transcrição de um vídeo de terceiros
> usada como teste (`tests/fixtures/`).

## Como começar (Windows)

1. Instale (uma vez):
   - **Python 3.12** em python.org, marcando "Add python.exe to PATH".
   - **Git** em git-scm.com.
   - **ffmpeg**: no PowerShell, `winget install Gyan.FFmpeg` (feche e reabra o terminal;
     confira com `ffmpeg -version`).
2. Coloque esta pasta no **SSD de 447 GB** (ex.: `D:\Repository\pcp-shortcut-factory`), não no de 112 GB.
3. Abra a pasta no Antigravity (File > Open Folder).
4. No terminal da IDE:
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -U pip
   pip install -r requirements.txt
   pytest
   ```
   Se o PowerShell bloquear o script de ativação:
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo.
   O `pytest` deve mostrar **3 testes passando** (essa é a tarefa T00).
5. `git init`, depois `git add .` e `git commit -m "kit inicial"`.
6. Copie `.env.example` para `.env` e ajuste `DATA_DIR`.
7. **Cole o seu prompt editorial original** em `prompts/contrato_editorial.md`
   (veja o aviso dentro do arquivo).
8. No Antigravity, abra *Customizations > Rules* e confirme que a regra
   `00-contrato-junior` está ativa para este workspace (se a interface oferecer, use
   "Always On"). Em *Workflows*, confirme `/relatorio-para-senior`.
9. Leia `docs/PROCESSO.md` e envie a primeira tarefa, `docs/tarefas/T01.md`, ao agente.

## Mapa

- `GEMINI.md` e `.agents/`: regras e workflows do agente "júnior".
- `docs/`: arquitetura, decisões, backlog, processo, cartões de tarefa e modelos.
- `prompts/`: contrato editorial e prompts (versionados).
- `schemas/`: esquema JSON da saída.
- `src/cortesia/`: código. `tests/`: testes e gabaritos.
