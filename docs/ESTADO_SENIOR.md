# Estado do sênior (atualizar ao fechar cada tarefa e quando o limite do Claude estiver acabando)

**Atualizado em:** 21/11/2026 (após T04a)

## Tarefas
- T00 (ambiente): concluída.
- T01 (validador do esquema): FECHADO (`959d0ac`, `f45a25e`).
- T02 (tempo hh:mm:ss.cc): FECHADO (`529f791`, `441feac`).
- T03 (leitor de transcrição): FECHADO (`2bca048`, `5acfe08`; rejeita NaN, infinito e start negativo).
- T04a (validadores editoriais I): FECHADO (`b2d64f8`, `6040513`; 25 regras, 114 testes).
  Pendência de verificação: o `tests/test_validacao.py` reforçado não foi relido por mim; conferir junto
  com o relatório do T04b (pedir o arquivo).
- T04b (validadores com transcrição): cartão pronto em `docs/tarefas/T04b.md`; é o próximo a enviar ao júnior.
  Resultado esperado no gabarito: 2 avisos `NUMERO_SEM_DADOS` (2024 em C1, 2026 em C7), nenhum erro.
- Depois: T05 (UX e UI v0). Primeiro eu escrevo `docs/UX.md` e o protótipo; depois o júnior constrói a tela.

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
Decisão do dono: seguir este plano, com a UX logo após o T04.

## Decisões recentes (além de DECISOES.md)
- Relatório do júnior deve vir completo, num bloco de quatro crases (workflow ajustado).
- O contrato do júnior manda um commit por tarefa; correções entram como novo commit.
- Tarefas pequenas com assinaturas exatas podem dispensar a aprovação do plano.
- Lições das revisões estão em BRIEFING_SENIOR.md (oneOf, não reduzir listas de erros, regex com fullmatch, tempos não finitos, sobreposição contra o maior fim).
- O diff salvo pelo PowerShell em arquivo vem com caracteres trocados (codificação do console); não é erro do código.

## Pendências do dono
- Fazer commit de `docs/ESTADO_SENIOR.md` e `docs/BRIEFING_SENIOR.md` (estavam fora do Git).
- Confirmar que o prompt editorial foi colado em `prompts/contrato_editorial.md`.
- Corrigir "shortcut" para "shortcut" nos arquivos de docs (a pasta já foi corrigida).
- Definir a estratégia de direitos autorais (D008) antes de editar vídeos de terceiros.
- Configurar a conta da irmã: projeto no Claude (kit-senior-continuidade) e, depois, o Antigravity.

## Conversa de origem
O histórico completo está na conta do dono; este arquivo e o BRIEFING_SENIOR.md bastam para continuar.
