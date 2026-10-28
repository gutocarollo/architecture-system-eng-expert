"""Create two source-derived PostgreSQL learning journeys."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CASES = [
 dict(case_id='query-grain-postgres', case='grain', title='A comissão de R$ 100 aparece como R$ 200',
      issue='FBI-4604', pr=507, status='MERGED', before='b1df42295ce42d593ae14f0a8a9092c28d1b410d', after='05b2cacdddd59b968641b12d8d124bad1888392f',
      path='backend/app/repositories/account.py', function='get_family_revenue_by_period',
      story='Um gestor consulta a receita de uma família. A consulta anterior associa uma comissão por conta e mês a duas linhas de assessores. A comissão de R$ 100 aparece duas vezes. O exercício usa uma conta fictícia e repete a consulta histórica no PostgreSQL para tornar essa multiplicação visível.',
      result='A versão anterior retorna duas linhas e soma R$ 200. A versão alterada retorna uma linha e soma R$ 100. A custódia do exemplo continua em R$ 1.000.000.',
      mechanism='A informação precisa ter uma unidade bem definida antes da junção (granularidade). O lado de comissão contém uma linha por conta e mês. O lado anterior de ROA pode conter uma linha por conta, mês e assessor. Associar os dois lados replica a comissão para cada assessor. A versão selecionada agrupa a custódia por conta e mês antes da junção.',
      changes='Localize `roa_per` no arquivo anterior. No patch, acompanhe sua substituição por `custody_per`, a leitura de `rpt_advisor__roa_pj1`, o agrupamento por mês e conta e a seleção de `MAX(r.net_assets_amount)`. A prática executa esse SQL; ela não deduplica a resposta no Python.',
      limit='O uso de MAX depende do contrato deste recorte: a custódia da conta está repetida por assessor. MAX não é uma receita geral para somar patrimônios distintos. O exercício isola a cardinalidade da junção e não valida a fórmula financeira de ROA nem o caminho completo da tela.',
      invariant='Uma conta e um mês produzem uma linha com comissão total de R$ 100; a junção não pode alterar essa soma.',
      output='grain: before_rows=2 before_commission=200 after_rows=1 after_commission=100',
      diagram='flowchart LR\n  C["Comissão: conta 101, mês janeiro, R$ 100"] --> J["Junção por conta e mês"]\n  R["Duas linhas de assessores"] --> J\n  J --> B["Antes: duas linhas, R$ 200"]\n  R --> G["Agrupar custódia por conta e mês"]\n  G --> A["Depois: uma linha, R$ 100"]\n  C --> A'),
 dict(case_id='revision-cas-postgres', case='revision', title='Uma única versão atual ainda pode perder uma alteração',
      issue='FBI-4924', pr=630, status='OPEN na leitura histórica registrada', before='3ad846049c32fedee09d458c8d685fb39b675b82', after='c5e8efc5913355a8545b8a27b8b72e0828f77660',
      path='backend/app/repositories/employee_repository.py', function='update_employee_scd2_without_commit',
      story='Dois escritores trabalham sobre o mesmo colaborador. O primeiro lê a linha atual. O segundo confirma uma alteração em azure_id. O primeiro ainda conserva a leitura antiga e tenta encerrar a versão para criar outra. Ter somente uma versão atual não impede que essa nova versão recoloque o valor antigo.',
      result='A versão anterior termina com uma única linha atual, mas perde AZURE-CONFIRMED e conserva AZURE-OLD. O predicado alterado rejeita o escritor atrasado e preserva AZURE-CONFIRMED. Os identificadores deste exercício são sintéticos.',
      mechanism='A gravação só pode prosseguir quando a revisão ainda é a mesma que o escritor leu (concorrência otimista, com comparação de versão). A versão selecionada compara a combinação de _employee_id com xmin. Se outro escritor alterou a linha, o UPDATE não encerra nenhuma versão. O chamador precisa tratar esse resultado como conflito e reler antes de decidir novamente.',
      changes='Compare o predicado do UPDATE nos dois templates. A alteração acrescenta a comparação com `:source_revision` e devolve as linhas encerradas com `RETURNING _employee_id`. O exercício produz a alteração concorrente antes desse UPDATE e verifica o valor preservado.',
      limit='A revisão baseada em xmin é opaca e transitória. Ela não é uma identidade durável nem um fencing token monotônico. O laboratório isola o predicado de encerramento, com uma atualização concorrente entre leitura e escrita; não executa o método inteiro, a API ou a integração Azure. O commit selecionado pertence a um PR cuja leitura histórica estava aberta; este material não afirma implantação em produção.',
      invariant='O escritor atrasado não encerra a linha modificada e AZURE-CONFIRMED permanece na única versão atual.',
      output='revision: before_current_rows=1 lost_azure_update=True after_current_rows=1 stale_writer_rejected=True',
      diagram='sequenceDiagram\n  participant A as Escritor A\n  participant P as PostgreSQL\n  participant B as Escritor B\n  A->>P: Ler valor e revisão\n  B->>P: Gravar AZURE-CONFIRMED\n  A->>P: Encerrar versão com revisão antiga\n  P-->>A: Zero linhas encerradas\n  Note over A,P: A precisa reler, e o valor confirmado permanece')
]


def links(item):
    slug = item['case_id']
    return f'[Retorne ao caso](/jornadas/{slug}/), [entenda o mecanismo](/explicacoes/casos/{slug}/), [aprenda fazendo](/tutoriais/casos/{slug}/), [resolva a tarefa](/guias/casos/{slug}/) ou [consulte o contrato](/referencia/casos/{slug}/).'


def source(item):
    return f"Este recorte está ligado ao [card {item['issue']}](https://fazcapital.atlassian.net/browse/{item['issue']}) e ao [PR {item['pr']}](https://bitbucket.org/fazcapital/makershub/pull-requests/{item['pr']}). A leitura histórica registrou o PR como **{item['status']}**. Compare a [fonte anterior](https://bitbucket.org/fazcapital/makershub/src/{item['before']}/{item['path']}) com a [fonte alterada](https://bitbucket.org/fazcapital/makershub/src/{item['after']}/{item['path']}). A investigação conserva as descrições de PR e do campo visível do Jira em `execution/history`; o laboratório verifica somente o kernel SQL selecionado."


def emit(folder, slug, title, kind, body):
    target = ROOT / 'content' / folder / slug / 'index.mdx'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f'---\ntitle: {json.dumps(title, ensure_ascii=False)}\ndescription: "Uma experiência com SQL histórico e um PostgreSQL descartável."\ndiataxis: {kind}\n---\n\n# {title}\n\n{body}\n')


for item in CASES:
    slug, case = item['case_id'], item['case']
    common = links(item)
    emit('jornadas', slug, item['title'], 'explanation', f"{item['story']}\n\n{source(item)}\n\n## Escolha seu próximo passo\n\n| Sua necessidade | Destino deste caso | Resultado |\n| --- | --- | --- |\n| Você quer entender a decisão. | [Explicação](/explicacoes/casos/{slug}/) | Você reconhece o mecanismo e seu limite. |\n| Você quer aprender fazendo. | [Tutorial](/tutoriais/casos/{slug}/) | Você faz uma cópia falhar, aplica o patch e repete o contrato. |\n| Você precisa investigar outro fluxo. | [Guia](/guias/casos/{slug}/) | Você confere a mesma garantia em uma consulta semelhante. |\n| Você procura nomes e parâmetros. | [Referência](/referencia/casos/{slug}/) | Você consulta os caminhos, as entradas e os limites. |\n\n## O que você observará\n\n{item['result']}\n\n{item['limit']}")
    emit('explicacoes/casos', slug, 'Por que acontece: ' + item['title'], 'explanation', f"{common}\n\n{item['story']}\n\n{item['mechanism']}\n\n```mermaid\n{item['diagram']}\n```\n\n## O que muda no código\n\nA função estudada é `{item['function']}`, em `{item['path']}`. {item['changes']}\n\n{item['result']}\n\n## Até onde essa conclusão vale\n\n{item['limit']}\n\n{source(item)}\n\n{common}")
    tutorial = f"""{common}

