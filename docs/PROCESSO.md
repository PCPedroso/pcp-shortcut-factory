# Processo de trabalho (sênior, júnior e dono do projeto)

Papéis
- **Sênior (Claude):** escreve cartões de tarefa, decide a arquitetura, revisa relatórios e diffs.
- **Júnior (agente do Antigravity):** planeja, implementa e testa dentro do escopo do cartão.
- **Dono do projeto:** leva cartões ao júnior e relatórios ao sênior, e decide as prioridades.

Ciclo de cada tarefa
1. O sênior entrega o cartão (`docs/tarefas/Txx.md`).
2. O dono cola o cartão no Antigravity e pede **o plano primeiro**.
3. Tarefas médias ou grandes: o dono cola o plano para o sênior aprovar antes de implementar.
4. O júnior implementa, roda `ruff` e `pytest` e executa `/relatorio-para-senior`.
5. O dono cola ao sênior: o relatório e, se pedido, o `git diff` ou arquivos específicos.
6. O sênior aprova ou devolve correções objetivas. Aprovado: um commit por tarefa.

Para economizar limites
- Cole só o necessário: relatório + diff enxuto, nunca o projeto inteiro.
- Uma tarefa por conversa no Antigravity; ao terminar, abra uma nova.
- Se o limite da conta acabar, outra pessoa continua com os mesmos arquivos do repositório:
  `docs/BACKLOG.md` (estado), o cartão da tarefa e o último relatório.

Regras de ouro
- Testes primeiro. Sem teste, a tarefa não está pronta.
- Mudou prompt, esquema ou gabarito? Só com aprovação do sênior e registro em `DECISOES.md`.
- Dúvida editorial (contexto, atribuição, risco) é decisão humana + sênior, não do júnior.
