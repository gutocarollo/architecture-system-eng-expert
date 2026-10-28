"""Prepare author recommendations; never edit the frozen matrix."""
import datetime
import hashlib
import json
from pathlib import Path
from evidence_helpers import source

BASE = Path(__file__).resolve().parent
rows = []

def add(concept_id, base, application, mechanism, limits, application_kind='PRODUCT_OSS'):
    rows.append(dict(concept_id=concept_id, decision='AUTHOR_SOURCE_MATCH_REPAIR', independent_review='PENDING',
                     application_kind=application_kind, base=base, application=application,
                     mechanism=mechanism, limits=limits,
                     version_scope='Cada fonte e licença está fixada na revisão indicada. Uma base comparativa não é apresentada como dependência da aplicação sem prova específica.'))

S = source
add('circuit-breaker', [S('resilience4j/resilience4j', 'resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/internal/CircuitBreakerStateMachine.java', [
    (628,630,'O estado fechado registra falhas e verifica o limite.'), (663,667,'A ultrapassagem do limite abre o circuito.'),
    (739,754,'O estado aberto recusa chamadas até passar o prazo e então tenta half-open.'),
    (1188,1194,'O resultado da sondagem fecha ou reabre o circuito.')])], [
    S('mastodon/mastodon','app/services/concerns/search_stoplight.rb',[(3,13,'O produto configura o circuito search:elasticsearch com dez falhas, cinco minutos de recuperação e classes de erro explícitas.')]),
    S('mastodon/mastodon','app/services/tag_search_service.rb',[(3,24,'O serviço de busca tenta Elasticsearch e utiliza o banco quando o resultado é nil.'),(30,36,'A chamada remota passa pelo circuito; RedLight e falhas selecionadas retornam nil para acionar o fallback.'),(116,118,'O fallback executa Tag.search_for no banco.')]),
    S('mastodon/mastodon','config/initializers/stoplight.rb',[(3,9,'O inicializador instala a biblioteca Stoplight com armazenamento Redis do estado do circuito.')])],
    'Na busca de hashtags do Mastodon, a consulta ao Elasticsearch passa por um circuito com limite de dez falhas selecionadas e intervalo de recuperação de cinco minutos. Quando a biblioteca recusa a chamada com RedLight, o serviço consulta o banco. A base Resilience4j mostra separadamente o registro de falhas e as transições fechado, aberto e meio aberto; não é apresentada como biblioteca usada pelo Mastodon.',
    'O recorte é a busca de hashtags quando Chewy está habilitado. A política de contagem do Stoplight não é confundida com a taxa de falha do Resilience4j. O fallback pode devolver resultado e custo diferentes. Nenhuma falha remota nem recuperação foram executadas nesta leitura.')

add('consistent-hashing', [
    S('grafana/dskit','ring/util.go',[(129,139,'A busca binária encontra o primeiro token estritamente maior que a chave e dá a volta ao começo do anel.')]),
    S('grafana/dskit','ring/ring.go',[(497,503,'Get resolve a chave para um conjunto de réplicas.'),(530,543,'O conjunto escolhido é filtrado pela estratégia de saúde.'),(549,559,'A seleção começa no token responsável pela chave.'),(599,619,'A caminhada circular traduz tokens em donos distintos.')])], [
    S('grafana/loki','go.mod',[(61,66,'O Loki fixa Dskit no pseudo-version que resolve ao SHA b6a53f6bee29 selecionado como base.')]),
    S('grafana/loki','pkg/util/ring/ring.go',[(11,16,'A chave do stream é derivada do tenant e dos labels por FNV de 32 bits.')]),
    S('grafana/loki','pkg/distributor/distributor.go',[(599,607,'O caminho sem subdivisão adicional calcula HashKey para o stream.'),(948,972,'O distribuidor consulta ingestersRing.Get(HashKey) e agrupa os streams pelos endereços dos donos.')])],
    'O Loki transforma tenant e labels em uma chave de 32 bits e pede ao anel os ingesters responsáveis. O Dskit procura o token seguinte por busca binária, percorre o anel com retorno ao início e escolhe donos distintos para as réplicas. Assim, a seleção usa posições estáveis no anel em vez de apenas calcular um hash sem resolver seu dono.',
    'O recorte é o caminho de ingestão por ingesters quando habilitado, sem confundir a alternativa Kafka/partition-ring. Saúde, fator de replicação e zonas podem ampliar ou filtrar os donos. A propriedade local do anel não é uma medição de balanceamento nem de percentual de dados movidos.', 'INFRASTRUCTURE_OSS')

