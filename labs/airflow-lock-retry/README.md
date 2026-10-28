# Repita a falha elegível do Airflow

Este exercício executa o corpo histórico de `task_run_60_days_rule_hs`, do PR 161 do repositório `fazcapital/airflow`, ligado ao Bug FBI-4797. A versão anterior faz uma chamada. A versão selecionada permite duas novas tentativas somente quando o retorno falha e o stderr contém 55P03.

Use Python 3.11 ou posterior e `patch`, a partir da raiz deste repositório:

```sh
python3 labs/airflow-lock-retry/run.py
python3 labs/airflow-lock-retry/check_challenge.py
```

O segundo comando copia a função anterior para uma pasta temporária, verifica a falha esperada, aplica `source.patch` e executa o mesmo contrato contra a cópia corrigida. O tutorial mostra os comandos manuais em `/tutoriais/casos/airflow-lock-retry/`.

O runner verifica os hashes dos snapshots e executa somente a função selecionada. Ele substitui a conexão, o processo externo, o relógio de espera, a leitura de RSS e o logger por doubles declarados. JSON e escape de URI usam a biblioteca padrão. Nenhum binário, DAG ou conexão de banco real é iniciado por esse programa. A espera é registrada como intenção, com zero segundos de espera real.

Os contratos conferem a falha transitória seguida de sucesso, outro erro, a cota esgotada, um timeout do próprio processo e o sucesso inicial. O runner exige tentativas, esperas e resultado exatos em cada condição.

`manifest.json` conserva os dois SHAs, o hash do arquivo de origem inteiro, o blob e as linhas do recorte. A única normalização é retirar a indentação do wrapper da DAG. Os comentários históricos foram preservados como fonte; suas afirmações sobre o motor Haskell não são certificadas pelo laboratório. Atomicidade, idempotência, RSS real e o bloqueador original continuam fora da prova.

A prática apresenta espera fixa de trinta segundos. Ela não demonstra exponential backoff ou jitter. Três timeouts individuais de trezentos segundos e duas esperas somam um orçamento teórico de 960 segundos, fora overhead; o loop não estabelece um prazo global de dez minutos.
