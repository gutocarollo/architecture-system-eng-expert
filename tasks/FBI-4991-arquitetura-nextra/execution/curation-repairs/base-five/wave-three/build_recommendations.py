import copy
import datetime
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
WORKSPACE = pathlib.Path.cwd()
EXECUTION = WORKSPACE / 'tasks/FBI-4991-arquitetura-nextra/execution'
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
MATRIX = json.loads((EXECUTION/'curation/matrix.json').read_text())
ROWS = {row['concept_id']:row for row in MATRIX['concepts']}
FROZEN_SOURCES = list(json.loads((EXECUTION/'curation/sources.json').read_text()).values())
SHARED = json.loads((EXECUTION/'curation-repairs/sources.json').read_text())
SHARED = SHARED if isinstance(SHARED,list) else list(SHARED.values())
PREVIOUS = json.loads((ROOT.parent/'captures.json').read_text())
CAPTURES = json.loads((ROOT/'captures.json').read_text())
WAVE_TWO = json.loads((ROOT.parent/'wave-two/captures.json').read_text())
ALL_SOURCES = FROZEN_SOURCES + SHARED + PREVIOUS + WAVE_TWO + CAPTURES
LICENSES = {'rails/rails':('MIT-LICENSE','MIT'),'grpc/grpc-go':('LICENSE','Apache-2.0'),'github/scientist':('LICENSE.txt','MIT'),'xataio/pgroll':('LICENSE','Apache-2.0'),'gitlabhq/gitlabhq':('LICENSE','MIT'),'gitlab-org/gitaly':('LICENSE','MIT')}

REPO_RECEIPTS = json.loads((EXECUTION/'curation-repairs/repository-receipts.json').read_text())

