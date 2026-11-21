# Estado do sênior (atualizar ao fechar cada tarefa e quando o limite do Claude estiver acabando)

**Atualizado em:** 21/11/2026

## Tarefas
- T00 (ambiente): concluída pelo dono.
- T01 (validador do esquema): FECHADO. Commits `959d0ac` e `f45a25e` verificados (sem arquivos proibidos).
  18 testes. Erros múltiplos reportados com caminho completo.
- T02 (tempo hh:mm:ss.cc): FECHADO. Commits `529f791` e `441feac` verificados. 55 testes no total, ruff limpo.
  Limitação conhecida (aceita): `segundos_para_tempo(True)` devolve "00:00:01.00" (bool é int em Python);
  arredondamento é "half-even" do Python (0.125 vira .12).
- T03 (leitor de transcrição): cartão pronto em `docs/tarefas/T03.md`; é o próximo a enviar ao júnior.
- Depois: ver "Proposta em discussão".

## Proposta em discussão (aguarda decisão do dono)
O dono quer ver a aplicação rodando cedo e dá muita importância à UX. Ainda não há nada visual (só módulos
de validação e tempo). Proposta: reordenar o roadmap para ter um "Revisor de cortes" (UI v0, Streamlit)
logo depois do T03 e do T04:
  T03 leitor de transcrição -> T04 validadores editoriais -> NOVO T05 UI v0 (Revisor) -> pipeline (candidatos,
  provedores, orquestrador) alimentando a mesma UI -> ffmpeg -> Whisper -> vídeos longos.
UI v0: carregar transcrição + colar/abrir o JSON gerado no Claude, validar (usa `esquema.py`), mostrar cortes em
cartões (nota, risco, duração, observações), mostrar o trecho da transcrição, ajustar início/fim, aprovar/rejeitar,
exportar. Antes de codar: escrever `docs/UX.md` (princípios, fluxos, wireframes) e validar com o dono.
Streamlit exige alteração em `requirements.txt` (arquivo protegido): só com aprovação do sênior.

## Decisões recentes (além de DECISOES.md)
- Relatório do júnior deve vir completo, num bloco de quatro crases (workflow ajustado).
- O contrato do júnior manda um commit por tarefa; correções entram como novo commit.
- Tarefas pequenas com assinaturas exatas podem dispensar a aprovação do plano.
- Lições das revisões estão em BRIEFING_SENIOR.md (oneOf, não reduzir listas de erros, regex com fullmatch).

## Pendências do dono
- Confirmar `git status --short` limpo (o ajuste de `.agents/workflows/relatorio-para-senior.md` pode estar sem commit).
- Confirmar que o prompt editorial foi colado em `prompts/contrato_editorial.md`.
- Decidir o nome do projeto (a pasta usa "shortcut", sem o "t").
- Definir a estratégia de direitos autorais (D008) antes de editar vídeos de terceiros.
- Configurar a conta da irmã: projeto no Claude (kit-senior-continuidade) e, depois, o Antigravity.
- Decidir se seguimos com a proposta de UI v0 antecipada.

## Conversa de origem
O histórico completo está na conta do dono; este arquivo e o BRIEFING_SENIOR.md bastam para continuar.
