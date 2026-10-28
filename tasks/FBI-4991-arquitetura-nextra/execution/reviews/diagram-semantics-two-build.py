"""Assemble the independent, bounded semantic judgments for lane two."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess

ROOT = Path('/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991')
REVIEWS = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution/reviews'
MAKERS = Path('/Users/augustocarollo/Developer/makershub')
FROZEN = '623ae1d3d34143df53c571327a508de47ab58951'
ASSIGNMENT = REVIEWS / 'diagram-semantic-assignment-two.json'
assignment = json.loads(ASSIGNMENT.read_text())
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
sources = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source(key, path, spans, kind='local source', base=ROOT):
    full = Path(path) if Path(path).is_absolute() else base / path
    raw = full.read_bytes()
    sources[key] = {'path': str(full), 'sha256': sha(raw), 'spans': spans, 'kind': kind}
    if base == MAKERS:
        committed = subprocess.check_output(['git', 'show', f'e233fb046ec333982cd1547171b0f0bd8d8d92ee:{path}'], cwd=MAKERS)
        sources[key]['matches_documented_revision'] = raw == committed
    return key


source('calendar', 'frontend/app/api/calendar/events/route.ts', [[40,81],[93,108],[141,272]], base=MAKERS)
source('insurance-api','backend/app/api/v1/insurance.py',[[46,73]],base=MAKERS)
source('insurance-service','backend/app/services/insurance_service.py',[[19,24]],base=MAKERS)
source('insurance-repo','backend/app/repositories/insurance_repo.py',[[74,112]],base=MAKERS)
source('insurance-hook','frontend/app/(pages)/insurance/_hooks/useInsurance.ts',[[248,259]],base=MAKERS)
source('insurance-manager','frontend/app/(pages)/insurance/_data/InsuranceDataManager.tsx',[[238,240],[406,445]],base=MAKERS)
source('insurance-page','frontend/app/(pages)/insurance/page.tsx',[[40,51]],base=MAKERS)
source('singleflight-current','backend/app/utils/single_flight.py',[[75,154]],base=MAKERS)
source('nextbilling','backend/app/integrations/nextbilling_integration.py',[[198,218]],base=MAKERS)
source('breaker','backend/app/core/task_queue.py',[[127,227]],base=MAKERS)
source('worker','backend/app/core/task_worker.py',[[221,262]],base=MAKERS)
source('api-rate','backend/app/core/api_key_auth.py',[[99,124]],base=MAKERS)
source('slowapi-rate','backend/app/core/rate_limiter.py',[[118,137]],base=MAKERS)
source('idempotency','backend/app/services/idempotency_store.py',[[70,100],[127,173]],base=MAKERS)
source('outbox-flag','backend/app/services/absence_reassignment_service.py',[[337,415]],base=MAKERS)
source('metrics','backend/app/services/metrics_service.py',[[230,319]],base=MAKERS)
source('financial-cache','labs/architecture/financial.py',[[284,302]],'controlled hypothetical model')
source('financial-order','labs/architecture/financial.py',[[65,107]],'controlled hypothetical model')
source('financial-reservation','labs/architecture/financial.py',[[109,140]],'controlled hypothetical model')
source('date-before-card','labs/architecture/date-only/before-card.tsx',[[239,247]],'historical extracted source')
source('date-after-card','labs/architecture/date-only/after-card.tsx',[[241,244]],'historical extracted source')
source('date-helper','labs/architecture/date-only/after.ts',[[7,12],[30,45]],'historical extracted source')
source('date-harness','labs/architecture/date-only/run.mjs',[[18,26]],'controlled harness; read only')
source('early-before','labs/architecture/early-refresh/before.py',[[55,80]],'historical extracted source')
source('early-after','labs/architecture/early-refresh/after.py',[[75,154]],'historical extracted source')
source('early-harness','labs/architecture/early-refresh/run.py',[[9,47]],'controlled harness; read only')
source('opportunity-before','labs/architecture/opportunity-entry/before-integration.py',[[6205,6224]],'historical extracted source')
source('opportunity-after','labs/architecture/opportunity-entry/after-integration.py',[[6811,6826]],'historical extracted source')
source('opportunity-rule','labs/architecture/opportunity-entry/after.py',[[542,580]],'historical extracted source')
source('opportunity-claim','labs/architecture/opportunity-entry/after-qualify.py',[[103,104],[375,378],[2575,2601],[2622,2679],[2982,2986]],'historical extracted source')
source('cancel-before','labs/architecture/single-flight-cancel/before.py',[[55,82]],'historical extracted source')
source('cancel-after','labs/architecture/single-flight-cancel/after.py',[[55,97]],'historical extracted source')
source('cancel-harness','labs/architecture/single-flight-cancel/run.py',[[15,36]],'controlled harness; cancellation injected explicitly')
source('topology-capture','tasks/architecture-course-2026-10-14/evidence/s6-platform.md',[[19,29],[33,45],[88,102]],'dated primary command projections, 2026-10-14 16:10-16:16 UTC')
source('workflow-capture','tasks/architecture-course-2026-10-14/evidence/s3-airflow.md',[[19,21],[39,41],[69,76]],'dated disk-read receipt, 2026-10-14')
source('tut-idempotency','content/tutoriais/idempotency.mdx',[[29,56],[75,79]],'embedded standalone local program')
source('tut-outbox','content/tutoriais/outbox.mdx',[[29,71],[94,98]],'embedded standalone local program')
source('tut-singleflight','content/tutoriais/single-flight.mdx',[[29,112],[134,138]],'embedded standalone local program')

airflow_path = REVIEWS / 'diagram-semantics-two-airflow.json'
airflow = json.loads(airflow_path.read_text())
for key, suffix in [('sf-task','crm__salesforce__api_to_stg__task.py'),('audio','recordings__nextbilling__api_to_stg__audio.py'),('sf-factory','factory.py'),('sf-pipeline','pipeline.py'),('sf-calls','fct_salesforce__calls.sql')]:
    item = next(x for x in airflow['files'] if x['path'].endswith(suffix))
    sources[key] = {k:item[k] for k in ['path','sha256','mtime_utc']}
    sources[key].update(kind='canonical host disk read; no execution',host='airflow-70',observed_at_utc=airflow['observed_at_utc'],spans=[[s['start'],s['end']] for s in item['spans']],capture_path=str(airflow_path),capture_sha256=sha(airflow_path.read_bytes()))

cosmos_path = REVIEWS / 'diagram-semantics-two-cosmos.json'
cosmos = json.loads(cosmos_path.read_text())
sources['cosmos'] = {k:cosmos[k] for k in ['path','sha256','mtime_utc','observed_at_utc']}
sources['cosmos'].update(kind='canonical host disk read; no execution',host='airflow-70',spans=[[1,len(cosmos['source'].splitlines())]],capture_path=str(cosmos_path),capture_sha256=sha(cosmos_path.read_bytes()))

official_path = REVIEWS / 'diagram-semantics-two-official.json'
official = json.loads(official_path.read_text())
for key,value in official['sources'].items():
    sources[key] = dict(value, observed_at_utc=official['observed_at_utc'],capture_path=str(official_path),capture_sha256=sha(official_path.read_bytes()))


def judgment(number, basis, refs, rationale, limit):
    return {'id':f'diagram-{number}','basis':basis,'source_refs':refs,'status':'PASS_BOUNDED','rationale':rationale,'limit':limit}


J = judgment
judgments = [
J(2,'observed source abstraction',['calendar'],'Sessão e token precedem Graph; o ramo sem calendário compartilhado chama getSchedule e transforma a disponibilidade.','O desenho resume o ramo compartilhado; não demonstra permissões, autenticação executada ou implantação.'),
J(4,'dated configuration capture',['topology-capture'],'A captura separa main/git-sync/emptyDir, scheduler único, duas APIs, metadata CNPG e logs configurados.','Só vale para a topologia capturada em 14/10; não acompanha uma task até S3 nem prova failover.'),
J(6,'hypothetical model',[],'O destino aceita 43 e rejeita 42 depois da troca de lease; a conferência está no recurso protegido.','A geração ordenada é premissa da proposta; não é uma garantia conferida nas Leases Kubernetes medidas.'),
J(8,'dated configuration capture',['topology-capture'],'Git-sync e scheduler compartilham emptyDir no pod; a árvore sincronizada fornece os arquivos ao scheduler.','Configuração capturada em 14/10; não representa execução recente, GitOps completo ou igualdade de todo repositório.'),
J(10,'hypothetical model',[],'Cadastro, elegibilidade, disponibilidade e confirmação concorrente aparecem como decisões distintas com recusas próprias.','É proposta explicativa. A proteção concreta da reserva e as regras comerciais não são implementadas pelo desenho.'),
J(12,'hypothetical model',[],'A fronteira local candidata é separada do Salesforce e a retomada reentra por comando validado.','A existência de um Aggregate D1 e sua fronteira transacional permanecem hipóteses explícitas.'),
J(14,'observed source abstraction',['insurance-api','insurance-service','insurance-repo'],'O hit retorna antes do serviço; o miss delega, grava TTL 300 e devolve o resultado; exceções viram erro HTTP.','Não demonstra idade da origem, escopo de autorização completo ou cache efetivamente disponível em produção.'),
J(16,'observed source plus hypothetical cancellation',['singleflight-current','nextbilling','cancel-after'],'O segundo leitor reutiliza _inflight; shield isola cancelamento do awaiter e o callback libera o slot também após erro.','Um processo e uma instância; o cancelamento é condição do cenário, sem afirmar que fechar o browser sempre o cause.'),
J(18,'source-backed conceptual state machine',['breaker','worker'],'O critério de falhas abre o breaker; cooldown permite half-open, e sucesso/falha fecham/reabrem.','A abstração não certifica quota exata de probes, sincronização entre processos ou failover.'),
J(20,'hypothetical model',[],'A classificação direciona trabalhos a pools próprios e a sobrecarga tem recusa ou adiamento explícitos.','Separação proposta; a força do isolamento depende dos recursos realmente reservados, não apenas do desenho.'),
J(22,'source-backed hypothetical policy',['api-rate','slowapi-rate'],'O ramo de indisponibilidade prossegue segundo fail-open; exceder o contador recebe 429 e informação de espera.','A quota 60 é fictícia. Autenticação continua uma condição separada; a disponibilidade do contador não foi executada.'),
J(25,'executable hypothetical model',['financial-cache'],'Chave tenant/consulta, expiração, invalidação e persistência antes da confirmação correspondem aos probes locais.','É uma composição didática de probes independentes, com dicionários locais; não é um trace único nem armazenamento durável real.'),
J(27,'historical extracted source',['date-before-card','date-after-card','date-helper','date-harness'],'O helper distingue a string inteira YYYY-MM-DD e monta componentes locais; timestamps seguem new Date.','Os valores são do cenário São Paulo declarado. Não consulta backend nem prova que o card implantado usa essa revisão.'),
J(29,'historical extracted source',['early-before','early-after','early-harness'],'A janela antecipada inicia tarefa no mesmo slot e devolve valor válido; a expiração dura continua aguardando o produtor.','O harness libera a renovação antes de 1,05; não há promessa de eliminar toda espera nem medição de latência real.'),
J(31,'historical extracted source',['opportunity-before','opportunity-after','opportunity-rule','opportunity-claim'],'Há criação anterior, reaproveitamento por source_opp_id, recusas de estado/tipo e claim por OPP com ator fixo; a liberação aguarda writers.','Os efeitos externos são doubles, e o ciclo final de writers não é executado pelo probe; isso está explicitado no desenho.'),
J(33,'executable hypothetical model',['financial-order'],'O inbox conserva identidade, SQLite registra ordem e intenção na mesma transação e uma ação compensatória recompõe 100.','São probes independentes, não uma saga única executada; o worker é proposto. As três mensagens são ORDER-1, ORDER-1 e ORDER-2.'),
J(36,'executable hypothetical model',['financial-reservation'],'A versão 7 é recusada após o crédito, a releitura produz 900, o destino rejeita 101 e a chave do slot independe do operador.','Modelo local determinístico; as três guardas são probes independentes e não comprovam exclusão entre processos.'),
J(39,'historical source with unsupported transport-cause label',['cancel-before','cancel-after','cancel-harness'],'Shield, callback e quatro sobreviventes têm suporte. A entrada atribui ao FastAPI a causa de cancelamento que o harness injeta explicitamente.','A leitura não prova nem refuta cancelamentos possíveis do FastAPI; só não estabelece essa seta como causa histórica/observada.'),
J(41,'observed source abstraction',['insurance-page','insurance-hook','insurance-manager','insurance-api','insurance-service','insurance-repo'],'A página chama o hook; Promise.all inclui KPI; o miss percorre serviço/repositório/SQL e grava cache 300; erro propaga.','Sequência estática do KPI, sem afirmar uma recuperação completa da interface ou execução recente do SQL.'),
J(43,'hypothetical model',[],'Adaptador HTTP usa a porta de entrada; o caso de uso depende das portas e os adaptadores concretos implementam contratos.','As setas pontilhadas são dependências/implementações propostas, não chamadas observadas nem refatoração já realizada.'),
J(45,'hypothetical model',[],'A ação explícita selectMode percorre controller/model e a view recebe estado ou recusa, preservando o modo.','É comparação MVC didática, sem atribuir essa estrutura ao componente React ou ao seu framework.'),
J(47,'hypothetical model',[],'A view envia ação ao ViewModel, o model decide e o estado observado retorna à apresentação.','Não prova binding implementado, estado compartilhado entre instâncias ou classificação MVVM integral do MakersHub.'),
J(49,'hypothetical model',[],'As duas escolhas válidas incluem auto-transições idempotentes; uma entrada inválida conserva o estado.','O estado inicial Manual pertence ao modelo proposto, sem alegar default de produção ou classes GoF.'),
J(51,'hypothetical model',[],'O recurso registra 102 antes do retorno de A e rejeita 101; expiração de lease e fencing são decisões separadas.','A emissão monotônica e a comparação no destino são premissas declaradas; UUID de ownership local não as estabelece.'),
J(53,'hypothetical model',[],'A consulta de outubro pode evitar outras partições somente se o plano permitir; o armazenamento permanece no mesmo PostgreSQL.','Não afirma particionamento existente, pruning executado ou ganho de desempenho na tabela medida.'),
J(55,'hypothetical model',[],'A entrada de C transfere um intervalo e preserva parte das chaves, com migração e retomada explicitadas.','Não define posições exatas, porcentagem universal, consenso ou membership já implantado.'),
J(57,'vendor-contract conceptual model',['pg-wal'],'A persistência dos registros necessários precede as páginas correspondentes; a recuperação reaplica o que o WAL cobre.','É mecanismo conceitual PostgreSQL 16, sem crash real, política efetiva de commit ou garantia de durabilidade medida.'),
J(59,'vendor-contract hypothetical model',['pg-standby'],'O commit local pode preceder a aplicação remota; a consulta antes da aplicação pode devolver o estado anterior.','A seta de propagação indica envio, não confirmação de aplicação. O aporte e a réplica são hipotéticos.'),
J(61,'source-inspired recovery model',['audio'],'O código separa objeto e metadado; o modelo trata resultado desconhecido por consulta da mesma identidade antes da retomada.','Os estados e as consultas de recuperação são proposta; a DAG não tem essa máquina persistida nem atomicidade entre objeto e SQL.'),
J(63,'hypothetical model',[],'O fato de disponibilidade permite reações independentes; a falha transitória de transcrição retorna ao consumidor.','A publicação durável, o limite de retry e a implantação de consumidores não são demonstrados por este modelo.'),
J(65,'observed local guard plus hypothetical remote failure',['idempotency'],'INSERT/SELECT da identidade e replay done correspondem ao código; a queda entre efeito remoto e finish demonstra o limite da guarda local.','Salesforce e a queda são hipotéticos; claim_or_replay não chama o fornecedor nem prova deduplicação externa.'),
J(67,'hypothetical model',[],'Falhas transitórias seguem orçamento, falhas permanentes/limite vão à quarentena, e replay conserva a identidade.','Não garante transferência atômica para DLQ, autorização implementada ou ausência de efeitos parciais no destino.'),
J(69,'observed source abstraction',['metrics'],'O snapshot ocorre sob lock, o I/O fora dele, os deltas usam bases confirmadas e o avanço acontece depois do commit.','Não certifica agregações não aditivas, flushes simultâneos, retenção ou ausência de commit com resposta ambígua.'),
J(71,'hypothetical model',[],'A versão condiciona append; aporte 1000 menos estorno 200 deriva 800, e replay reconstrói projeções.','A prosa exige comparação/append atômicos. Não há ledger financeiro implantado nem repetição de pagamento no replay.'),
J(73,'vendor-contract proposed model',['pg-refresh'],'A leitura usa conteúdo disponível enquanto REFRESH CONCURRENTLY obedece suas pré-condições; o sucesso renova leituras posteriores.','É proposta PostgreSQL 16, não refresh observado. Falha não atesta frescor, e o modelo não promete atualização incremental.'),
J(75,'observed local write plus proposed relay',['outbox-flag'],'Owner e flag pending mudam na mesma instrução local; o relay proposto conserva intenção e explicita duplicação após aceite remoto.','A flag guarda estado pendente, não cada evento. O destino e a conclusão do lote não foram executados pelo diagrama.'),
J(77,'hypothetical model',[],'Rejeição anterior à liquidação libera a reserva; aceite definitivo é o pivô e falha de comprovante gera retry do aviso.','Não cobre timeout de resultado desconhecido nem implementa devolução automática; a narrativa só resolve os dois resultados explícitos.'),
J(79,'hypothetical model',[],'A expansão mantém aliases de uma fonte única; a contração aguarda ausência observada de leitores antigos.','Não é migração executada. Contagens de consumidores e observação de uso precisam existir antes de aplicar a proposta.'),
J(81,'hypothetical model',[],'De 100 requisições, 90 seguem estável e 10 candidata; critérios controlam retorno ou crescimento.','A amostra delimita requisições, não pessoas; rollback de tráfego não desfaz efeitos anteriores.'),
J(83,'vendor-contract hypothetical model',['entra-oidc'],'Identidade autenticada do cliente e access token da API têm papéis distintos; a política de objeto decide permitir ou negar.','OIDC e nomes são didáticos. A autorização falha fechada no modelo, sem certificar login, política ou transporte implantados.'),
J(85,'canonical disk-source abstraction',['sf-task','sf-factory','sf-pipeline','sf-calls','cosmos','workflow-capture','topology-capture'],'A factory ordena extract/transform/validate/load e cadeia de removidos; staging alimenta o modelo dbt selecionado por Cosmos.','A ligação por tabela é dependência de dados, não ordem de agendamento entre DAGs. O código .70 não certifica toda a paridade do cluster.'),
J(87,'canonical disk source plus proposed failure',['audio','topology-capture'],'A ordem da DAG passa por extração, enriquecimento, stat/put e load_metadata com conflito por nextbilling_call_id.','O ramo de falha SQL é cenário proposto e resume uma tentativa que falhou; não houve upload, SQL ou gravação recente executados nesta revisão.'),
J(89,'embedded controlled simulation',['tut-idempotency'],'A chave e o hash preservam resposta após repetição; outro slot com a mesma chave retorna MISMATCH sem novo efeito.','Memória sequencial local; não prova atomicidade concorrente, persistência ou resposta HTTP real.'),
J(91,'embedded controlled simulation',['tut-outbox'],'O publicador cai depois do efeito e antes da marca; a segunda entrega encontra a identidade no consumidor e marca sent.','A unidade local são duas atribuições em memória; não prova transação durável nem retomada depois de reiniciar o processo.'),
J(93,'embedded controlled simulation',['tut-singleflight'],'Cinco leitores compartilham inflight e shield isola A; em 8 a janela iniciada em 7 renova sem aguardar o valor novo.','A conta de duas buscas é do produtor controlado. Nenhuma latência externa ou coordenação entre workers é demonstrada.'),
]

lookup = {x['id']:x for x in judgments}
assert len(lookup) == len(assignment['items']) == 45
rows = []
for item in assignment['items']:
    d,b = item['diagram'],item['rendered_block']
    p = Path(b['path'])
    raw = p.read_bytes()
    text = raw.decode()
    match = list(re.finditer(r'```mermaid\r?\n(.*?)```',text,re.S))[b['fence_index']-1]
    body = match.group(1)
    doc_hash,body_hash = sha(raw),sha(body.encode())
    assert doc_hash == b['document_sha256'], (d['id'],'document moved during first review')
    assert body_hash == b['source_sha256'], (d['id'],'body moved during first review')
    frozen = subprocess.check_output(['git','show',f'{FROZEN}:{p.relative_to(ROOT)}'],cwd=ROOT)
    assert raw == frozen, (d['id'],'source differs from frozen product/doc HEAD')
    row = dict(lookup[d['id']],document=str(p.relative_to(ROOT)),document_sha256=doc_hash,body_sha256=body_hash,fence_index=b['fence_index'],line_start=b['line_start'])
    if row['basis'].startswith('hypothetical'):
        row['hypothetical_model'] = {'path':row['document'],'span':[max(1,b['line_start']-10),text[:match.end()].count('\n')+10],'sha256':doc_hash}
    row['inspected_sources'] = [{'id':k,'sha256':sources[k].get('sha256',sources[k].get('http_response_sha256')),'spans':sources[k].get('spans'),'url':sources[k].get('url')} for k in row['source_refs']]
    if d['id'] in ['diagram-31','diagram-33','diagram-43']:
        png = Path(b['render']['artifact_path'])
        row['png_inspected'] = {'path':str(png.relative_to(ROOT)),'sha256':sha(png.read_bytes())}
    if d['id'] == 'diagram-39':
        row['status'] = 'HIGH'
        row['finding_id'] = 'DSEM2-H1'
    rows.append(row)

finding = {
    'id':'DSEM2-H1','severity':'HIGH','status':'REPAIR_REQUIRED','diagram':'diagram-39',
    'class':'TESTE/EVIDENCIA','verdict':'NAO-PROVADO for transport cause; REAL support gap',
    'document':'content/explicacoes/casos/single-flight-cancel/index.mdx','lines':[25,26],
    'claim':'Assessor fecha uma consulta -> FastAPI cancela um awaiter',
    'evidence':'cancel-harness:26-36 explicitly executes readers[0].cancel(); cancel-after:55-97 implements consequences after cancellation, not the browser/FastAPI transport bridge.',
    'impact':'The diagram teaches an unestablished transport cause as part of a historical source flow.',
    'fix':'Replace the source trigger/label with an explicit laboratory-injected cancellation, keeping shield/callback/four-survivor relationships.',
    'boundary':'This neither establishes nor denies that FastAPI requests may be cancelled in other conditions.'
}
report = {
    'review':'first independent semantic pass, lane two','reviewer':'/root/diagram_semantics_two',
    'model':'gpt-6.1-sol','native_role':'default','contract':'independent read-only adversarial semantic reviewer',
    'observed_at_utc':now,'product_doc_source_head':FROZEN,
    'execution_metadata_head_at_assembly':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
    'assignment_sha256':sha(ASSIGNMENT.read_bytes()),'scope_count':45,
    'counts':{'PASS_BOUNDED':44,'HIGH':1,'PENDING':0},'verdict':'REPAIR_REQUIRED_DSEM2_H1',
    'scope_limits':['All 45 actual Mermaid bodies and their surrounding prose were read. Approval is semantic and bounded to the identified abstraction.','No code/docs edits, deployment, live business operations, new suite or production fault injection were performed.','CodeGraph was reached on the indexed MakersHub checkout; named Airflow disk sources were read and also traversed through the canonical host CodeGraph.','Primary source claims are bound to file hashes and spans. Configuration diagrams use their explicitly dated captures.','The existing 310-concept OSS curation and already-approved three semantic diagrams are outside this lane.','Context7 was attempted and returned quota exhaustion; four official vendor pages were read directly.'],
    'findings':[finding],
    'backlog':[{'severity':'LOW','diagram':'diagram-33','note':'The node reporting debit 250 summarizes messages ORDER-1(100), ORDER-1(100), ORDER-2(50); naming ORDER-2 in the input would make this arithmetic visible without opening the source.'}],
    'sources':sources,'diagrams':rows,
    'next_step':'Repair only the unsupported transport trigger in diagram-39, then one warm recheck of that material finding at its new document/body hashes; retain the other 44 judgments when their bytes match.'
}
(REVIEWS/'diagram-semantics-two.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md = ['# Revisão semântica independente dos diagramas — lane 2','',
      'O recorte contém 45 diagramas. A revisão aprova 44 com os limites registrados e exige um reparo no diagrama 39. O aceite se refere aos hashes do documento e do corpo Mermaid; ele não certifica implantação ou execução recente.','',
      f'A fonte congelada do produto e dos documentos é `{FROZEN}`. A montagem ocorreu em `{now}`. Os metadados de entrega podem avançar sem alterar estes documentos.','',
      '## Reparo material','',
      'O diagrama 39 apresenta o fechamento da consulta como causa de um cancelamento efetuado pelo FastAPI. O laboratório executa `readers[0].cancel()` em `labs/architecture/single-flight-cancel/run.py:29`. O módulo extraído demonstra o efeito desse cancelamento, o escudo da tarefa e a liberação pelo callback; ele não demonstra a ponte do transporte. Substituir a entrada por um cancelamento explicitamente injetado pelo laboratório fecha a lacuna. Essa conclusão não nega eventuais cancelamentos do FastAPI em outras condições.','',
      '## Julgamentos por diagrama','',
      'Cada referência abaixo aponta para uma fonte efetivamente lida. O JSON contém caminhos, hashes e trechos das fontes, além dos dois hashes de cada diagrama. Nos modelos propostos, a justificativa avalia somente o mecanismo identificado.','']
for row in rows:
    refs=', '.join(row['source_refs']) or 'modelo hipotético identificado no próprio documento'
    md += [f"- **{row['id']} — {row['status']}**. {row['rationale']} Limite: {row['limit']} Fontes: {refs}.",f"  Documento `{row['document']}`: `{row['document_sha256']}`. Corpo: `{row['body_sha256']}`."]
md += ['', '## Evidência e limites','',
       f"- [{now}] `{ROOT}` — leitura de `pwd`, branch e fontes congeladas → branch `{report['branch']}`; 45 documentos/corpos coincidem com a atribuição e com a fonte congelada.",
       f"- [{airflow['observed_at_utc']}] `airflow-70:/home/fazcapital/airflow/airflow-dags` — leitura de bytes e `Path.stat()` → Task `63d2b11a4eb36cb637504cacb0f96808351109799f8e2aad2c8ac89805b4403d`; áudio `0f07f024b88303ed2f07f1343eb45e879591291222706d68916f65f4aeac50ad`; factory `e20a6b8996a672bbd0d514e1ef1b83f9deb7459bd50bd773f0aabd610cfbeb1b`. Os mtimes e trechos completos selecionados ficam no recibo próprio.",
       '- A topologia dos diagramas 4 e 8 permanece limitada à captura de 14/10/2026. A leitura atual dos arquivos do host não a transforma em medição atual do cluster.',
       '- Os PNGs 31, 33 e 43 foram inspecionados para conferir rótulos, ramificações e direção das dependências. A revisão dos demais se baseou no corpo Mermaid e no contexto; a aprovação de renderização preexistente mantém seu próprio escopo.',
       '- A tentativa de Context7 encontrou a quota mensal. O mecanismo de WAL, o refresh concorrente, o atraso de replicação e a separação entre autenticação e autorização foram conferidos nas páginas oficiais registradas no recibo de fontes.',
       '- O diagrama 33 pode explicitar ORDER-2 no rótulo inicial para tornar a soma 100 + 100 + 50 visível. Esse ajuste de clareza fica no backlog.',
       '', 'O próximo passo é reparar a entrada do diagrama 39 e devolver somente esse achado ao mesmo revisor. As outras 44 aprovações permanecem válidas enquanto seus hashes coincidirem.']
(REVIEWS/'diagram-semantics-two.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'counts':report['counts'],'verdict':report['verdict'],'paths':['diagram-semantics-two.json','diagram-semantics-two.md'],'sources_matching_documented_makershub_revision':all(v.get('matches_documented_revision',True) for v in sources.values())},ensure_ascii=False))
