---
description: Gera o relatório de fim de tarefa para o desenvolvedor sênior revisar
---

1. Rode `ruff check .` e `pytest -q` e guarde a saída completa.
2. Rode `git status --short` e `git diff --stat`.
3. Preencha o modelo `docs/templates/RELATORIO.md` com: tarefa, o que mudou, decisões que
   você tomou, desvios do cartão (se houver), saída do ruff e do pytest, dúvidas.
4. Mostre o relatório preenchido no chat, em um único bloco, pronto para copiar.
5. Não inclua o código-fonte inteiro no relatório; liste apenas os arquivos alterados.
   Se o sênior pedir um arquivo, mostre-o depois.
