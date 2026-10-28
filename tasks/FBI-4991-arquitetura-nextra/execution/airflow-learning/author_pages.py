"""Publish the source-bound Airflow retry journey with explicit execution limits."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[4]
SLUG='airflow-lock-retry'
TITLE='Uma falha de lock derruba a tarefa do Airflow'
DEST=dict(journey=f'/jornadas/{SLUG}/',explanation=f'/explicacoes/casos/{SLUG}/',tutorial=f'/tutoriais/casos/{SLUG}/',how_to=f'/guias/casos/{SLUG}/',reference=f'/referencia/casos/{SLUG}/')
BEFORE='febaf1be978aad59c29f38d1bd74f357f8e942b5'
AFTER='55dfe8acb362e6854d1af4e7dd7d17e6497af9bd'
PATH='dags/inflow__xp__stg_to_fct.py'
LINKS=f"[Retorne ao caso]({DEST['journey']}), [entenda o mecanismo]({DEST['explanation']}), [aprenda fazendo]({DEST['tutorial']}), [resolva a tarefa]({DEST['how_to']}) ou [consulte o contrato]({DEST['reference']})."
SOURCE=f"Este caso vem do [Bug FBI-4797](https://fazcapital.atlassian.net/browse/FBI-4797) e do [PR 161 do Airflow](https://bitbucket.org/fazcapital/airflow/pull-requests/161). A investigação leu o campo visível `customfield_10047`, o relato do PR e as [versões anterior](https://bitbucket.org/fazcapital/airflow/src/{BEFORE}/{PATH}) e [selecionada](https://bitbucket.org/fazcapital/airflow/src/{AFTER}/{PATH}). O relato registra um timeout de lock; o bloqueador original não foi identificado nessa fonte. O código selecionado é histórico. A prática não mede a versão atualmente implantada."
LIMIT='O laboratório executa a função Python histórica com substitutos locais controlados (doubles). Ele não inicia uma DAG, não executa o binário Haskell, não conecta ao PostgreSQL e não faz esperas reais. A atomicidade e a idempotência do motor Haskell são premissas relatadas pelo PR e continuam fora desta prova. O código procura 55P03 no stderr; isso também não identifica qual consulta segurava o lock.'
OUTPUT='''transient_lock: before_attempts=1 failure=True after_attempts=2 success=True waits=[30]
permanent_error: before_attempts=1 after_attempts=1 failure_preserved=True
lock_budget: before_attempts=1 after_attempts=3 waits=[30, 30] failure_preserved=True
process_timeout: before_attempts=1 after_attempts=1 timeout_preserved=True
comparison=PASS real_subprocesses=0 real_database_connections=0 real_sleep_seconds=0'''

def write(folder,title,kind,body):
 p=ROOT/'content'/folder/SLUG/'index.mdx';p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(f'---\ntitle: {json.dumps(title,ensure_ascii=False)}\ndescription: "Aprenda quando repetir uma falha transitória e quando propagá-la."\ndiataxis: {kind}\n---\n\n# {title}\n\n{body}\n')

write('jornadas',TITLE,'explanation',f'''O pipeline de captação chega à regra de sessenta dias. A função chama um binário e recebe uma falha de espera por lock, identificada por 55P03. A versão anterior derruba a tarefa na primeira falha. A mudança selecionada permite repetir somente essa condição, com uma cota definida. Você vai executar as duas funções e corrigir uma cópia sua.

{SOURCE}

## Escolha seu próximo passo

| Sua necessidade | Destino do mesmo caso | Resultado |
| --- | --- | --- |
| Você quer entender a decisão. | [Explicação]({DEST['explanation']}) | Você distingue falha transitória, limite de tentativas e propagação. |
| Você quer aprender fazendo. | [Tutorial]({DEST['tutorial']}) | Você faz a cópia anterior falhar, aplica o patch e repete os contratos. |
| Você precisa investigar um fluxo semelhante. | [Guia]({DEST['how_to']}) | Você confere o erro elegível, a cota e as premissas da repetição. |
| Você quer consultar nomes e garantias. | [Referência]({DEST['reference']}) | Você encontra a função, os SHAs, os fixtures e os limites. |

## O que muda

Com uma falha 55P03 seguida de sucesso, a função anterior faz uma tentativa e falha; a posterior faz duas e conclui. Um erro 23505 e um timeout do próprio processo continuam falhando na primeira tentativa. Quando 55P03 persiste, a função encerra após três tentativas totais e dois pedidos de espera de trinta segundos.

{LIMIT}''')
write('explicacoes/casos','Por que repetir somente a falha elegível','explanation',f'''{LINKS}

Esperar por um lock pode falhar mesmo quando a mesma operação teria sucesso alguns instantes depois. Repetir automaticamente ajuda nessa situação (retry), desde que a operação possa ser repetida com segurança. A regra histórica não trata toda falha como transitória: ela exige retorno diferente de zero e 55P03 no stderr.

{SOURCE}

## O caminho real da função

A função `task_run_60_days_rule_hs`, em `{PATH}`, monta a conexão, chama `subprocess.run`, interpreta a resposta JSON e acrescenta uma medida de memória (RSS). O patch envolve a chamada externa em um loop. Ele permite duas novas tentativas, com espera fixa de trinta segundos. O código não implementa exponential backoff nem jitter.

```mermaid
flowchart TB
  subgraph B["Antes"]
    B1["Uma chamada ao binário"] --> B2["Retorno de falha"]
    B2 --> B3["RuntimeError encerra a tarefa"]
  end
  subgraph A["Depois"]
    A1["subprocess.run: timeout 300 s"] --> A2{{"Falhou com 55P03 e há cota?"}}
    A1 -->|TimeoutExpired| A7["Falha sem nova tentativa"]
    A2 -->|Sim| A3["Registra tentativa e espera 30 s"]
    A3 --> A1
    A2 -->|Não| A4{{"Retorno é zero?"}}
    A4 -->|Sim| A5["Interpreta JSON e retorna"]
    A4 -->|Não| A6["Propaga RuntimeError"]
  end
```

O desenho descreve o Python histórico. Na prática, a borda do processo e a espera são substituídas por doubles. Um timeout do próprio `subprocess.run` também se propaga, pois não vira um retorno contendo 55P03.

## Por que a cota importa

Três tentativas com limite individual de 300 segundos e duas esperas de 30 segundos representam 3 × 300 + 2 × 30 = 960 segundos, ou 16 minutos, sem contar overhead. A estimativa de aproximadamente cinco minutos apresentada no PR usa durações observadas de cerca de oitenta segundos por tentativa. Ela não é um teto estático de dez minutos. Um prazo total precisa de um orçamento próprio (deadline), que esse loop não estabelece.

## O que a prática não resolve

{LIMIT}

Repetir melhora a tolerância à condição transitória selecionada. Investigar quem segurou o lock é outra tarefa. Se a operação pudesse confirmar efeitos antes da falha, seria necessário tratar essa repetição no desenho de consistência; o retorno diferente de zero, sozinho, não provaria ausência de efeitos.

{LINKS}''')
write('tutoriais/casos','Experimente: repita o erro de lock com uma cota','tutorial',f'''{LINKS}

Você usará Python 3.11 ou posterior e a CLI `patch`. Abra o terminal na raiz deste repositório. Nenhum SDK Airflow, binário Haskell ou servidor de banco é necessário.

## 1. Reconheça a entrada

A primeira sequência contém uma resposta fictícia 55P03 e depois um sucesso. A segunda contém 23505. A terceira repete 55P03 além da cota. A quarta provoca um timeout do processo. Uma quinta sequência começa com sucesso. Todos os valores e a conexão `learning.invalid` são sintéticos.

## 2. Execute as condições históricas

```sh
python3 labs/airflow-lock-retry/run.py
```

A saída esperada é:

```text
{OUTPUT}
```

O pedido de espera de trinta segundos aparece no recibo, mas o double só o registra. Você não precisa aguardar. O PASS exige os cinco contratos; uma mudança qualquer entre dois objetos não é suficiente.

## 3. Faça uma cópia anterior falhar

```sh
learning_retry_dir=$(mktemp -d)
cp labs/airflow-lock-retry/before.py "$learning_retry_dir/candidate.py"
python3 labs/airflow-lock-retry/run.py --candidate "$learning_retry_dir/candidate.py"
```

A última execução deve terminar com código 1 e informar `transient_lock: after violates retry contract`. Sua cópia ainda para na primeira resposta 55P03.

## 4. Aplique o patch histórico

```sh
cat labs/airflow-lock-retry/source.patch
patch -p0 -d "$learning_retry_dir" < labs/airflow-lock-retry/source.patch
python3 labs/airflow-lock-retry/run.py --candidate "$learning_retry_dir/candidate.py"
```

Agora a mesma verificação deve passar com código 0. Abra a cópia e localize a condição `lock_timeout`, a cota `lock_retries` e a espera fixa. Confira também o caminho que continua propagando outro erro.

## 5. Verifique e reinicie

```sh
python3 labs/airflow-lock-retry/check_challenge.py
```

Esse comando automatiza a cópia anterior, a falha esperada, a aplicação do patch e o sucesso posterior. Cada execução cria fixtures novas. Para reiniciar o roteiro manual, crie outra pasta temporária e copie novamente `before.py`; nenhuma limpeza de sistema externo é necessária.

{LIMIT}

{SOURCE}

{LINKS}''')
write('guias/casos','Como conferir se uma falha pode ser repetida','how-to',f'''{LINKS}

Use este guia quando você já entende retry e precisa conferir uma tarefa semelhante. O resultado procurado é uma regra explícita de erro elegível, tentativas e propagação, sustentada pelo efeito da operação.

## Fixe o contrato da repetição

Localize a operação em `{PATH}`, função `task_run_60_days_rule_hs`. Compare os SHAs da referência. Leia a condição que seleciona 55P03; confira o retorno diferente de zero, a cota de duas novas tentativas e os trinta segundos de espera fixa.

## Repita as mesmas condições

```sh
python3 labs/airflow-lock-retry/run.py
python3 labs/airflow-lock-retry/check_challenge.py
```

Conserve controles que falham cedo para outro erro, propagam o timeout do processo e encerram a repetição persistente. O tutorial permite alterar uma cópia e repetir esses contratos.

## Confira as premissas antes de adaptar

Determine onde a operação confirma seus efeitos e por que a mesma intenção pode ser tentada novamente. A premissa de transação atômica relatada no PR precisa ser conferida no motor Haskell e no ambiente relevante antes de autorizar outra operação a seguir a mesma política. Este laboratório não produz essa prova.

Some as tentativas e esperas dentro do prazo total. Repetição em outra camada pode multiplicar o trabalho; o limite deste loop não prova o limite de toda a DAG. Depois, investigue a origem da contenção usando as fontes autorizadas daquele incidente.

{SOURCE}

{LIMIT}

{LINKS}''')
write('referencia/casos','Contrato do retry histórico do Airflow','reference',f'''{LINKS}

| Contrato | Valor selecionado |
| --- | --- |
| Repositório | `fazcapital/airflow` |
| Arquivo | `{PATH}` |
| Função | `task_run_60_days_rule_hs` |
| Versão anterior | `{BEFORE}` |
| Versão selecionada | `{AFTER}` |
| Condição repetida | `returncode != 0` e `55P03` no stderr |
| Cota | Duas novas tentativas, três tentativas totais |
| Espera | Fixa, trinta segundos; sem backoff exponencial ou jitter |
| Timeout | Trezentos segundos por chamada do processo |
| Runner | `python3 labs/airflow-lock-retry/run.py` |
| Desafio | `python3 labs/airflow-lock-retry/check_challenge.py` |

Os snapshots `before.py` e `after.py` conservam o corpo da função, seus comentários históricos e os imports. O normalizador retira somente a indentação do wrapper da DAG. O manifesto registra o hash do arquivo de origem inteiro, seu blob e as linhas selecionadas, além do hash de cada snapshot executável.

O runner injeta `os`, a conexão, o logger e os módulos `subprocess`, `resource` e `time`. JSON e escape de URI continuam usando a biblioteca padrão. A chamada externa recebe argumentos e timeout iguais aos históricos, mas o double retorna as respostas escolhidas; ele não executa processos. Os contratos cobrem erro transitório, erro diferente, cota esgotada, timeout do processo e sucesso inicial.

```text
{OUTPUT}
```

{LIMIT}

O pacote `tasks/FBI-4991-arquitetura-nextra/execution/history/airflow` registra a leitura das fontes e sua divergência de topologia. O censo da fonte declarada tem 914 commits alcançáveis em 155 refs locais; ele não representa todo o histórico remoto nem comprova o estado de produção no Rancher/RKE2.

{SOURCE}

{LINKS}''')
family=dict(case_id=SLUG,title=TITLE,destinations=DEST,kind='historical',lab='labs/airflow-lock-retry/run.py')
(Path(__file__).parent/'families.json').write_text(json.dumps(dict(families=[family]),ensure_ascii=False,indent=2)+'\n')
print('Created five connected Airflow retry MDX destinations.')
