from pathlib import Path
import copy
import datetime
import hashlib
import json
import subprocess


ROOT = Path("tasks/FBI-4991-arquitetura-nextra/execution")
OUTPUT = ROOT / "curation-repairs/rare-runtime"
REVIEW = ROOT / "reviews/curation-second.concepts.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


sources = {}
for receipt_path in sorted(OUTPUT.glob("*.receipt.json")):
    source = json.loads(receipt_path.read_text())
    data = Path(source["artifact"]).read_bytes()
    assert digest(data) == source["sha256"], source["artifact"]
    assert len(data.splitlines()) == source["line_count"]
    sources[(source["repo"], source["revision"], source["path"])] = source

licenses = {}
cached_licenses = json.loads((ROOT / "curation/revision-licenses.json").read_text())
for repo, revision in [
    ("temporalio/temporal", "10791698da3708020fe52db8af1b4bef89db3177"),
    ("apache/hadoop", "6f3d71bc35f5eaab0487283533e6057c58038ae4"),
    ("trinodb/trino", "5706548dade9b1dc81144af6850c5dde9a356713"),
]:
    item = copy.deepcopy(cached_licenses[f"{repo}@{revision}"])
    data = Path(item["artifact"]).read_bytes()
    assert digest(data) == item["sha256"]
    destination = OUTPUT / (repo.replace("/", "--") + "--license-cache.txt")
    destination.write_bytes(data)
    item["cache_artifact"] = item["artifact"]
    item["artifact"] = str(destination)
    item["reuse"] = "Existing pinned license bytes were copied after checking their SHA-256."
    licenses[f"{repo}@{revision}"] = item

TEMPORAL = ("temporalio/temporal", "10791698da3708020fe52db8af1b4bef89db3177")
HADOOP = ("apache/hadoop", "6f3d71bc35f5eaab0487283533e6057c58038ae4")
TRINO = ("trinodb/trino", "5706548dade9b1dc81144af6850c5dde9a356713")
AIRLIFT = ("airlift/airlift", "2fd0bb60d560a511403957d79931f5915adced44")
COSMO = ("wundergraph/cosmo", "4879bb547802dae3b1e35f71e6a8af2165c01009")
TOOLS = ("wundergraph/graphql-go-tools", "4d20fae7080021bc08cd2d4602747ad600326ead")

for project, spdx in [(AIRLIFT, "Apache-2.0"), (COSMO, "Apache-2.0"), (TOOLS, "MIT")]:
    license_path = "v2/LICENSE" if project == TOOLS else "LICENSE"
    source = copy.deepcopy(sources[(*project, license_path)])
    source["license_spdx"] = spdx
    source["scope"] = "The selected v2 files are covered by their nearest v2/LICENSE (MIT)." if project == TOOLS else "Root license covers selected non-demo paths; the complete pinned tree has no nearer license in their ancestor directories."
    licenses["@".join(project)] = source


def evidence(project, path, ranges, role, proves):
    source = copy.deepcopy(sources[(*project, path)])
    lines = Path(source["artifact"]).read_text().splitlines()
    source["role"] = role
    source["proves"] = proves
    source["inspected_ranges"] = ranges
    source["excerpts"] = []
    for start, end in ranges:
        assert 1 <= start <= end <= len(lines), (path, start, end, len(lines))
        source["excerpts"].append({
            "start_line": start,
            "end_line": end,
            "url": f'{source["url"]}#L{start}-L{end}',
            "text": "\n".join(f"{line + 1}: {lines[line]}" for line in range(start - 1, end)),
        })
    return source


T = "service/history/hsm/"
N = T + "nexusoperations/"
H = "hadoop-hdfs-project/hadoop-hdfs/src/main/java/org/apache/hadoop/hdfs/server/namenode/"
R = "core/trino-main/src/main/java/io/trino/"
A = "opentelemetry/src/main/java/io/airlift/opentelemetry/"
G = "v2/pkg/engine/datasource/graphql_datasource/"

