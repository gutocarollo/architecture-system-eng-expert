import copy
import datetime
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
WORKSPACE = pathlib.Path.cwd()
CURATION = WORKSPACE / 'tasks/FBI-4991-arquitetura-nextra/execution/curation'
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
MATRIX = json.loads((CURATION / 'matrix.json').read_text())
ROWS = {row['concept_id']: row for row in MATRIX['concepts']}
CAPTURES = json.loads((ROOT / 'captures.json').read_text())
FROZEN_SOURCES = json.loads((CURATION / 'sources.json').read_text())
ALL_SOURCES = list(FROZEN_SOURCES.values()) + CAPTURES

def find_source(repo, path):
    matches = [value for value in ALL_SOURCES if value.get('repo') == repo and value.get('path') == path and value.get('http_status') == 200 and value.get('artifact')]
    if not matches:
        raise ValueError((repo, path))
    source = copy.deepcopy(matches[-1])
    raw = (WORKSPACE / source['artifact']).read_bytes()
    measured_hash = hashlib.sha256(raw).hexdigest()
    if measured_hash != source['sha256']:
        raise ValueError(('HASH_MISMATCH', repo, path))
    source['cache_inspected_utc'] = NOW
    source['hash_valid'] = True
    source['line_count'] = len(raw.splitlines())
    source['kind'] = 'FILE'
    if source.get('license'):
        return source
    spdx = {'github/scientist':'MIT','open-feature/js-sdk':'Apache-2.0','AxonFramework/AxonFramework':'Apache-2.0','xataio/pgroll':'Apache-2.0','debezium/debezium':'Apache-2.0'}
    if repo in spdx:
        license_path = 'LICENSE.txt' if repo in ['github/scientist','AxonFramework/AxonFramework','debezium/debezium'] else 'LICENSE'
        license_source = next(value for value in reversed(CAPTURES) if value.get('repo') == repo and value.get('path') == license_path and value.get('http_status') == 200)
        source['license'] = {**copy.deepcopy(license_source), 'status':'READ', 'license_spdx':spdx[repo], 'license_text_read_utc':NOW}
    else:
        examples = [value for row in MATRIX['concepts'] for role in ['base','application'] for value in row.get(role,[]) if value.get('repo') == repo and value.get('license')]
        if examples:
            source['license'] = copy.deepcopy(examples[0]['license'])
            if examples[0].get('repository_metadata'):
                source['repository_metadata'] = copy.deepcopy(examples[0]['repository_metadata'])
    metadata_path = ROOT / (repo.replace('/','--')+'-metadata.json')
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        source['repository_metadata'] = {'stars':metadata['stargazers_count'],'archived':metadata['archived'],'pushed_at':metadata['pushed_at'],'observed_utc':next(value['observed_utc'] for value in json.loads((ROOT/'api-captures.json').read_text()) if value['name']==repo.replace('/','--')+'-metadata'),'artifact':str(metadata_path.relative_to(WORKSPACE))}
    return source

def hit(source, term, start, end):
    lines = (WORKSPACE / source['artifact']).read_text().splitlines()
    if start < 1 or end > len(lines):
        raise ValueError((source['path'],start,end,len(lines)))
    base_url = source['url'].split('#')[0]
    return {'term':term,'start_line':start,'end_line':end,'excerpt':'\n'.join(lines[start-1:end]),'url':f'{base_url}#L{start}-L{end}'}

def proof(role, source, specs):
    return {'role':role,'source_url':source['url'].split('#')[0],'artifact':source['artifact'],'sha256':source['sha256'],'hits':[hit(source,*spec) for spec in specs]}

def app_sources(concept_id):
    return [find_source(source['repo'],source['path']) for source in ROWS[concept_id]['application']]