add('distributed-cache', [
    S('pallets-eco/cachelib','src/cachelib/redis_base.py',[(40,53,'Leitura e escrita usam um cliente Redis compartilhado pelo backend.'),(72,93,'get lê a chave no Redis; set serializa o valor e escreve no Redis com expiração.')]),
    S('pallets-eco/flask-caching','src/flask_caching/backends/rediscache.py',[(14,21,'O backend Flask-Caching herda a implementação Redis do Cachelib.'),(69,104,'A fábrica usa host, banco, prefixo e URL configurados para construir o cliente Redis.')])], [
    S('apache/superset','docker/pythonpath_dev/superset_config.py',[(65,79,'A configuração Docker do produto escolhe RedisCache e usa a mesma configuração para o cache de dados.')]),
    S('apache/superset','superset/utils/cache_manager.py',[(200,210,'A configuração de cache é selecionada para inicializar o backend.'),(234,239,'DATA_CACHE_CONFIG inicializa o cache de dados do aplicativo.')]),
    S('apache/superset','superset/common/utils/query_cache_manager.py',[(39,42,'A região DATA aponta para cache_manager.data_cache.'),(175,198,'Uma consulta tenta ler o resultado pelo backend e trata falha como miss.'),(254,270,'A escrita de resultados usa o backend da região selecionada.')]),
    S('apache/superset','superset/utils/cache.py',[(110,119,'set_and_log_cache realmente chama cache_instance.set e trata uma recusa explícita do backend.')])],
    'Na configuração Docker selecionada do Superset, o cache de resultados usa RedisCache. O gerenciador inicializa esse backend, e as consultas leem e gravam resultados pela região DATA. O backend Redis do Flask-Caching/Cachelib resolve essas operações em GET/SET no servidor Redis; processos com a mesma URL, banco e prefixo podem compartilhar o mesmo valor.',
    'A prova vale para a configuração Docker capturada e para processos configurados com o mesmo namespace Redis. Não afirma que toda instalação Superset usa Redis nem que este backend está ativo no MakersHub. Revisões das bibliotecas são exemplos fixados do mecanismo; não houve resolução ou execução do lockfile dessa instalação.')

add('refresh-ahead', [
    S('google/guava','guava/src/com/google/common/cache/LocalCache.java',[(2361,2378,'Após o intervalo de refresh, uma leitura dispara atualização se outra carga não estiver em andamento e pode devolver o valor anterior.')]),
    S('google/guava','guava/src/com/google/common/cache/CacheLoader.java',[(185,202,'asyncReloading executa reload no executor e devolve um futuro.')])], [
    S('trinodb/trino','lib/trino-metastore/src/main/java/io/trino/metastore/cache/CachingHiveMetastore.java',[(159,168,'O produto transmite TTL e intervalo de refresh para a fábrica do cache de metadados.'),(203,207,'A tabela usa um cache carregado por loadTable.'),(429,437,'getTable lê o cache, e seu carregador consulta o metastore delegado.'),(1130,1153,'A implementação ativa refreshAfterWrite e asyncReloading apenas quando o refresh ocorre antes da expiração ou quando não há expiração.')])],
    'O Trino pode atualizar metadados do Hive em segundo plano antes de seu TTL terminar. O construtor só habilita refresh se o intervalo for menor que o prazo de expiração, e envolve o carregador com asyncReloading. Uma leitura de uma entrada elegível dispara a carga; o valor anterior pode continuar atendendo enquanto a atualização termina.',
    'Este é refresh antecipado disparado por acesso, não um agendador que atualiza todas as chaves. Se a chave não for consultada, ela pode expirar. O ramo não é ativado quando o intervalo de refresh é maior ou igual ao TTL; falhas de carga não tornam o dado automaticamente atual.', 'INFRASTRUCTURE_OSS')