fsm_evidence = [
    evidence(TEMPORAL, T + "sm.go", [[18, 24], [31, 66]], "base", "A base genérica registra origens, destino e evento; Possible verifica o estado atual e Apply rejeita uma transição inválida antes de trocar o estado."),
    evidence(TEMPORAL, "proto/internal/temporal/server/api/enums/v1/nexus.proto", [[7, 27]], "finite_control_states", "O enum da operação Nexus tem oito estados de controle, incluindo UNSPECIFIED e quatro estados terminais."),
    evidence(TEMPORAL, N + "statemachine.go", [[45, 89], [245, 289], [298, 332], [364, 367]], "application", "A operação do servidor instancia a base: UNSPECIFIED vai a SCHEDULED, uma falha recuperável vai a BACKING_OFF, o retry volta a SCHEDULED e o início assíncrono vai a STARTED."),
    evidence(TEMPORAL, N + "workflow/commands.go", [[238, 258]], "real_command_bridge", "O handler do comando ScheduleNexusOperation registra o evento e aplica ScheduledEventDefinition à HSM do workflow."),
    evidence(TEMPORAL, N + "events.go", [[19, 29], [174, 187], [203, 218]], "event_dispatch", "Os eventos de agendamento, início e conclusão aplicam a transição da operação, em vez de apenas reconstruir um snapshot."),
    evidence(TEMPORAL, N + "executors.go", [[421, 429], [452, 480], [568, 575], [606, 612]], "runtime_bridge", "A resposta pending de uma chamada real a Nexus provoca TransitionStarted; erro recuperável provoca TransitionAttemptFailed e o executor de backoff aplica TransitionRescheduled."),
    evidence(TEMPORAL, N + "fx.go", [[8, 19]], "registration", "O módulo do servidor registra máquinas, eventos e executor."),
]

concepts = []
for identifier in ["finite-state-machine", "state-machine"]:
    concepts.append({
        "concept_id": identifier,
        "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
        "independent_review": "PENDING",
        "base_role": "Temporal HSM é a infraestrutura genérica de transições dentro do servidor.",
        "application_role": "Temporal Server é o produto OSS real; a aplicação escolhida é a máquina de uma operação Nexus, e não todo o motor de workflows.",
        "mechanism": "Uma operação Nexus nasce no estado UNSPECIFIED. O comando de agendamento aplica uma transição para SCHEDULED. Se a chamada falha de forma recuperável, o executor muda o controle para BACKING_OFF; o timer de retry pode devolvê-lo a SCHEDULED. Uma resposta assíncrona muda o controle para STARTED, e um evento de conclusão permite SUCCEEDED. Cada transição declara suas origens aceitas. A base testa o estado atual e devolve ErrInvalidTransition quando a origem não está na lista.",
        "review_gap_addressed": "A nova seleção mostra enum finito, origens e destino, guarda, mutação e callers reais de comandos, eventos e executor.",
        "limits": [
            "A finitude demonstrada é a dos oito estados de controle. Payload, tentativas e timestamps são dados adicionais; não se afirma que todo o espaço de configuração do serviço seja finito.",
            "A base genérica aceita S comparable e, sozinha, não exige um conjunto finito. O enum Nexus e suas transições fornecem esse recorte.",
            "Não se deduz GoF State desse enum. Também não se afirma atomicidade de persistência a partir de Apply: a função troca o estado antes de chamar o callback, que pode retornar erro.",
        ],
        "licenses": ["@".join(TEMPORAL)],
        "evidence": copy.deepcopy(fsm_evidence),
        "official_context": [{"url": "https://docs.temporal.io/nexus/operations", "scope": "Documentação primária do ciclo de vida Nexus; o código fixado acima é a prova do mecanismo."}],
    })