recommendations = []
openfeature = find_source('open-feature/js-sdk','packages/server/src/provider/multi-provider/multi-provider.ts')
first_match = find_source('open-feature/js-sdk','packages/shared/src/provider/multi-provider/strategies/first-match-strategy.ts')
provider = find_source('open-feature/js-sdk','packages/server/src/provider/provider.ts')
branch_apps = app_sources('branch-by-abstraction')
recommendations.append({
    'concept_id':'branch-by-abstraction',
    'decision':'RECOMMEND_AUTHOR_SOURCE_MATCH_AFTER_REPAIR',
    'independent_review':'PENDING',
    'application_kind':'PRODUCT_OSS',
    'base':[openfeature,first_match,provider],
    'application':branch_apps,
    'pairing_relationship':'PARALLEL_PRIMARY_MECHANISM_EXAMPLES_NOT_A_DEPENDENCY_CLAIM',
    'base_scope':'OpenFeature MultiProvider implements the Provider interface, forwards the same evaluation operation to interchangeable providers and selects the final result by a concrete strategy. FirstMatch continues to the next provider only when FLAG_NOT_FOUND is reported.',
    'application_scope':'GitLab Redis MultiStore keeps its Redis command surface while feature flags select default/nondefault storage or enable both stores. Wrapper supplies the pooled call boundary.',
    'mechanism':'O MultiProvider do OpenFeature conserva a interface Provider enquanto consulta implementações selecionadas por uma estratégia. A estratégia FirstMatch tenta a próxima implementação quando a flag não existe na anterior. No caso real do GitLab, MultiStore conserva as operações Redis, e flags escolhem qual armazenamento responde como padrão e quando os dois recebem trabalho. Os chamadores continuam usando a abstração enquanto a seleção da implementação muda.',
    'limits':'A base mostra a substituição de provedores de flags atrás de uma interface; o GitLab mostra a substituição de armazenamentos Redis. Estas são referências independentes do mesmo mecanismo, e não há afirmação de que o GitLab usa o SDK OpenFeature. A interface e a seleção não demonstram paridade de dados entre os armazenamentos nem uma migração concluída. FirstMatch não trata todo erro como motivo para fallback: o avanço demonstrado ocorre em FLAG_NOT_FOUND.',
    'classification_basis':'Pattern correspondence is inferred from the actual common interface, concrete provider dispatch and implementation-selection code; upstream naming alone was not used as proof.',
    'source_evidence':[
        proof('base',openfeature,[('stable evaluation method',119,125),('iterate implementations and select result',164,192),('dispatch through Provider interface',292,306)]),
        proof('base',first_match,[('concrete implementation-selection policy',10,34)]),
        proof('application',branch_apps[0],[('preserved Redis command surface',235,240),('feature-selected migration mode',284,303),('selected default implementation',331,336)]),
        proof('application',branch_apps[1],[('stable pooled caller interface',26,29)])
    ]
})