Você fará a mesma consulta com uma cópia anterior e uma cópia corrigida. O objetivo desta experiência é verificar: {item['invariant']}

## 1. Prepare o ambiente

Abra o terminal na raiz deste repositório. Você precisa de Python 3.11 ou posterior, da CLI `patch` e dos programas PostgreSQL 16 ou posterior no PATH. O recibo desta execução usou PostgreSQL 16.15. Os binários precisam pertencer à mesma instalação. Não é necessário ter um servidor iniciado.

```sh
python3 --version
postgres --version
initdb --version
psql --version
pg_ctl --version
```

O runner cria um banco descartável dentro de `.pg-learning`, escuta somente em socket Unix local e confirma o diretório de dados antes de executar as fixtures. Ele não usa credenciais ou endereços de produção. Execute os exercícios sequencialmente.

## 2. Veja as duas condições

```sh
python3 labs/postgres-lineage/run.py --case {case}
```

Você deve encontrar a saída abaixo. PASS significa que o problema esperado apareceu antes e que o invariante delimitado foi respeitado depois.

```text
{item['output']}
comparison=PASS isolation_verified=True temporary_server_stopped=True
```

{item['result']}

## 3. Comece com uma cópia que ainda falha

```sh
mkdir -p .pg-learning/{case}-challenge
cp labs/postgres-lineage/{case}-before.sql.template .pg-learning/{case}-challenge/candidate.sql
python3 labs/postgres-lineage/run.py --case {case} --candidate-{case} .pg-learning/{case}-challenge/candidate.sql
```