concepts.append({
    "concept_id": "state",
    "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
    "independent_review": "PENDING",
    "base_role": "HAState é a classe abstrata de comportamento por estado usada pelo HDFS; não é um framework GoF separado.",
    "application_role": "O daemon NameNode do Apache HDFS mantém e troca instâncias concretas de HAState.",
    "mechanism": "O NameNode guarda um campo HAState que pode conter ActiveState ou StandbyState. O contexto encaminha checkOperation para o objeto atual. ActiveState aceita operações, enquanto StandbyState recusa as operações que não passam pelas condições de leitura permitida. Ao trocar de estado, HAState executa a saída do objeto atual, atualiza o objeto guardado pelo contexto e chama a entrada do próximo objeto. O comportamento muda pela delegação ao mesmo contrato abstrato.",
    "review_gap_addressed": "Há contexto, objeto atual intercambiável, contrato comum, implementações distintas e transição com enter/exit, satisfazendo a delegação pedida para State.",
    "limits": ["A interpretação GoF vale para o subsistema de alta disponibilidade do NameNode. As fontes chamam HAState de base para state machine; não se atribui ao projeto uma declaração textual de adesão ao catálogo GoF.", "StandbyState também representa observer mediante uma flag; o exemplo didático deve se limitar a ativo e standby e preservar a exceção de leituras obsoletas permitidas."],
    "licenses": ["@".join(HADOOP)],
    "evidence": [
        evidence(HADOOP, H + "ha/HAState.java", [[27, 32], [56, 69], [102, 103], [127, 152]], "base", "A classe abstrata declara comportamento comum e controla a substituição do estado no contexto com saída e entrada."),
        evidence(HADOOP, H + "NameNode.java", [[452, 464], [2011, 2035], [2181, 2189], [2257, 2262]], "application", "O produto mantém os objetos concretos, delega a troca e encaminha operações ao estado atual."),
        evidence(HADOOP, H + "ha/ActiveState.java", [[34, 64]], "concrete_state", "ActiveState aceita operações e sua entrada inicia serviços ativos; a transição para standby troca o objeto."),
        evidence(HADOOP, H + "ha/StandbyState.java", [[55, 73], [89, 113]], "concrete_state", "StandbyState possui outra implementação do mesmo contrato e lança StandbyException para operações não permitidas."),
        evidence(HADOOP, H + "FSNamesystem.java", [[1676, 1680]], "caller_bridge", "FSNamesystem efetivamente chama o contrato HAContext para verificar a operação."),
    ],
    "official_context": [{"url": "https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/build/source/hadoop-hdfs-project/hadoop-hdfs/target/api/org/apache/hadoop/hdfs/server/namenode/ha/HAState.html", "scope": "API oficial documenta a base abstrata e suas subclasses; a classificação GoF é uma interpretação delimitada do código."}],
})