coordinator = find_source('debezium/debezium','debezium-connector-common/src/main/java/io/debezium/pipeline/ChangeEventSourceCoordinator.java')
snapshot = find_source('debezium/debezium','debezium-connector-postgres/src/main/java/io/debezium/connector/postgresql/PostgresSnapshotChangeEventSource.java')
streaming = find_source('debezium/debezium','debezium-connector-postgres/src/main/java/io/debezium/connector/postgresql/PostgresStreamingChangeEventSource.java')
cdc_apps = app_sources('cdc-migration')
binlog = find_source('julien-duponchelle/python-mysql-replication','pymysqlreplication/binlogstream.py')
package = find_source('julien-duponchelle/python-mysql-replication','setup.py')
package_declaration = hit(package,'primary package license declaration',45,51)
binlog['license'] = {'status':'DECLARED_PRIMARY_PACKAGE_METADATA_NO_LICENSE_TEXT_FOUND','license_declared':'Apache 2','license_spdx_inference':'Apache-2.0','url':package_declaration['url'],'artifact':package['artifact'],'sha256':package['sha256'],'excerpt':package_declaration['excerpt'],'caveat':'Pinned root tree has no license file; API repository metadata returned license=null. Preserve this disclosure. Do not label full license text READ.'}
chameleon_package = find_source('the4thdoctor/pg_chameleon','setup.py')
recommendations.append({
    'concept_id':'cdc-migration',
    'decision':'RECOMMEND_AUTHOR_SOURCE_MATCH_AFTER_REPAIR',
    'independent_review':'PENDING',
    'application_kind':'PRODUCT_OSS',
    'base':[coordinator,snapshot,streaming],
    'application':cdc_apps,
    'supplemental_direct_dependency_sources':[binlog,chameleon_package,package],
    'pairing_relationship':'DEBEZIUM_IS_A_PARALLEL_CDC_FRAMEWORK_EXAMPLE; PG_CHAMELEON_DIRECTLY_IMPORTS_BINLOGSTREAMREADER',
    'base_scope':'Debezium coordinator completes or skips the snapshot and passes its offset to the streaming source. PostgreSQL snapshot captures the WAL starting position; the streaming source consumes the replication stream. This is an implementing CDC framework rather than generic CRUD.',
    'application_scope':'pg_chameleon copies initial tables and resumes MySQL binlog events using log_file/log_pos or GTID and resume_stream=True, then maintains PostgreSQL destination replication state.',
    'mechanism':'O coordenador do Debezium executa o snapshot e, quando ele termina ou é dispensado, passa sua posição à leitura contínua das mudanças. No conector PostgreSQL, essa posição considera o ponto de WAL da transação ou do slot. A ferramenta real pg_chameleon aplica o mesmo princípio em MySQL para PostgreSQL: copia o conjunto inicial e depois lê o binlog desde a posição ou o GTID conservado. O código do leitor BinLogStreamReader, importado pela ferramenta, confirma a retomada desde a posição fornecida.',
    'limits':'Debezium e pg_chameleon são exemplos independentes; o pg_chameleon usa python-mysql-replication, não Debezium. Snapshot e leitura contínua fornecem a base de captura, mas estes recortes não provam reconciliação completa, drenagem final, troca de autoridade da aplicação ou CDC habilitado em algum banco da Faz. O setup.py do pg_chameleon declara mysql-replication>=0.31; ele não fixa uma versão instalada. O leitor suplementar foi consultado em um commit fixo, e sua licença foi encontrada apenas como declaração Apache 2 no setup.py. As três fontes principais do Debezium têm licença Apache-2.0 integral capturada.',
    'source_evidence':[
        proof('base',coordinator,[('snapshot offset flows into streaming',209,227),('streaming executes from supplied offset',333,347)]),
        proof('base',snapshot,[('capture WAL snapshot boundary',194,214)]),
        proof('application',cdc_apps[1],[('initial copy and destination setup',507,528)]),
        proof('application',cdc_apps[0],[('actual BinLogStreamReader import',4,10),('persisted position and resumed row-event consumption',1258,1284)]),
        proof('supplemental_base',binlog,[('replication protocol resumes from caller position',414,444),('stream consumes and decodes replication packets',598,639)]),
        proof('version_contract',chameleon_package,[('dependency declared by real product',48,55)]),
        proof('license_declaration',package,[('primary package license declaration',45,51)])
    ]
})

scientist = find_source('github/scientist','lib/scientist/experiment.rb')
observation = find_source('github/scientist','lib/scientist/observation.rb')
dark_apps = app_sources('dark-launch')
recommendations.append({
    'concept_id':'dark-launch',
    'decision':'RECOMMEND_AUTHOR_SOURCE_MATCH_AFTER_REPAIR',
    'independent_review':'PENDING',
    'application_kind':'PRODUCT_OSS',
    'base':[scientist,observation],
    'application':dark_apps,
    'pairing_relationship':'PARALLEL_PRIMARY_MECHANISM_EXAMPLES_NOT_A_DEPENDENCY_CLAIM',
    'base_scope':'Scientist registers control and candidate behaviors, actually executes them through Observation, publishes comparison information and by default returns control.value.',
    'application_scope':'GitLab sends writes to the storage selected as default and to the nondefault storage while returning only the default result. This is a hidden launch of a storage destination.',
    'mechanism':'Scientist permite executar um comportamento candidato junto com o comportamento de controle. A execução observa os dois, publica o resultado do experimento e, na chamada run() padrão, devolve o valor do controle. No GitLab, o armazenamento secundário recebe uma escrita real antes de assumir a resposta ao chamador: write_both devolve o resultado do armazenamento padrão. Assim, o trabalho novo pode ser exercitado sem escolher seu resultado como resposta principal.',
    'limits':'Scientist e o MultiStore do GitLab são exemplos independentes; não se afirma que esse recorte do GitLab usa Scientist. Scientist executa blocos no mesmo processo e não isola efeitos colaterais. O exemplo não é um teste A/B nem uma interface desligada. O padrão devolve o controle, mas a API também aceita o nome de outro comportamento e uma configuração de divergência pode lançar exceção. No GitLab, o destino secundário recebe efeitos reais, e sua falha é registrada sem tornar as duas escritas atômicas.',
    'source_evidence':[
        proof('base',scientist,[('register control and candidate',291,305),('actually run each registered behavior',322,333),('publish observations and return control value',241,263)]),
        proof('base',observation,[('candidate block is executed and observed',26,36)]),
        proof('application',dark_apps[0],[('default response authority',331,336),('hidden secondary write, default result returned',425,437)])
    ]
})

