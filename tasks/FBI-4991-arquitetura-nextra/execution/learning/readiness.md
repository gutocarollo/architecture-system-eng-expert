# Entrega dos reparos T1, T2 e T3

A frente autora concluiu os reparos materiais e congelou seus quinze casos para a rechecagem independente. O manifesto foi medido em 2026-10-15T02:34:49.328230+00:00, na branch `docs/FBI-4991-arquitetura-aplicada`, com base `23d5d158d3a964dceba296296368ec14bcd8970b`. Ele fixa 165 arquivos e o subconjunto próprio do registro compartilhado. Seu SHA-256 é `a0781e97ce689e4903bda7b0e562707ecbc711df6a8b1f4938b119aaab905727`. Os casos `query-grain-postgres` e `revision-cas-postgres`, assim como `labs/postgres-lineage`, pertencem ao principal e foram excluídos do recorte.

## T1: o mecanismo executado precisa corresponder ao conceito

Os 310 conceitos foram adjudicados individualmente em `mapping_decisions.json` e `concept-matrix.json`. Todos têm uma observação pertinente e nenhuma prática específica permanece PENDING nesta matriz. A frente acrescentou 101 propriedades executáveis nos oito módulos `models_*.py`, além das práticas existentes. Cada entrada publicada mostra sua ação, seu comando, o módulo de origem, os valores esperados e o limite que conserva.

Paxos carrega o valor previamente aceito durante a nova rodada. Raft recusa um prevLogTerm incompatível e repete a partir do prefixo comum. Gossip dissemina conjuntos de membros, sem contar maioria. Stateless Services muda a instância da requisição e conserva a sessão por seu dono externo. Cache Aside carrega e preenche um miss, Negative Caching conserva a ausência, Message Filter retira a entrada inválida, Splitter produz mensagens individuais e A/B entrega respostas visíveis a dois grupos estáveis.

Os exercícios de contexto, linguagem, mapa e relação fornecedor/consumidor alteram um contrato e executam os consumidores que quebram e depois são adaptados. Os modelos organizacionais não se resumem a trocar nomes. Modelos arquiteturais expõem papéis, chamadas, propriedade de dados ou dependências específicas; não afirmam uma arquitetura completa só porque uma função recebe um callback.

O mTLS usa handshakes reais SSLContext por socketpair: aceita o cliente sem certificado no caso de TLS unilateral, recusa-o quando o certificado passa a ser exigido e autentica os dois pares confiáveis. As chaves geradas ficam numa pasta temporária e são removidas. O OpenTelemetry usa o SDK real 1.45.1 e exporta para memória, com traceparent, relação parent/child e um erro. Os demais modelos também delimitam exatamente o que executam; nenhum recebeu uma alegação de implantação ou implementação integral de um protocolo.

## T2: PASS precisa conferir a garantia

`invariants.py` confere todos os campos de before e after contra contratos fixos, separadamente do código que calcula as observações. Os 169 probes financeiros passaram. O teste recusou 629 corrupções de campos e rejeitou o desvio do resultado protegido durante a execução de cada probe. O mutante exato da revisão, que debitava 250 apesar de registrar dois efeitos, agora é recusado.

Os 23 mecanismos de objetos também usam contratos; seus controles recusaram 31 corrupções de campos. Os controles históricos removem shield, renovação antecipada e o ramo de reaproveitamento em cópias temporárias e exigem falha por AssertionError. A prática de data e a de cancelamento continuam mostrando uma cópia anterior que falha, a aplicação do patch e o sucesso na mesma condição. São controles delimitados, sem a alegação de uma campanha exaustiva sobre todo operador de código.

## T3: requisição não é span

A fixture principal registra três spans, duas requisições e uma operação. Uma das duas requisições tem erro, portanto 1 ÷ 2 = 50%. O cálculo também declara uma janela de um segundo e duas requisições por segundo. A propriedade separada do SDK produz dois spans de uma requisição e confere essa distinção nos dados exportados. As saídas publicadas foram regeneradas com esses grãos explícitos.

## Preparação e reprodução

`python3 labs/architecture/setup_labs.py` verifica Python e OpenSSL 3.x, cria apenas `labs/architecture/.venv` e instala `requirements-lock.txt` com cache de download desabilitado. O lock fixa SDK/API 1.45.1, semantic-conventions 0.66b1 e typing_extensions 4.16.0. `otel_probe.py` é chamado explicitamente por essa virtualenv. Nenhuma instalação global do SDK é necessária. Os tutoriais e guias receberam a preparação, e os testes não enviam telemetria a um serviço externo.

A rodada final registrou os resultados abaixo:

- `run_all.py` executou dezesseis runners e todos terminaram com código 0.
- `check_challenges.py` executou os dois desafios, observando código 1 antes, patch com código 0 e código 0 depois.
- `check_invariants.py` executou os 169 probes financeiros, os 23 mecanismos de objetos e os controles negativos descritos acima.
- `check_matrix.py` executou 189 comandos distintos para os 310 vínculos pertinentes e não encontrou falhas. Um comando compartilhado tem seus conceitos consumidores enumerados no recibo.
- `check_mdx.mjs` aceitou 80 páginas do recorte próprio e encontrou 0 falhas. O parsing exclui os dois IDs PostgreSQL reservados ao principal.

Os quatro pares históricos e seus snapshots continuam intactos. O manifest de cada laboratório conserva SHA anterior, SHA posterior, caminhos e hashes. Os dois casos SQL novos são uma integração separada do principal. Os resultados de todos os quinze casos e os contratos ampliados estão atualizados em `families.json`, `receipts.json`, `financial_contracts.json` e `additional-observations.json`; a frente de referência pode regenerar suas tabelas a partir desses artefatos.

A rechecagem T1–T3 e a revisão terminal ainda pertencem a agentes independentes. A frente autora não assina esses veredictos. Nenhum commit, push, deploy ou escrita nos sistemas de origem foi feito por esta frente.