concepts.append({
    "concept_id": "graphql-federation",
    "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
    "independent_review": "PENDING",
    "base_role": "graphql-go-tools v2.28.0 fornece o planejador e a execução federada usados pelo produto.",
    "application_role": "WunderGraph Cosmo é o produto OSS de infraestrutura. Sua CLI compõe os schemas e seu router atende consultas usando a configuração composta. As provas vêm de código do produto, não de demo ou teste.",
    "mechanism": "A CLI lê os SDLs dos subgraphs e chama a composição. O resultado fornece schema federado e configuração por subgraph. O builder gera a configuração do router com URLs, keys, requires e provides. O loader do router converte esses dados em datasources e metadados do planejador. O prehandler planeja a consulta contra RouterSchema, e o handler executa o plano com o Resolver. Para uma busca aninhada de entidade, a biblioteca constrói representations com os campos exigidos e gera _entities; o loader executa a árvore de fetches em sequência ou paralelo e combina seus resultados.",
    "review_gap_addressed": "A cadeia agora inclui composição, consumo da configuração, planejamento federado, fetch em subgraphs e entidade por chave. O go.mod fixa exatamente a versão da biblioteca inspecionada.",
    "dependency_binding": {"manifest": "router/go.mod:34", "required_version": "v2.28.0", "tag_revision": TOOLS[1], "resolution_command": "git ls-remote https://github.com/wundergraph/graphql-go-tools.git refs/tags/v2.28.0", "literal_output": "4d20fae7080021bc08cd2d4602747ad600326ead\trefs/tags/v2.28.0"},
    "limits": ["O recorte é o próprio router federado e sua ferramenta de composição; não se afirma uma adoção por uma empresa cliente ou um deployment medido.", "O caminho mostrado é GraphQL HTTP com entidades. Os ramos opcionais de gRPC, plugins e pub/sub não são necessários à classificação.", "Cosmo usa Apache-2.0 e a biblioteca selecionada usa MIT. O novo par dispensa Apollo Router e seu enquadramento de licença."],
    "licenses": ["@".join(COSMO), "@".join(TOOLS)],
    "evidence": [
        evidence(TOOLS, G + "graphql_datasource.go", [[383, 409], [463, 470], [945, 987], [2104, 2112]], "base", "A biblioteca monta consultas _entities e representations, configura o fetch HTTP e executa a chamada ao subgraph."),
        evidence(TOOLS, G + "representation_variable.go", [[21, 25], [45, 62]], "entity_keys", "A representação é construída a partir de TypeName e SelectionSet dos campos exigidos, com typename."),
        evidence(TOOLS, "v2/pkg/engine/resolve/loader.go", [[391, 441], [522, 537], [2249, 2258]], "multi_subgraph_execution", "A árvore de fetch possui ramos single, sequence e parallel; o loader chama o datasource e mescla o resultado."),
        evidence(COSMO, "router/core/operation_planner.go", [[74, 112]], "application", "O router instancia plan.NewPlanner com PlanConfig e planeja contra RouterSchema."),
        evidence(COSMO, "router/go.mod", [[30, 36]], "dependency", "O produto depende de graphql-go-tools/v2 v2.28.0."),
        evidence(COSMO, "cli/src/commands/router/commands/compose.ts", [[312, 339], [373, 402], [198, 207]], "composition_caller", "A CLI real compõe SDLs, gera configuração a partir do resultado e a grava em arquivo."),
        evidence(COSMO, "cli/src/utils.ts", [[189, 208]], "composition_bridge", "composeSubgraphs encaminha os subgraphs à API de federação."),
        evidence(COSMO, "composition/src/federation/federation.ts", [[14, 23]], "composition_dispatch", "A API pública despacha a implementação de composição correspondente."),
        evidence(COSMO, "composition/src/v1/federation/federation-factory.ts", [[3486, 3503], [3520, 3527], [3648, 3654]], "composition_implementation", "A composição normaliza os subgraphs e constrói o schema GraphQL federado e os metadados por subgraph."),
        evidence(COSMO, "shared/src/router-config/builder.ts", [[269, 300], [372, 429]], "composition_output", "O builder preserva SDL, keys, requires, provides e URL de fetch em uma configuração de engine única."),
        evidence(COSMO, "router/core/factoryresolver.go", [[441, 449], [464, 500], [662, 682]], "runtime_metadata", "O router monta o datasource federado e copia as chaves e dependências para o planejador da biblioteca."),
        evidence(COSMO, "router/core/executor.go", [[234, 255]], "caller_bridge", "A construção do executor usa o loader para transformar EngineConfig e Subgraphs em PlanConfig."),
        evidence(COSMO, "router/core/graphql_prehandler.go", [[1164, 1172]], "request_bridge", "Uma consulta HTTP real chama o planejador."),
        evidence(COSMO, "router/core/graphql_handler.go", [[216, 238], [350, 355]], "execution_caller", "O handler resolve o plano preparado e registra os subgraphs envolvidos."),
    ],
    "official_context": [{"url": "https://cosmo-docs.wundergraph.com/router/intro", "scope": "A documentação primária identifica o router Apache 2.0 e confirma sua utilização de graphql-go-tools, roteamento federado e agregação."}],
})