add('single-flight', [S('golang/sync','singleflight/singleflight.go',[(121,141,'DoChan registra uma chamada por chave; duplicatas entram no mesmo conjunto de canais.'),(198,200,'A execução compartilhada invoca fn uma vez e guarda valor e erro para os clientes.')])], [
    S('grafana/loki','pkg/dataobj/metadatacache/cache.go',[(116,145,'Após um miss, DoChan agrupa por chave e inicia uma carga com timeout independente do cancelamento de um cliente.'),(145,166,'O resultado da única carga é armazenado quando permitido e devolvido ao grupo.'),(168,175,'Cada cliente recebe o mesmo resultado pelo canal ou encerra pela própria espera cancelada.')]),
    S('grafana/loki','pkg/dataobj/decoder.go',[(69,91,'O decoder real solicita a região de metadados ao cache e usa os bytes para decodificar o objeto.')])],
    'No leitor de objetos de dados do Loki, misses concorrentes para a mesma região de metadados entram em Group.DoChan com a mesma chave. Uma carga lê o objeto e devolve seus bytes para todos os clientes que continuam esperando. O decoder consome esse resultado em sua leitura real de metadados.',
    'O agrupamento é local à instância do Group; não é uma exclusão global entre processos. O cancelamento de um cliente não cancela a carga compartilhada, que tem seu próprio timeout. Depois que a chamada termina, uma nova falta pode executar outra carga; erros de cache podem fazer a operação recorrer ao armazenamento.', 'INFRASTRUCTURE_OSS')

add('thread-pool', [S('python/cpython','Lib/concurrent/futures/thread.py',[(97,122,'Workers persistentes retiram itens de uma fila e executam trabalhos sucessivos.'),(199,238,'submit enfileira um trabalho; o executor reutiliza threads ociosas ou cria até max_workers.')])], [
    S('apache/nutch','src/java/org/apache/nutch/fetcher/Fetcher.java',[(231,265,'Um conjunto configurado de FetcherThread compartilha fetchQueues; cada worker é iniciado uma vez.'),(408,415,'O produto pode ampliar o conjunto quando a política de largura de banda pede mais workers.'),(428,435,'O conjunto também pode diminuir por sinalização de parada.')]),
    S('apache/nutch','src/java/org/apache/nutch/fetcher/FetcherThread.java',[(304,334,'Cada worker permanece no loop e busca o próximo item na fila compartilhada.'),(357,365,'O item é consumido pelo protocolo real de coleta de páginas.')])],
    'O coletor do Nutch inicia um conjunto de threads que compartilham a fila de URLs. Cada thread busca um item, executa a coleta pelo protocolo adequado e volta ao loop para o próximo trabalho. O tamanho inicial vem da configuração e pode ser ajustado pela política de largura de banda. O ThreadPoolExecutor do CPython oferece uma base comparativa com fila, reutilização e limite de workers.',
    'O Nutch implementa seu próprio conjunto de workers Java; não usa o executor Python. A quantidade inicial não é uma garantia de concorrência útil nem de throughput. Filas por host, robots.txt, delays e threads bloqueadas ainda limitam o progresso.', 'INFRASTRUCTURE_OSS')

packet = dict(schema_version=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              frozen_matrix_sha256='a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e',
              purpose='Recomendações autorais para seis HIGH; nenhuma aprovação independente.', rows=rows,
              independent_review='PENDING', frozen_files_mutated=False)
path=BASE/'cache-and-concurrency-recommendations.json'
path.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(rows=len(rows),sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
