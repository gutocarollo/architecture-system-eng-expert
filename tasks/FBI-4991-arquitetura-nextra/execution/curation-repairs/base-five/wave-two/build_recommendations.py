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
ALL_SOURCES = FROZEN_SOURCES + SHARED + PREVIOUS + CAPTURES
LICENSES = {
    'AxonFramework/AxonFramework':('LICENSE.txt','Apache-2.0'),
    'spring-projects/spring-framework':('LICENSE.txt','Apache-2.0'),
    'flippercloud/flipper':('LICENSE','MIT'),
    'fastapi/fastapi':('LICENSE','MIT'),
    'Kludex/starlette':('LICENSE.md','BSD-3-Clause'),
    'apache/airflow':('LICENSE','Apache-2.0'),
    'jellyfin/jellyfin':('LICENSE','GPL-2.0')
}
REPO_RECEIPTS = json.loads((EXECUTION/'curation-repairs/repository-receipts.json').read_text())

def source(repo,path):
    matches=[v for v in ALL_SOURCES if v.get('repo')==repo and v.get('path')==path and v.get('http_status')==200 and v.get('artifact')]
    if not matches:raise ValueError((repo,path))
    result=copy.deepcopy(matches[-1])
    raw=(WORKSPACE/result['artifact']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=result['sha256']:raise ValueError(('HASH_MISMATCH',repo,path))
    result.update(kind='FILE',hash_valid=True,cache_inspected_utc=NOW,line_count=len(raw.splitlines()))
    examples=[s for r in MATRIX['concepts'] for role in ['base','application'] for s in r.get(role,[]) if s.get('repo')==repo and s.get('license')]
    if examples:
        result.setdefault('license',copy.deepcopy(examples[0]['license']))
        if examples[0].get('repository_metadata'):result.setdefault('repository_metadata',copy.deepcopy(examples[0]['repository_metadata']))
    if repo in LICENSES:
        license_path,spdx=LICENSES[repo]
        licenses=[v for v in ALL_SOURCES if v.get('repo')==repo and v.get('path')==license_path and v.get('http_status')==200 and v.get('artifact')]
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
        hits.append({'term':term,'start_line':start,'end_line':end,'excerpt':'\n'.join(lines[start-1:end]),'url':record['url'].split('#')[0]+f'#L{start}-L{end}'})
    return {'role':role,'source_url':record['url'].split('#')[0],'artifact':record['artifact'],'sha256':record['sha256'],'hits':hits}

def applications(concept):return [source(s['repo'],s['path']) for s in ROWS[concept]['application']]

def recommendation(concept,base,application,mechanism,limits,base_scope,application_scope,evidence,pairing):
    return {'concept_id':concept,'decision':'RECOMMEND_AUTHOR_SOURCE_MATCH_AFTER_REPAIR','independent_review':'PENDING','application_kind':'PRODUCT_OSS','base':base,'application':application,'mechanism':mechanism,'limits':limits,'base_scope':base_scope,'application_scope':application_scope,'source_evidence':evidence,'pairing_relationship':pairing}

axon='AxonFramework/AxonFramework'
abstract_repo=source(axon,'modelling/src/main/java/org/axonframework/modelling/command/AbstractRepository.java')
locking=source(axon,'modelling/src/main/java/org/axonframework/modelling/command/LockingRepository.java')
aggregate_model=source(axon,'modelling/src/main/java/org/axonframework/modelling/command/inspection/AnnotatedAggregateMetaModelFactory.java')
aggregate_wrapper=source(axon,'modelling/src/main/java/org/axonframework/modelling/command/inspection/AnnotatedAggregate.java')
aggregate_api=source(axon,'modelling/src/main/java/org/axonframework/modelling/command/Aggregate.java')
repository=source(axon,'modelling/src/main/java/org/axonframework/modelling/command/Repository.java')
child_handler=source(axon,'modelling/src/main/java/org/axonframework/modelling/command/inspection/ChildForwardingCommandMessageHandlingMember.java')
loan=applications('aggregate')[0]
loan_service=source('apache/fineract','fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanApplicationWritePlatformServiceJpaRepositoryImpl.java')
rows=[]
rows.append(recommendation(
    'aggregate',[abstract_repo,locking,aggregate_model],[loan,loan_service],
    'Um agregado reúne uma raiz e os objetos que ela coordena dentro de uma fronteira de consistência. O Axon mantém a instância do agregado na unidade de trabalho, carrega o agregado com um lock configurado e verifica esse lock antes de salvar. Seu modelo executa o tratamento do evento no objeto principal e o propaga aos filhos registrados. No Fineract, Loan reúne encargos, garantias e parcelas. Ao adicionar uma parcela, o próprio Loan associa a parcela ao empréstimo e a inclui em sua coleção; o serviço valida e persiste o Loan na operação de submissão.',
    'Axon e Fineract são exemplos independentes; não se afirma que o Fineract usa Axon. A fronteira de lock demonstrada pertence ao repositório configurado do Axon e à sua unidade de trabalho, não a uma transação distribuída entre serviços. No Fineract, o recorte demonstra composição e operações coordenadas pelo Loan, mas não prova que toda regra do produto ou todo acesso aos filhos passe exclusivamente pela raiz. As anotações JPA descrevem persistência das relações; os métodos e seus chamadores fornecem a prova de comportamento.',
    'Axon manages one root instance per UnitOfWork, obtains and checks a configured aggregate lock, and publishes aggregate events to the root model and registered children.',
    'Fineract Loan owns related components, associates a repayment installment with itself before adding it, and is validated/persisted by the submission service.',
    [proof('base',abstract_repo,[('managed aggregate type and uniqueness within UnitOfWork',93,124)]),proof('base',locking,[('load with aggregate lock through UnitOfWork cleanup',133,143),('save rejects lost aggregate lock',194,208)]),proof('base',aggregate_model,[('root handler and registered child propagation',563,581)]),proof('application',loan,[('related components within Loan',293,310),('root associates and adds child installment',1410,1417)]),proof('application',loan_service,[('real transactional caller validates and persists aggregate',134,145)])],
    'PARALLEL_PRIMARY_DDD_MECHANISM_REFERENCES_NOT_A_DEPENDENCY_CLAIM'
))
rows.append(recommendation(
    'aggregate-root',[aggregate_api,repository,aggregate_wrapper,child_handler],[loan,loan_service],
    'A raiz do agregado é o objeto que identifica o conjunto e recebe a operação que será aplicada nele. O Axon expõe identidade e tratamento de mensagens pelo wrapper Aggregate. A implementação seleciona um handler a partir da raiz e encaminha um comando destinado a um filho somente quando encontra esse filho dentro do agregado; a ausência produz erro. No Fineract, Loan atua como raiz no recorte: seu método de inclusão de parcela ajusta a associação do filho e o incorpora à coleção, e o serviço grava o empréstimo como objeto principal.',
    'A API e a implementação do Axon demonstram uma entrada de mensagens mediada pela raiz e a resolução de filhos dentro dela. Isso não afirma que a linguagem Java impeça todo acesso direto a objetos internos. No Fineract, os métodos citados mostram o papel do Loan nessas operações; eles não provam uma disciplina universal de acesso exclusivo à raiz em todo o produto. Axon é uma referência de framework independente e não uma dependência atribuída ao Fineract. A raiz não é inferida de uma anotação JPA.',
    'Aggregate exposes identity and message handling; AnnotatedAggregate executes handlers against aggregateRoot; child command forwarding resolves the child from that root and rejects missing children.',
    'Loan mediates association of repayment installments and is the submitted object validated and saved by the application service.',
    [proof('base',aggregate_api,[('aggregate identity',49,62),('aggregate message handling boundary',69,81)]),proof('base',repository,[('repository loads aggregate by aggregate identifier',35,59)]),proof('base',aggregate_wrapper,[('message handling executes within aggregate lifecycle',394,405),('handler receives aggregate root',438,454)]),proof('base',child_handler,[('child must resolve within current aggregate',115,126)]),proof('application',loan,[('root association operation',1410,1417),('derived state belongs to Loan',602,612)]),proof('application',loan_service,[('application persists root Loan',134,145)])],
    'PARALLEL_PRIMARY_DDD_MECHANISM_REFERENCES_NOT_A_DEPENDENCY_CLAIM'
))

fastapi_app=source('fastapi/fastapi','fastapi/applications.py')
cors_export=source('fastapi/fastapi','fastapi/middleware/cors.py')
starlette_app=source('Kludex/starlette','starlette/applications.py')
cors=source('Kludex/starlette','starlette/middleware/cors.py')
airflow_apps=applications('chain-of-responsibility')
airflow_core=source('apache/airflow','airflow-core/src/airflow/api_fastapi/core_api/app.py')
access_log=source('apache/airflow','airflow-core/src/airflow/api_fastapi/common/http_access_log.py')
airflow_apps.extend([airflow_core,access_log])
rows.append(recommendation(
    'chain-of-responsibility',[fastapi_app,cors_export,starlette_app,cors],airflow_apps,
    'A cadeia distribui responsabilidades entre componentes que podem encaminhar o pedido ou responder sem continuar. O FastAPI constrói essa cadeia envolvendo o próximo aplicativo em cada middleware. O middleware CORS do Starlette delega os pedidos comuns, mas responde ao preflight de OPTIONS e retorna antes de chamar o próximo componente. A API real do Airflow registra esses middlewares; seu middleware de log captura o envio da resposta e chama o próximo aplicativo ASGI para continuar o processamento.',
    'O FastAPI possui seu próprio build_middleware_stack, por isso a prova usa sua implementação concreta e não presume que ele execute a implementação homônima do Starlette. O módulo CORS do FastAPI reexporta a classe do Starlette. O Airflow registra CORS quando há configuração correspondente; o recorte não demonstra uma configuração ativa, uma requisição de produção ou uma execução de DAG. Os commits das bibliotecas são referências fixas de implementação e não uma medição das versões instaladas em algum ambiente Airflow.',
    'FastAPI builds nested middleware around its router. Starlette add_middleware registers handlers; CORSMiddleware either sends a preflight response and returns or forwards ordinary requests to the next ASGI app.',
    'Airflow API initializes middleware, conditionally installs CORS and uses HttpAccessLogMiddleware whose __call__ delegates to the next application while observing its response.',
    [proof('base',fastapi_app,[('actual FastAPI middleware chain ordering',1067,1078),('each middleware wraps the next app',1102,1105)]),proof('base',cors_export,[('FastAPI uses Starlette CORS implementation',1,1)]),proof('base',starlette_app,[('middleware registration order',104,107)]),proof('base',cors,[('delegate or short circuit preflight',77,91),('ordinary response delegates to next app',145,151)]),proof('application',airflow_apps[0],[('actual application imports FastAPI middleware initializer',26,40),('application invokes initializer',148,160)]),proof('application',airflow_core,[('actual conditional CORS registration',268,276),('actual middleware registration',281,294)]),proof('application',access_log,[('real next-app delegation and response observation',81,109)])],
    'AIRFLOW_IMPORTS_FASTAPI_AND_STARLETTE_APIS; FIXED_SOURCE_COMMITS_DO_NOT_ASSERT_INSTALLED_LIBRARY_VERSIONS'
))

flipper=source('flippercloud/flipper','lib/flipper/feature.rb')
boolean_gate=source('flippercloud/flipper','lib/flipper/gates/boolean.rb')
actor_gate=source('flippercloud/flipper','lib/flipper/gates/percentage_of_actors.rb')
flag_apps=applications('feature-flags')
rows.append(recommendation(
    'feature-flags',[flipper,boolean_gate,actor_gate],flag_apps,
    'Uma flag decide se um caminho de execução está habilitado para um contexto. O Flipper monta o contexto com os valores da flag e seus atores, consulta os gates e devolve verdadeiro quando um deles abre. Os gates citados implementam a habilitação booleana e a seleção determinística de uma porcentagem de atores. O GitLab constrói uma instância Flipper, obtém a flag e consulta enabled?; no MultiStore, duas flags controlam o uso dos dois armazenamentos e a escolha do armazenamento padrão.',
    'O código do GitLab demonstra o uso real do Flipper, mas os commits fixados não identificam a versão de gem instalada em produção. A flag controla um ramo do programa; ela não concede por si só autorização de negócio, não reverte uma escrita Redis já concluída e não garante que os dois armazenamentos tenham o mesmo estado. A regra do GitLab ainda aplica seus defaults e exclusões de atores depois da avaliação do motor.',
    'Flipper::Feature.enabled? constructs FeatureCheckContext and evaluates gate.open?. Boolean and percentage-of-actors gates implement actual decisions rather than marker metadata.',
    'GitLab creates Flipper with application adapters, obtains feature objects, evaluates them and applies the result to real Redis storage selection paths.',
    [proof('base',flipper,[('actual feature evaluation engine',90,111)]),proof('base',boolean_gate,[('concrete boolean gate decision',18,28)]),proof('base',actor_gate,[('concrete actor-percentage gate and stable bucket decision',32,52)]),proof('application',flag_apps[0],[('application calls feature engine and applies actor exclusion',406,420),('feature comes from Flipper instance',431,452),('application creates concrete Flipper engine',472,486)]),proof('application',flag_apps[1],[('real execution paths are gated',284,303),('gate selects the default and nondefault stores',331,336)])],
    'GITLAB_DIRECTLY_USES_FLIPPER_API; SOURCE_COMMITS_DO_NOT_ASSERT_INSTALLED_GEM_VERSION'
))

spring='spring-projects/spring-framework'
context=source(spring,'spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java')
web_context=source(spring,'spring-web/src/main/java/org/springframework/web/context/support/AbstractRefreshableWebApplicationContext.java')
template_apps=applications('template-method')
rows.append(recommendation(
    'template-method',[context,web_context],template_apps,
    'Um método de template organiza uma sequência comum e chama etapas que uma subclasse pode especializar. No Spring, refresh prepara o contexto e o bean factory, chama o hook postProcessBeanFactory e continua com os processadores, os listeners e a inicialização dos objetos. A subclasse web implementa esse hook para registrar recursos do ambiente servlet. No Jellyfin, o fluxo comum de configuração chama a propriedade virtual ConfigurationFileName ao montar o caminho e chama SaveConfiguration durante a atualização ou a criação da configuração padrão.',
    'Spring e Jellyfin são exemplos independentes; não há afirmação de que o Jellyfin use Spring. A prova do padrão está na sequência comum chamando hooks efetivos, e não no nome da classe ou na presença isolada de um método virtual. O recorte do Jellyfin demonstra os pontos de extensão e suas chamadas, sem atribuir a um plugin específico uma implementação que não foi citada. Ele não demonstra Factory Method nem Abstract Factory.',
    'AbstractApplicationContext.refresh invokes overridable postProcessBeanFactory in a fixed initialization sequence. AbstractRefreshableWebApplicationContext actually overrides the hook and registers servlet processors/scopes.',
    'Jellyfin BasePlugin<T> lazy-loads configuration; the common load/update/save paths call virtual filename and save hooks.',
    [proof('base',context,[('common refresh sequence invokes overridable hook',589,606),('common sequence continues after hooks',609,625),('hook contract and default implementation',778,788)]),proof('base',web_context,[('actual subclass specializes invoked hook',146,157)]),proof('application',template_apps[0],[('common configuration getter invokes loader',102,118),('path invokes virtual filename hook',121,131),('common update invokes virtual save hook',157,171),('common loader calls save hook for default configuration',184,198)])],
    'PARALLEL_PRIMARY_TEMPLATE_IMPLEMENTATIONS_NOT_A_DEPENDENCY_CLAIM'
))

payload={'schema_version':1,'recorded_utc':NOW,'workspace':str(WORKSPACE),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'checkout_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'frozen_matrix_sha256':hashlib.sha256((EXECUTION/'curation/matrix.json').read_bytes()).hexdigest(),'purpose':'Wave two: primary-source recommendations for exactly aggregate, aggregate-root, chain-of-responsibility, feature-flags and template-method. Curator owns incorporation; independent reviewer owns verdict.','rows':rows,'capture_inventory':str((ROOT/'captures.json').relative_to(WORKSPACE)),'frozen_files_mutated':False,'review_boundary':'Research/source recommendations only. New writes are confined to base-five/wave-two. No source matrix, shared cache, MDX, gzip, global repository, Jira, runtime or implementation test was changed.'}
(ROOT/'recommendations.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
refs={s['artifact']:s for row in rows for role in ['base','application'] for s in row[role]};errors=[]
for path,record in refs.items():
    if hashlib.sha256((WORKSPACE/path).read_bytes()).hexdigest()!=record['sha256']:errors.append(path)
for row in rows:
    for evidence in row['source_evidence']:
        lines=(WORKSPACE/evidence['artifact']).read_text().splitlines()
        for h in evidence['hits']:
            if '\n'.join(lines[h['start_line']-1:h['end_line']])!=h['excerpt']:errors.append(h['url'])
receipt={'observed_utc':NOW,'rows':len(rows),'concept_ids':[r['concept_id'] for r in rows],'unique_source_artifacts':len(refs),'hash_or_excerpt_errors':errors,'main_base_license_statuses':sorted({s.get('license',{}).get('status','MISSING') for r in rows for s in r['base']}),'frozen_matrix_sha256':payload['frozen_matrix_sha256'],'recommendations_sha256':hashlib.sha256((ROOT/'recommendations.json').read_bytes()).hexdigest(),'scope':'Artifact consistency only; no independent semantic review or implementation test.'}
(ROOT/'consistency-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