concepts.append({
    "concept_id": "distributed-tracing",
    "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
    "independent_review": "PENDING",
    "base_role": "Airlift 451 fornece a propagação W3C, os carriers HTTP/JSON e o exporter OpenTelemetry usados pelo Trino.",
    "application_role": "Trino é o motor SQL distribuído real; o recorte liga uma tarefa remota no coordinator ao processamento no worker.",
    "mechanism": "HttpRemoteTask serializa stageSpan no TaskUpdateRequest e o envia por HTTP ao worker. O TracingModule instalado pelo servidor registra os serializers de Span: a serialização injeta o contexto em um mapa e a desserialização extrai um Span remoto desse mapa. TaskResource recebe o pedido e entrega o stageSpan a SqlTaskManager, que o passa para SqlTask. O worker cria o span task com esse stageSpan como pai. Em paralelo, o cliente HTTP injeta contexto em headers e o filtro do servidor extrai os headers para criar um span SERVER correlacionado. Com tracing habilitado, o mesmo módulo instala BatchSpanProcessor e exporter OTLP.",
    "review_gap_addressed": "Há carrier enviado ao outro processo, inject/extract, span remoto com pai explícito, instalação pelo produto e caminho de exportação. Isso excede a mera presença de spans locais.",
    "dependency_binding": {"manifest": "pom.xml:188", "required_version": "451", "tag_revision": AIRLIFT[1], "resolution_command": "git ls-remote https://github.com/airlift/airlift.git refs/tags/451 refs/tags/451^{}", "literal_output": "7a861450d9336a49815a8c9f56247e1885c2df91\trefs/tags/451\n2fd0bb60d560a511403957d79931f5915adced44\trefs/tags/451^{}"},
    "limits": ["Tracing é desabilitado por padrão. A classificação comprova o caminho implementado e configurável; não comprova que algum cluster esteja exportando traces neste momento.", "O span task no worker é filho do stageSpan transportado no JSON. Ele não é apresentado como filho do span HTTP task-update; ambos pertencem à mesma árvore por rotas explícitas diferentes.", "A prova não pressupõe que todos os connectors propaguem contexto. A documentação exige suporte e habilitação nas integrações externas."],
    "licenses": ["@".join(TRINO), "@".join(AIRLIFT)],
    "evidence": [
        evidence(AIRLIFT, "tracing/src/main/java/io/airlift/tracing/SpanSerialization.java", [[28, 49], [52, 73]], "base", "O serializer injeta contexto no carrier JSON e o deserializer o extrai e recupera Span.fromContext."),
        evidence(TRINO, R + "server/remotetask/HttpRemoteTask.java", [[778, 789], [804, 815], [1204, 1210]], "application", "O coordinator envia stageSpan no pedido real e cria o span da chamada HTTP com pai explícito."),
        evidence(TRINO, R + "server/TaskResource.java", [[142, 172]], "remote_receiver", "O endpoint no worker recebe TaskUpdateRequest e entrega seu stageSpan ao taskManager."),
        evidence(TRINO, R + "execution/SqlTaskManager.java", [[498, 507], [519, 529], [569, 569]], "worker_bridge", "SqlTaskManager encaminha o span recebido até a atualização de SqlTask."),
        evidence(TRINO, R + "execution/SqlTask.java", [[581, 591], [248, 248]], "remote_child_span", "O worker cria task com parent(stageSpan), atributos de query/stage/task, e encerra o span no fim da tarefa."),
        evidence(TRINO, R + "server/Server.java", [[106, 120]], "installation", "O bootstrap real instala JsonModule e TracingModule."),
        evidence(TRINO, "pom.xml", [[188, 188]], "dependency", "O produto fixa Airlift 451."),
        evidence(AIRLIFT, "tracing/src/main/java/io/airlift/tracing/TracingModule.java", [[26, 36]], "carrier_and_exporter_binding", "O módulo registra ambos os serializers e instala o exporter quando tracing está habilitado."),
        evidence(AIRLIFT, "http-client/src/main/java/io/airlift/http/client/jetty/JettyHttpClient.java", [[954, 978]], "http_injection", "O cliente cria span CLIENT e injeta o contexto nos headers enviados."),
        evidence(AIRLIFT, "http-server/src/main/java/io/airlift/http/server/tracing/TracingServletFilter.java", [[86, 97], [128, 140]], "http_extraction", "O servidor extrai o carrier HTTP e cria span SERVER com o contexto remoto como pai."),
        evidence(AIRLIFT, "http-server/src/main/java/io/airlift/http/server/HttpServerModule.java", [[97, 100]], "filter_installation", "O módulo HTTP liga o filtro de tracing ao servidor."),
        evidence(AIRLIFT, A + "OpenTelemetryModule.java", [[102, 113], [144, 154]], "propagation_and_processing", "A SDK usa W3CTraceContextPropagator, sampler parent-based e o conjunto de SpanProcessors."),
        evidence(AIRLIFT, A + "OpenTelemetryExporterModule.java", [[72, 101]], "export", "O módulo cria BatchSpanProcessor e exporter OTLP gRPC ou HTTP/protobuf com endpoint configurado."),
        evidence(TRINO, "docs/src/main/sphinx/admin/opentelemetry.md", [[15, 29], [31, 48]], "pinned_product_documentation", "A documentação fixada no mesmo commit explica coordinator/worker, propagação e configuração de exportação desabilitada por padrão."),
    ],
    "official_context": [{"url": "https://trino.io/docs/current/admin/opentelemetry.html", "scope": "A documentação pública foi consultada; a versão no commit do produto foi capturada para não depender da URL current."}],
})