alter = find_source('xataio/pgroll','pkg/migrations/op_alter_column.go')
trigger = find_source('xataio/pgroll','pkg/backfill/templates/trigger.go')
function = find_source('xataio/pgroll','pkg/backfill/templates/function.go')
roll = find_source('xataio/pgroll','pkg/roll/execute.go')
dual_apps = app_sources('dual-write-migration')
recommendations.append({
    'concept_id':'dual-write-migration',
    'decision':'RECOMMEND_AUTHOR_SOURCE_MATCH_AFTER_REPAIR',
    'independent_review':'PENDING',
    'application_kind':'PRODUCT_OSS',
    'base':[alter,trigger,function,roll],
    'application':dual_apps,
    'pairing_relationship':'PARALLEL_PRIMARY_MECHANISM_EXAMPLES_WITH_DIFFERENT_TRANSACTION_BOUNDARIES',
    'base_scope':'pgroll OpAlterColumn duplicates a column, builds up/down synchronization triggers, backfills existing rows, and Complete drops the old representation and trigger functions and renames the new column. SQL templates show actual BEFORE INSERT/UPDATE synchronization.',
    'application_scope':'GitLab MultiStore writes sequentially to default and nondefault Redis storage and retains the default result. Pipeline comparison exposes divergence; secondary write failures are logged.',
    'mechanism':'O pgroll mantém duas representações de uma coluna durante a migração. A operação cria a coluna nova e triggers que propagam valores em ambos os sentidos; o executor instala os triggers antes de preencher as linhas antigas. A conclusão remove a representação antiga e os auxiliares da migração. O GitLab demonstra a variante em que a aplicação escreve em dois armazenamentos: ela grava no padrão, tenta o secundário e conserva a resposta da primeira gravação.',
    'limits':'O pgroll sincroniza duas representações dentro do PostgreSQL por triggers na alteração da linha. O GitLab faz duas chamadas Redis sequenciais, que podem divergir. São referências independentes, e não uma afirmação de dependência do GitLab em pgroll. A garantia transacional local do trigger não se transfere para duas bases ou serviços separados. O recorte do GitLab registra falha secundária e diferenças de pipeline, mas não fornece reconciliação automática de todas as divergências. A fase Complete do pgroll é explícita; a pesquisa não executou uma migração nem demonstrou um cutover de produção.',
    'source_evidence':[
        proof('base',alter,[('duplicate physical column and add forward synchronization',34,60),('backward synchronization and backfill task',76,101),('complete removes old representation and triggers',127,140)]),
        proof('base',trigger,[('actual insert/update trigger',5,9)]),
        proof('base',function,[('actual conditional second-representation assignment',17,29)]),
        proof('base',roll,[('triggers precede backfill',368,386)]),
        proof('application',dual_apps[0],[('sequential double write and partial failure',425,437),('pipeline divergence is observed without changing authority',439,458)])
    ]
})

