# PostgreSQL: aprenda com dois commits do MakersHub

Os exercícios executam kernels SQL extraídos de quatro revisões imutáveis. As fixtures usam dados sintéticos. O primeiro mostra uma comissão duplicada por uma junção com granularidades diferentes. O segundo mostra uma alteração perdida por um escritor atrasado, mesmo com um índice que permite somente uma versão atual.

Você precisa de Python 3.11 ou posterior, `patch` e dos binários `postgres`, `initdb`, `pg_ctl` e `psql` da mesma instalação PostgreSQL 16 ou posterior no PATH. Não é necessário iniciar um servidor. Execute a partir da raiz do repositório, sequencialmente:

```sh
python3 labs/postgres-lineage/run.py
python3 labs/postgres-lineage/check_challenges.py
```

O segundo comando confirma que cada cópia anterior falha com código 1, aplica o patch a essa cópia e confirma o resultado corrigido com código 0. Os tutoriais apresentam esses passos manualmente.

O runner cria um diretório temporário em `.pg-learning`, inicia PostgreSQL com `listen_addresses=''`, conecta por um socket Unix em uma pasta temporária curta de `/tmp` e verifica o diretório de dados antes das escritas. A configuração não usa endereço de produção. O caminho curto do socket permite executar a prática mesmo quando o caminho do checkout é longo. O servidor é encerrado no bloco de limpeza e os diretórios temporários são removidos. O usuário `learning_operator` pertence somente a esse cluster descartável.

O manifesto registra o SHA da fonte, a função, as linhas e o hash de cada template. Os snapshots `.function.txt` conservam a função completa. Para regenerar a extração, use `python3 labs/postgres-lineage/extract.py --source-repo /caminho/para/makershub`; esse comando opcional exige acesso de leitura ao histórico privado. A execução das práticas usa os snapshots entregues e não precisa desse checkout.

No exercício de granularidade, somente o CTE que descobre familiares é substituído por uma conta sintética. A consulta que vem depois é o kernel histórico. O uso de MAX corresponde à custódia da conta repetida por assessor nesse contrato; ele não serve como regra geral de agregação financeira. O exercício não valida a fórmula de ROA.

No exercício de revisão, o runner usa uma tabela mínima e isola o predicado de encerramento. A alteração concorrente é confirmada entre a leitura e o UPDATE do escritor atrasado. Ele não executa o método inteiro ou a integração Azure. O token baseado em xmin é transitório e não representa uma identidade durável nem um fencing token monotônico.

As jornadas começam em `/jornadas/query-grain-postgres/` e `/jornadas/revision-cas-postgres/`. Os recibos locais ficam em `tasks/FBI-4991-arquitetura-nextra/execution/postgres-learning`.