review = json.loads(REVIEW.read_text())
review_by_id = {item["concept_id"]: item for item in review["concepts"]}
for concept in concepts:
    concept["original_review_state"] = review_by_id[concept["concept_id"]]["state"]
    concept["original_review_note"] = review_by_id[concept["concept_id"]]["notes"]

result = {
    "schema_version": "rare-runtime-repairs/v1",
    "author_lane": {"agent": "/root/rare_oss_sources", "native_type": "default", "model": "gpt-6.1-sol", "reasoning_effort": "xhigh", "routing": "WARM_REUSE", "role": "DEEP_EXPLORE primary-source curation; not an independent review"},
    "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "workspace": str(Path.cwd()),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "review_input": {"artifact": str(REVIEW), "sha256": digest(REVIEW.read_bytes()), "matrix_sha256_from_review": review["matrix_sha256"]},
    "write_scope": str(OUTPUT) + "/**",
    "delivery_limits": ["Somente evidência autoral foi produzida. Nenhuma classificação congelada, fonte global, MDX, build, produção, teste ou Jira foi alterado por esta lane.", "A integração e a rechecagem independente pertencem ao curador e ao reviewer; os cinco itens continuam recomendações até esses gates.", "Context7 respondeu que a cota mensal estava esgotada. Foram usados caches locais e código/documentação primários oficiais. A pesquisa GitHub Search não foi necessária: árvores já capturadas e a API de árvore do repositório orientaram os paths.", "O primeiro palpite router/pkg/execution_config/execution_config.go retornou 404; a árvore primária indicou routerconfig.go, que foi capturado com sucesso. Nenhuma conclusão usa o path inexistente."],
    "licenses": licenses,
    "concepts": concepts,
}
destination = OUTPUT / "rare-runtime-recommendations.json"
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
manifest = {"sources": list(sources.values()), "licenses": licenses}
(OUTPUT / "rare-runtime-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
receipt = {"observed_utc": result["observed_utc"], "workspace": result["workspace"], "branch": result["branch"], "head": result["head"], "recommendation_count": len(concepts), "independent_review": "PENDING", "source_count": len(sources), "license_count": len(licenses), "artifact": str(destination), "sha256": digest(destination.read_bytes())}
(OUTPUT / "rare-runtime-completion-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