repository = find_source('AxonFramework/AxonFramework','modelling/src/main/java/org/axonframework/modelling/command/Repository.java')
abstract_repository = find_source('AxonFramework/AxonFramework','modelling/src/main/java/org/axonframework/modelling/command/AbstractRepository.java')
annotated = find_source('AxonFramework/AxonFramework','modelling/src/main/java/org/axonframework/modelling/command/inspection/AnnotatedAggregate.java')
concrete_repository = find_source('AxonFramework/AxonFramework','modelling/src/main/java/org/axonframework/modelling/command/GenericJpaRepository.java')
factory_apps = app_sources('factory')
assembler = find_source('apache/fineract','fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanAssemblerImpl.java')
service = find_source('apache/fineract','fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanApplicationWritePlatformServiceJpaRepositoryImpl.java')
factory_apps.extend([assembler,service])
recommendations.append({
    'concept_id':'factory',
    'decision':'RECOMMEND_AUTHOR_SOURCE_MATCH_AFTER_REPAIR',
    'independent_review':'PENDING',
    'application_kind':'PRODUCT_OSS',
    'base':[repository,abstract_repository,concrete_repository,annotated],
    'application':factory_apps,
    'pairing_relationship':'PARALLEL_DDD_AGGREGATE_CONSTRUCTION_REFERENCES_NOT_A_FRAMEWORK_DEPENDENCY_CLAIM',
    'base_scope':'Axon Repository.newInstance accepts a factory callable for an aggregate root; AbstractRepository manages construction in a UnitOfWork and rejects an unsuitable aggregate type; AnnotatedAggregate.initialize/registerRoot actually invokes the callable and assigns the root.',
    'application_scope':'Fineract submitApplication invokes LoanAssemblerImpl after request validation. The assembler resolves required product/client/group objects, selects named Loan creation methods, rejects missing client/group association, initializes the schedule, and returns the aggregate. The private Loan constructor associates children and assigns initial state. Additional business validation occurs after assembly and before persistence.',
    'mechanism':'A fábrica concentra uma construção que exige mais do que chamar um construtor vazio. No Axon, newInstance recebe a função que cria a raiz do agregado, executa essa função no ciclo de vida gerenciado e confere se o tipo criado corresponde ao repositório. No Fineract, o serviço de criação chama LoanAssemblerImpl. O montador resolve o produto e as partes do empréstimo, escolhe a criação individual ou em grupo e rejeita o pedido quando não há cliente nem grupo. Os métodos nomeados de Loan chamam um construtor privado que associa os componentes e inicia o empréstimo como submetido e pendente de aprovação.',
    'limits':'Axon fornece o ciclo de construção gerenciada e os controles técnicos do agregado; ele não define as regras de crédito do Fineract. Não se afirma que o Fineract usa Axon. O montador e os métodos de Loan representam a fábrica de domínio neste recorte, enquanto o serviço aplica validações antes e depois da montagem. Portanto, não se atribui a toda chamada direta de um método estático a garantia de satisfazer todas as regras do empréstimo, nem se usa a persistência JPA como prova de Factory.',
    'classification_basis':'The construction responsibility is established by the named creation API, real assembler invocation, private constructor, association initialization and caller validation boundary. A marker annotation, generic bean factory or entity name alone is not used as proof.',
    'source_evidence':[
        proof('base',repository,[('aggregate-specific factory API',61,70)]),
        proof('base',abstract_repository,[('construction failure and type boundary in managed lifecycle',93,121)]),
        proof('base',concrete_repository,[('concrete repository calls aggregate initializer with factory',148,156)]),
        proof('base',annotated,[('aggregate factory initializes real root',205,216),('factory callable is actually executed',276,288)]),
        proof('application',factory_apps[0],[('named domain construction with private constructor',438,454),('private construction and component association',489,526),('initial submitted aggregate state',543,575)]),
        proof('application',assembler,[('required product resolution',163,185),('choose valid association-specific factory or reject',266,296)]),
        proof('application',service,[('real caller validates, assembles, validates and persists',134,145)])
    ]
})

payload = {
    'schema_version':1,
    'recorded_utc':NOW,
    'workspace':str(WORKSPACE),
    'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
    'checkout_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    'frozen_matrix_sha256':hashlib.sha256((CURATION/'matrix.json').read_bytes()).hexdigest(),
    'purpose':'Primary-source investigator recommendations for five assigned HIGH source repairs. Only this subfolder is written; curator owns incorporation and independent reviewer owns verdict.',
    'rows':recommendations,
    'capture_inventory':'tasks/FBI-4991-arquitetura-nextra/execution/curation-repairs/base-five/captures.json',
    'frozen_files_mutated':False,
    'review_boundary':'Research/source recommendations only. No matrix, shared source cache, MDX, gzip, global repository, Jira, production service or implementation test was changed. Candidate adoption still needs curator integration and independent HIGH recheck.',
    'method':'Reused selected application captures and pinned metadata before adding actual framework/library implementations. Every cited raw source was read and its stored SHA256 measured. Base/app references explicitly distinguish a direct dependency from independent examples of the same mechanism.'
}
(ROOT/'recommendations.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'rows':[{'concept_id':r['concept_id'],'base_sources':len(r['base']),'application_sources':len(r['application'])} for r in recommendations],'artifact':str((ROOT/'recommendations.json').relative_to(WORKSPACE)),'frozen_matrix_sha256':payload['frozen_matrix_sha256']},ensure_ascii=False))
