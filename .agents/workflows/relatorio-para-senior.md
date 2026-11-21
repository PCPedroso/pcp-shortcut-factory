---
description: Gera o relatório de fim de tarefa para o desenvolvedor sênior revisar
---

1. Rode `ruff check .` e `pytest -q` e guarde a saída completa.
2. Rode `git status --short` e `git diff --stat`.
3. Preencha o modelo `docs/templates/RELATORIO.md` com: tarefa, o que mudou, decisões que
   você tomou, desvios do cartão (se houver), saída do ruff e do pytest, dúvidas.
4. Entregue o relatório COMPLETO, do título até "Dúvidas / riscos", em um único bloco de
   código com quatro crases (````markdown ... ````), incluindo as saídas inteiras do ruff e
   do pytest. Não escreva nada do relatório fora desse bloco.
5. Não inclua o código-fonte inteiro no relatório; liste apenas os arquivos alterados.
   Se o sênior pedir um arquivo, mostre-o depois.