A última execução deve terminar com código 1 porque sua cópia ainda produz o efeito incorreto. Leia o erro do invariante. Não interprete essa falha esperada como uma indisponibilidade do banco.

## 4. Examine e aplique a alteração

{item['changes']}

```sh
cat labs/postgres-lineage/{case}.patch
patch -p0 -d .pg-learning/{case}-challenge < labs/postgres-lineage/{case}.patch
python3 labs/postgres-lineage/run.py --case {case} --candidate-{case} .pg-learning/{case}-challenge/candidate.sql
```

Agora a execução deve terminar com código 0. A entrada e a verificação continuam iguais; quem mudou foi a sua cópia da consulta. Abra `candidate.sql` e localize a operação responsável por preservar o invariante.

## 5. Conclua e repita

O runner encerra e remove seu servidor descartável em cada execução. Sua cópia editável permanece em `.pg-learning/{case}-challenge`. Para repetir do início, copie novamente o template anterior para ela antes de aplicar o patch.

{item['limit']}

{source(item)}

{common}
"""
    emit('tutoriais/casos', slug, 'Experimente: ' + item['title'], 'tutorial', tutorial)
    emit('guias/casos', slug, 'Como investigar: ' + item['title'], 'how-to', f"{common}\n\nUse este guia quando você já entende o mecanismo e precisa conferir uma consulta semelhante. Seu resultado procurado é: {item['invariant']}\n\n## Fixe a fonte e a condição\n\nRegistre o SHA, a função e os valores de entrada. Comece pelo kernel `{item['function']}` em `{item['path']}`. Reproduza com dados sintéticos em um banco descartável; preserve as descrições de PR e Jira como contexto, separadas da prova de execução.\n\n## Verifique a garantia\n\n```sh\npython3 labs/postgres-lineage/run.py --case {case}\n```\n\n{item['changes']}\n\nTroque somente a cópia candidata e repita o mesmo invariante. O tutorial apresenta o roteiro editável completo. Para conferir automaticamente os dois desafios, use `python3 labs/postgres-lineage/check_challenges.py`.\n\n## Decida o que pode concluir\n\n{item['result']}\n\n{item['limit']}\n\nAntes de adaptar a mudança a outro fluxo, confirme o contrato dos dados e os chamadores desse fluxo. O resultado local não substitui essa investigação.\n\n{source(item)}\n\n{common}")
    reference = f"""{common}

| Contrato | Valor deste recorte |
| --- | --- |
| Caso | `{slug}` |
| Função | `{item['function']}` |
| Arquivo de origem | `{item['path']}` |
| SHA anterior | `{item['before']}` |
| SHA selecionado | `{item['after']}` |
| Runner | `python3 labs/postgres-lineage/run.py --case {case}` |
| Candidato editável | `--candidate-{case} caminho/candidate.sql` |
| Fonte dos hashes | `labs/postgres-lineage/manifest.json` |
| Patch | `labs/postgres-lineage/{case}.patch` |
| Garantia | {item['invariant']} |

O arquivo `{case}-before.sql.template` e seu correspondente posterior contêm o SQL extraído da árvore sintática da fonte. Os snapshots `.function.txt` conservam a função completa. Os valores financeiros e identidades das fixtures foram inventados para a experiência.

O runner substitui os parâmetros por literais controlados. No caso de granularidade, substitui somente o CTE de descoberta de familiares por uma conta sintética; a consulta posterior a esse CTE conserva o SQL selecionado. No caso de revisão, usa uma tabela mínima descartável com os mesmos nomes de colunas do predicado. As tabelas mínimas não reproduzem o esquema inteiro do MakersHub.

## Saída delimitada

```text
{item['output']}
comparison=PASS isolation_verified=True temporary_server_stopped=True
```

A comparação padrão devolve código 0. Um candidato que ainda infringe o contrato devolve código 1. Uma dependência ausente ou SQL inválido também impede a conclusão; é preciso ler o erro antes de atribuí-lo ao mecanismo.

{item['limit']}

{source(item)}

{common}
"""
    emit('referencia/casos', slug, 'Contrato: ' + item['title'], 'reference', reference)

registry = [dict(case_id=item['case_id'], title=item['title'], destinations=dict(journey=f"/jornadas/{item['case_id']}/", explanation=f"/explicacoes/casos/{item['case_id']}/", tutorial=f"/tutoriais/casos/{item['case_id']}/", how_to=f"/guias/casos/{item['case_id']}/", reference=f"/referencia/casos/{item['case_id']}/")) for item in CASES]
(Path(__file__).parent / 'families.json').write_text(json.dumps(dict(families=registry), ensure_ascii=False, indent=2) + '\n')
print('Created ten connected MDX pages for two source-derived PostgreSQL cases.')