def source(repo,path,revision=None):
    matches=[v for v in ALL_SOURCES if v.get('repo')==repo and v.get('path')==path and v.get('http_status')==200 and v.get('artifact') and (revision is None or v.get('revision')==revision)]
    if not matches:raise ValueError((repo,path))
    result=copy.deepcopy(matches[-1])
    raw=(WORKSPACE/result['artifact']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=result['sha256']:raise ValueError(('HASH_MISMATCH',repo,path))
    result.update(kind='FILE',hash_valid=True,cache_inspected_utc=NOW,line_count=len(raw.splitlines()))
    examples=[s for r in MATRIX['concepts'] for role in ['base','application'] for s in r.get(role,[]) if s.get('repo')==repo and s.get('revision')==result['revision'] and s.get('license')]
    if examples:
        result.setdefault('license',copy.deepcopy(examples[0]['license']))
        if examples[0].get('repository_metadata'):result.setdefault('repository_metadata',copy.deepcopy(examples[0]['repository_metadata']))
    if repo in LICENSES:
        license_path,spdx=LICENSES[repo]
        licenses=[v for v in ALL_SOURCES if v.get('repo')==repo and v.get('path')==license_path and v.get('http_status')==200 and v.get('artifact') and v.get('revision')==result['revision']]
        if licenses:
            lic=copy.deepcopy(licenses[-1]);result['license']={**lic,'status':'READ','license_spdx':spdx,'license_text_inspected_utc':NOW}
    if repo in REPO_RECEIPTS:
        meta=REPO_RECEIPTS[repo]
        result['repository_metadata']={k:meta[k] for k in ['stars','observed_utc','archived','pushed_at'] if k in meta}
    if repo=='Kludex/starlette':
        meta=json.loads((ROOT/'starlette-metadata.json').read_text());receipt=json.loads((ROOT/'starlette-metadata-receipt.json').read_text())
        result['repository_metadata']={'stars':meta['stargazers_count'],'observed_utc':receipt['observed_utc'],'archived':meta['archived'],'pushed_at':meta['pushed_at'],'artifact':str((ROOT/'starlette-metadata.json').relative_to(WORKSPACE))}
    return result

def proof(role,record,specifications):
    lines=(WORKSPACE/record['artifact']).read_text().splitlines()
    hits=[]
    for term,start,end in specifications:
        if start<1 or end>len(lines):raise ValueError((record['path'],start,end,len(lines)))
        hits.append({'term':term,'start_line':start,'end_line':end,'excerpt':'\n'.join(lines[start-1:end]),'url':record['url'].split('#')[0]+(f'#L{start}-{end}' if 'gitlab.com/' in record['url'] else f'#L{start}-L{end}')})
    return {'role':role,'source_url':record['url'].split('#')[0],'artifact':record['artifact'],'sha256':record['sha256'],'hits':hits}

def applications(concept):return [source(s['repo'],s['path'],s['revision']) for s in ROWS[concept]['application']]

def recommendation(concept,base,application,mechanism,limits,base_scope,application_scope,evidence,pairing):
    return {'concept_id':concept,'decision':'RECOMMEND_AUTHOR_SOURCE_MATCH_AFTER_REPAIR','independent_review':'PENDING','application_kind':'PRODUCT_OSS','base':base,'application':application,'mechanism':mechanism,'limits':limits,'base_scope':base_scope,'application_scope':application_scope,'source_evidence':evidence,'pairing_relationship':pairing}


rails=source('rails/rails','activerecord/lib/active_record/connection_handling.rb','ba3572c874040cfd6d4883f5ca574121968cdf6f')
database_apps=applications('database-decomposition')
rows=[recommendation(
    'database-decomposition',[rails],database_apps,
    'A decomposição de banco separa os dados de domínios e encaminha cada modelo à conexão correspondente. O Rails implementa connects_to resolvendo a configuração de cada papel e criando os pools associados à classe e ao shard. Quando o modelo pede uma conexão, o framework a busca pelo nome da classe, pelo papel e pelo shard atuais. No GitLab, Ci::ApplicationRecord liga leitura e escrita à conexão ci quando essa configuração existe, e a documentação identifica as tabelas CI como um domínio separado das tabelas main.',
    'O Rails fornece o roteamento entre conexões; ele não escolhe os domínios do GitLab nem executa sozinho a movimentação de dados necessária para decompor um banco. A aplicação pode ser configurada com um, dois ou três bancos, conforme sua documentação. O recorte prova o roteamento lógico por domínio e não mede hosts, instâncias ou configurações de uma implantação específica. A captura do modelo e a captura da documentação estão em commits distintos; elas não são apresentadas como um snapshot de produção. O commit do Rails é uma referência fixa de implementação da API, não uma afirmação sobre a versão de gem instalada no GitLab.',
    'ActiveRecord connects_to resolves each role/shard configuration and creates owner-specific connection pools; connection_pool/retrieve_connection select the corresponding current role/shard pool.',
    'GitLab Ci::ApplicationRecord explicitly routes both roles to :ci, and the primary documentation explains its main/ci/sec database-domain classification.',
    [proof('base',rails,[('concrete connects_to implementation',81,109),('actual connection pool selection',366,372)]),proof('application',database_apps[1],[('CI domain model connection routing',3,12)]),proof('application',database_apps[0],[('upstream explanation of database decomposition',8,22),('CI tables and root classes mapped to domain',25,48)])],
    'GITLAB_USES_RAILS_CONNECTS_TO_API; DISTINCT_FIXED_SOURCE_COMMITS_DO_NOT_ASSERT_INSTALLED_VERSION_OR_DEPLOYMENT'
)]

pgroll='xataio/pgroll'
alter=source(pgroll,'pkg/migrations/op_alter_column.go')
roll=source(pgroll,'pkg/roll/execute.go')
trigger_template=source(pgroll,'pkg/backfill/templates/trigger.go')
function_template=source(pgroll,'pkg/backfill/templates/function.go')
expand_apps=applications('expand-contract')
gitlab='gitlabhq/gitlabhq';gitlab_sha='2b79d1b09471e0f43ace3d37ff417919a5fe7092'
converter=source(gitlab,'lib/gitlab/database/migrations/conversions/bigint_converter.rb',gitlab_sha)
helpers=source(gitlab,'lib/gitlab/database/migration_helpers.rb',gitlab_sha)
trigger_helper=source(gitlab,'lib/gitlab/database/migrations/trigger_helpers.rb',gitlab_sha)
copy_trigger=source(gitlab,'lib/gitlab/database/unidirectional_copy_trigger.rb',gitlab_sha)
expand_apps.extend([helpers,converter,trigger_helper,copy_trigger])
rows.append(recommendation(
    'expand-contract',[alter,roll,trigger_template,function_template],expand_apps,
    'A mudança começa pela ampliação da estrutura, mantém a compatibilidade enquanto os dados são copiados e só depois remove a representação antiga. O pgroll implementa essas fases: duplica a coluna, instala triggers entre as representações, preenche as linhas antigas e oferece uma conclusão que remove a coluna e os auxiliares anteriores. No caso real do GitLab, as migrações de source_xid acrescentam a coluna de transição, agendam backfill em sublotes de 200, exigem sua conclusão, trocam as colunas e chamam a limpeza. O helper e seu conversor mostram como a coluna adicional e o trigger de cópia são criados e depois removidos.',
    'O pgroll e a migração GitLab são referências independentes; o GitLab usa seus próprios helpers neste caso. Os arquivos de expansão e backfill estão em um commit histórico, enquanto a finalização, a troca e a limpeza aparecem em outro. A implementação dos helpers também está fixada e não é apresentada como prova de que seus bytes atuais foram os executados na etapa histórica. Os arquivos comprovam a definição das fases e da compatibilidade, não uma execução realizada nesta sessão. A chamada Complete do pgroll é uma etapa explícita e não prova, por si só, que todos os clientes antigos saíram ou que toda divergência foi reconciliada.',
    'pgroll implements expansion by column duplication and synchronization triggers, ordered backfill, and explicit contraction that removes old storage and migration helpers.',
    'GitLab historical migrations invoke initialization, bounded backfill, completion gate, swap and cleanup; concrete helper -> converter -> copy-trigger implementations establish the actual compatibility mechanism.',
    [proof('base',alter,[('expand physical representation and forward synchronization',34,60),('backward synchronization and backfill task',76,101),('contract old representation and triggers',127,140)]),proof('base',roll,[('install triggers before copying old rows',368,386)]),proof('base',trigger_template,[('trigger runs on real inserts and updates',5,9)]),proof('base',function_template,[('synchronize represented column in the row',17,29)]),proof('application',expand_apps[0],[('historical expansion call',7,15)]),proof('application',expand_apps[1],[('historical bounded backfill call',7,15)]),proof('application',expand_apps[2],[('explicit completion gate',13,18)]),proof('application',expand_apps[3],[('column swap and trigger reset',23,29)]),proof('application',expand_apps[4],[('cleanup and reversal are explicitly defined',6,15)]),proof('application',helpers,[('helper calls implementing converter',451,454),('cleanup calls implementing converter',467,483)]),proof('application',converter,[('create compatibility columns and trigger',31,44),('cleanup removes added columns and trigger',47,68),('actual physical expansion and trigger installation',160,192)]),proof('application',trigger_helper,[('converter trigger API reaches copy trigger implementation',14,22)]),proof('application',copy_trigger,[('actual trigger function and BEFORE INSERT OR UPDATE trigger',16,49),('actual removal of compatibility trigger/function',52,54)])],
    'PARALLEL_IMPLEMENTING_MIGRATION_BASE; GITLAB_HELPERS_ARE_DIRECT_APPLICATION_CODE; HISTORICAL_PHASE_REVISIONS_PRESERVED'
))

scientist=source('github/scientist','lib/scientist/experiment.rb')
observation=source('github/scientist','lib/scientist/observation.rb')
result=source('github/scientist','lib/scientist/result.rb')
parallel_apps=applications('parallel-run')
rows.append(recommendation(
    'parallel-run',[scientist,observation,result],parallel_apps,
    'A execução comparativa aplica os comportamentos antigo e candidato e confronta seus resultados, conservando uma resposta escolhida como autoridade. O Scientist registra os dois comportamentos, executa cada um por meio de Observation e monta um Result que compara os candidatos com o controle. A chamada run() padrão publica as observações e devolve o valor do controle. O GitLab faz esse trabalho em pipelined_both: executa o mesmo pipeline nos dois armazenamentos Redis, registra os resultados diferentes e devolve o resultado do armazenamento padrão.',
    'O paralelismo aqui é lógico: os dois comportamentos são exercitados para comparação; os trechos citados executam as chamadas sequencialmente e não garantem simultaneidade de threads ou processos. Scientist e o MultiStore GitLab são exemplos independentes; não se afirma que o GitLab use Scientist. Os blocos podem produzir efeitos reais, e repetir um bloco não idempotente pode duplicá-los. A comparação depende das entradas, da regra de equivalência e das diferenças ignoradas. Ela não prova equivalência global de todos os comportamentos do produto.',
    'Scientist actually executes each registered behavior, compares candidate observations to control through Result and returns the default control result.',
    'GitLab pipelined_both executes both storage pipelines, observes mismatches and retains default-store response authority.',
    [proof('base',scientist,[('real comparative execution of every behavior',322,333),('publish and preserve control return authority',241,263),('equivalence delegates to actual observation comparator',200,206)]),proof('base',observation,[('behavior block actually executes',26,36)]),proof('base',result,[('control and candidates are established',28,35),('candidate comparisons produce mismatch set',63,75)]),proof('application',parallel_apps[0],[('two executions, mismatch detection and retained authority',439,458)])],
    'PARALLEL_PRIMARY_COMPARATIVE_EXECUTION_EXAMPLES_NOT_A_DEPENDENCY_CLAIM'
))

grpc=source('grpc/grpc-go','server.go','4d4d42843b7154ede87a6cead454ccf8410baea8')
gitaly='gitlab-org/gitaly';gitaly_sha='987854bc5e60a1b9c799eaf7220cb36964cc2356'
protocol=source(gitaly,'proto/operations.proto',gitaly_sha)
generated=source(gitaly,'proto/go/gitalypb/operations_grpc.pb.go',gitaly_sha)
tags=source(gitaly,'internal/gitaly/service/operations/tags.go',gitaly_sha)
gomod=source(gitaly,'go.mod',gitaly_sha)
service_apps=applications('service-extraction')
rows.append(recommendation(
    'service-extraction',[grpc,protocol,generated,tags],service_apps,
    'A extração de serviço precisa de uma fronteira pela qual a aplicação continue pedindo uma operação enquanto outro processo a executa. O gRPC registra o contrato e a implementação de um serviço e entrega a requisição decodificada ao handler. No Gitaly, o contrato declara UserCreateTag, o código gerado encaminha essa chamada a OperationServiceServer e o servidor valida o pedido antes de executar a criação da tag. O cliente GitLab monta esse pedido, seleciona o armazenamento remoto, informa timeout e transforma a resposta no objeto usado pela aplicação.',
    'As fontes demonstram o mecanismo da fronteira remota entre GitLab e Gitaly. Elas não reconstroem a cronologia inteira da extração, não provam que o monólito deixou de executar toda operação Git local e não medem a disponibilidade de um servidor. O gRPC fornece transporte e dispatch; ele não decide a fronteira de negócio nem garante que uma extração tenha sido concluída. Os commits do GitLab, do Gitaly e da biblioteca são referências fixas de código e não uma declaração das versões instaladas em uma implantação. Os links raw de página do Gitaly retornaram 403, mas a API oficial retornou 200; os arquivos foram comparados com os blobs obtidos do mesmo commit pelo protocolo Git e são idênticos.',
    'gRPC registers services and invokes unary handlers. The actual Gitaly protocol, generated dispatch and tag handler implement the remote operation on the service side.',
    'GitLab OperationService creates UserCreateTagRequest/UserDeleteTagRequest and makes storage-specific calls with timeout, preserving its application-facing operation and response shape.',
    [proof('base',grpc,[('concrete service registration',778,812),('receive request invoke implementation send response',1278,1288)]),proof('base',protocol,[('explicit remote tag operation contract',66,85),('request fields cross service boundary',346,364)]),proof('base',generated,[('register actual OperationService descriptor',546,555),('decode request and invoke actual service implementation',611,626)]),proof('base',tags,[('actual service validates and prepares repository operation',124,148),('actual Git reference update',180,184)]),proof('application',service_apps[0],[('real application constructs and calls remote service',22,48)])],
    'GITALY_PROTOCOL_AND_HANDLER_MATCH_GITLAB_OPERATION_NAMES; GRPC_IS_IMPLEMENTING_RPC_BASE; NO_EXTRACTION_HISTORY_OR_DEPLOYMENT_CLAIM'
))
rows[-1]['version_contract']=gomod
rows[-1]['transport_evidence']={'inventory':str((ROOT/'git-captures.json').relative_to(WORKSPACE)),'crosscheck':str((ROOT/'transport-crosscheck.json').relative_to(WORKSPACE)),'primary_api':'https://gitlab.com/api/v4/projects/gitlab-org%2Fgitaly/repository/files/','raw_page_transport_http_status':403,'api_transport_http_status':200,'git_commit':gitaly_sha,'scope':'Primary API captures used as source; Git blobs independently confirm exact captured bytes.'}

transition_apps=applications('transitional-architecture')
rows.append(recommendation(
    'transitional-architecture',[roll,alter,function_template],transition_apps,
    'Uma arquitetura de transição mantém uma ponte temporária enquanto o sistema muda de representação ou de destino. O pgroll cria views em esquemas de versão para conservar o contrato de colunas de cada versão, enquanto os triggers sincronizam as representações físicas. A conclusão remove o esquema da versão anterior e os auxiliares da migração. O MultiStore do GitLab implementa outra ponte temporária: começa no armazenamento antigo, pode executar nos dois, muda o padrão de resposta para o destino e permite desligar a execução dupla permanecendo nele.',
    'pgroll e GitLab são referências independentes de pontes de transição; não há afirmação de dependência entre eles. O código e os comentários do GitLab definem fases e uma saída da execução dupla, mas não provam que uma implantação concluiu essas fases ou retirou a classe MultiStore. No pgroll, o chamador ainda precisa decidir quando os clientes antigos podem perder seu esquema de compatibilidade. A ponte traz custos e efeitos reais enquanto está ativa; sua existência não garante reconciliação de dados nem uma transição concluída.',
    'pgroll builds versioned compatibility views with logical-to-physical column mapping, keeps representations synchronized and explicitly drops the previous version schema during Complete.',
    'GitLab MultiStore documents and implements old-only, dual execution, new default and new-only phases selected by feature flags.',
    [proof('base',roll,[('create version compatibility schema',139,151),('map compatibility columns and create actual view',319,329),('actual version-specific compatibility view SQL',345,361),('explicit removal of old compatibility schema',172,193)]),proof('base',alter,[('keep old and new representations synchronized',48,60),('backward synchronization during coexistence',76,88),('remove obsolete physical representation and helpers',127,140)]),proof('base',function_template,[('version-sensitive synchronization bridge',17,29)]),proof('application',transition_apps[0],[('explicit transition phases and dual-execution exit',163,173),('actual mode selection',204,222),('two flag decisions controlling bridge mode',284,303),('actual response authority selection',331,336)])],
    'PARALLEL_IMPLEMENTING_TRANSITION_BRIDGES; NO_HISTORICAL_OR_PRODUCTION_COMPLETION_CLAIM'
))

frozen_paths=[EXECUTION/'curation/matrix.json',EXECUTION/'curation/matrix.json.gz',EXECUTION/'curation/sources.json']
def frozen_hashes():return {str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen_paths if p.exists()}
frozen_before=frozen_hashes()
payload={'schema_version':1,'recorded_utc':NOW,'workspace':str(WORKSPACE),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'checkout_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'frozen_matrix_sha256':frozen_before['tasks/FBI-4991-arquitetura-nextra/execution/curation/matrix.json'],'frozen_inputs':frozen_before,'purpose':'Wave three final: exactly database-decomposition, expand-contract, parallel-run, service-extraction and transitional-architecture. Curator owns incorporation and independent reviewer owns verdict.','rows':rows,'capture_inventory':str((ROOT/'captures.json').relative_to(WORKSPACE)),'frozen_files_mutated':False,'review_boundary':'Primary-source research only. New writes are confined to base-five/wave-three. No main matrix, gzip, shared source cache, MDX, global repository, Jira, runtime or implementation test was changed.'}
(ROOT/'recommendations.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
refs={s['artifact']:s for r in rows for role in ['base','application'] for s in r[role]};errors=[]
for path,record in refs.items():
    if hashlib.sha256((WORKSPACE/path).read_bytes()).hexdigest()!=record['sha256']:errors.append(path)
for row in rows:
    for ev in row['source_evidence']:
        lines=(WORKSPACE/ev['artifact']).read_text().splitlines()
        for h in ev['hits']:
            if '\n'.join(lines[h['start_line']-1:h['end_line']])!=h['excerpt']:errors.append(h['url'])
frozen_after=frozen_hashes()
receipt={'observed_utc':NOW,'rows':len(rows),'concept_ids':[r['concept_id'] for r in rows],'unique_source_artifacts':len(refs),'hash_or_excerpt_errors':errors,'main_base_http_statuses':sorted({s.get('http_status') for r in rows for s in r['base']}),'main_base_license_statuses':sorted({s.get('license',{}).get('status','MISSING') for r in rows for s in r['base']}),'frozen_before':frozen_before,'frozen_after':frozen_after,'frozen_unchanged':frozen_before==frozen_after,'recommendations_sha256':hashlib.sha256((ROOT/'recommendations.json').read_bytes()).hexdigest(),'scope':'Artifact consistency and transport crosscheck only. No independent semantic review or implementation test.'}
(ROOT/'consistency-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
