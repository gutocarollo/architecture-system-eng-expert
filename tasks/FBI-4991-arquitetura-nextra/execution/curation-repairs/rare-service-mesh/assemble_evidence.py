from pathlib import Path
import copy
import datetime
import hashlib
import json
import subprocess


ROOT = Path("tasks/FBI-4991-arquitetura-nextra/execution")
OUTPUT = ROOT / "curation-repairs/rare-service-mesh"
ISTIO = ("istio/istio", "4e2c1c576e33a7b411ee7f38ac4bb9dd45c36631")
ENVOY = ("envoyproxy/envoy", "960eacbb5ccf0a6bcc768089b1e4785ac2e7e3a1")


def digest(data):
    return hashlib.sha256(data).hexdigest()


sources = {}
for receipt_path in sorted(OUTPUT.glob("*.receipt.json")):
    source = json.loads(receipt_path.read_text())
    data = Path(source["artifact"]).read_bytes()
    assert digest(data) == source["sha256"]
    assert len(data.splitlines()) == source["line_count"]
    sources[(source["repo"], source["revision"], source["path"])] = source


def evidence(project, path, ranges, role, proves):
    source = copy.deepcopy(sources[(*project, path)])
    lines = Path(source["artifact"]).read_text().splitlines()
    source.update({"role": role, "proves": proves, "inspected_ranges": ranges, "excerpts": []})
    for start, end in ranges:
        assert 1 <= start <= end <= len(lines), (path, start, end)
        source["excerpts"].append({"start_line": start, "end_line": end, "url": f'{source["url"]}#L{start}-L{end}', "text": "\n".join(f"{line + 1}: {lines[line]}" for line in range(start - 1, end))})
    return source


licenses = {}
for project in [ISTIO, ENVOY]:
    source = copy.deepcopy(sources[(*project, "LICENSE")])
    source["license_spdx"] = "Apache-2.0"
    licenses["@".join(project)] = source

review_path = ROOT / "reviews/curation-second.concepts.json"
review = json.loads(review_path.read_text())
original = next(item for item in review["concepts"] if item["concept_id"] == "service-mesh")
identity_path = ROOT / "curation-repairs/rare-security/rare-security-recommendations.json"
concept = {
    "concept_id": "service-mesh",
    "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
    "independent_review": "PENDING",
    "base_role": "Envoy fornece a assinatura CDS e o consumidor que instala clusters recebidos por xDS. A base selecionada agora mostra consumo efetivo de configuração, além do bootstrap genérico de servidor.",
    "application_role": "Istio é o produto OSS real. O recorte é seu plano de controle e o caminho sidecar Envoy, com um exemplo concreto de DestinationRule que altera a política de balanceamento do cluster.",
    "mechanism": "O controlador Kubernetes converte eventos de Service para o modelo do Istio e notifica a atualização. PushContext reúne o catálogo de serviços e as DestinationRules. O gerador CDS selecionado para ClusterType chama BuildClusters, que percorre os serviços visíveis ao sidecar, cria clusters e aplica a DestinationRule correspondente. applyTrafficPolicy altera o protobuf de cluster; por exemplo, LoadBalancerSettings_RANDOM vira Cluster_RANDOM. O servidor serializa esses recursos em DiscoveryResponse e os envia pelo stream xDS. No workload, o agente gera o bootstrap do Envoy com CDS/LDS via ADS e um cluster xds-grpc ligado ao socket local XDS. XdsProxy encaminha requisições para Istiod e respostas para Envoy. O consumidor CDS de Envoy recebe os recursos e chama addOrUpdateCluster ou removeCluster, atualizando sua configuração de comunicação.",
    "review_gap_addressed": "A nova seleção liga descoberta e política à geração, transporte e consumo de configuração do proxy. O injector permanece evidência complementar de implantação do sidecar.",
    "call_path": [
        "O controlador onServiceEvent converte o Service Kubernetes e notifica os handlers; mudanças de endpoints também podem pedir ConfigUpdate.",
        "DiscoveryServer.Push chama initPushContext; PushContext.initServiceRegistry lê env.Services e initDestinationRules lê o ConfigStore.",
        "InitGenerators associa ClusterType a CdsGenerator. O pedido ADS chega a processRequest e pushXds seleciona esse gerador.",
        "CdsGenerator.Generate chama ConfigGenerator.BuildClusters; buildClusters chama buildOutboundClusters para o sidecar.",
        "O builder cria o cluster de cada serviço e chama applyDestinationRule; applyTrafficPolicy configura pool, detecção de falhas, balanceamento e TLS.",
        "pushXds monta DiscoveryResponse com ResourcesToAny e chama xds.Send.",
        "O agente cria o bootstrap e inicia Envoy com o arquivo gerado. O bootstrap assina CDS e LDS por ADS no socket local XDS.",
        "XdsProxy abre o stream para Istiod, envia os pedidos e entrega as respostas ao stream downstream de Envoy.",
        "CdsApiImpl.onConfigUpdate chama CdsApiHelper.onConfigUpdate, que aplica as alterações no ClusterManager de Envoy.",
    ],
    "limits": [
        "A prova é estática e delimitada ao caminho sidecar e CDS. Ela não mede um cluster em execução, entrega real de xDS, ACKs, convergência ou desempenho.",
        "A política concreta demonstrada é DestinationRule aplicada a clusters. O pacote não afirma ter seguido toda tradução de VirtualService/RDS, EDS ou todas as políticas possíveis.",
        "O bootstrap pode ser substituído por configuração customizada, e Istio também possui caminho ambient. Não se afirma que toda instalação use o mesmo template ou sidecar.",
        "Os SHAs fixam fontes Istio e Envoy que implementam a fronteira xDS v3. Não se afirma que o binário Envoy empacotado com esse snapshot Istio tenha sido construído exatamente do SHA Envoy escolhido como base.",
        "O pacote anterior de identidade foi reaproveitado como suporte complementar de segurança no mesmo SHA Istio; a classificação Service Mesh aqui se sustenta na cadeia de controle e dados demonstrada, sem depender apenas de certificado ou injeção.",
    ],
    "licenses": list(licenses),
    "evidence": [
        evidence(ENVOY, "source/common/upstream/cds_api_impl.cc", [[25, 48], [102, 117]], "base", "Envoy cria a assinatura CDS e entrega mudanças de configuração ao helper de clusters."),
        evidence(ENVOY, "source/common/upstream/cds_api_helper.cc", [[38, 66], [79, 85]], "data_plane_effect", "O consumidor converte os recursos recebidos em Cluster e chama addOrUpdateCluster; remove clusters retirados da configuração."),
        evidence(ISTIO, "pilot/pkg/networking/core/cluster.go", [[64, 74], [313, 328], [554, 559], [579, 586]], "application", "A geração real usa serviços visíveis ao proxy, percorre o ramo sidecar e aplica a política ao cluster antes de empacotá-lo."),
        evidence(ISTIO, "pilot/pkg/serviceregistry/kube/controller/controller.go", [[419, 436], [493, 508], [545, 556]], "discovery_source", "Eventos de Service e endpoints alimentam o modelo e notificam atualizações do plano de controle."),
        evidence(ISTIO, "pilot/pkg/model/push_context.go", [[1389, 1399], [1547, 1555], [2014, 2024]], "discovery_and_policy_input", "O contexto de geração lê o registro real de serviços e as DestinationRules do ConfigStore."),
        evidence(ISTIO, "pilot/pkg/xds/discovery.go", [[317, 342], [574, 583]], "refresh_caller", "Push inicializa um novo contexto de configuração e inicia o push ADS para as conexões."),
        evidence(ISTIO, "pilot/pkg/bootstrap/discovery.go", [[29, 42], [68, 69]], "generator_registration", "ClusterType é ligado ao CdsGenerator do gerador de configuração real."),
        evidence(ISTIO, "pilot/pkg/xds/cds.go", [[135, 141]], "generation_caller", "O gerador CDS chama ConfigGenerator.BuildClusters com o proxy e o pedido de push."),
        evidence(ISTIO, "pilot/pkg/networking/core/cluster_builder.go", [[350, 365], [385, 393]], "policy_bridge", "A DestinationRule é selecionada e mesclada por porta antes de applyTrafficPolicy alterar o cluster."),
        evidence(ISTIO, "pilot/pkg/networking/core/cluster_traffic_policy.go", [[46, 76], [374, 390]], "concrete_policy_translation", "A tradução aplica os componentes de política ao protobuf Envoy; RANDOM vira Cluster_RANDOM, com ramos próprios para os demais algoritmos."),
        evidence(ISTIO, "pilot/pkg/xds/ads.go", [[140, 143], [156, 180], [183, 186]], "request_entry", "O endpoint ADS processa o DiscoveryRequest e solicita o push do recurso observado pelo proxy."),
        evidence(ISTIO, "pilot/pkg/xds/xdsgen.go", [[84, 93], [112, 119], [136, 160], [170, 175]], "generation_and_transport", "O servidor seleciona o gerador por tipo, executa Generate, serializa os recursos e envia DiscoveryResponse."),
        evidence(ISTIO, "pkg/istio-agent/agent.go", [[308, 333]], "bootstrap_caller", "O agente cria o bootstrap e atribui seu arquivo a envoyOpts.ConfigPath, salvo configuração customizada."),
        evidence(ISTIO, "tools/packaging/common/envoy_bootstrap.json", [[213, 235], [346, 359]], "data_plane_configuration", "O template configura CDS/LDS por ADS v3 e aponta xds-grpc para o socket XDS local do agente."),
        evidence(ISTIO, "pkg/envoy/proxy.go", [[126, 139], [205, 212], [229, 234]], "envoy_startup", "O agente inicia o processo Envoy com -c apontando para ConfigPath."),
        evidence(ISTIO, "pkg/istio-agent/xds_proxy.go", [[291, 294], [350, 368], [455, 466], [525, 529], [554, 579]], "agent_transport_bridge", "O proxy xDS recebe o stream de Envoy, abre stream para Istiod e encaminha pedidos e respostas entre as duas pontas."),
        evidence(ISTIO, "pkg/kube/inject/inject.go", [[221, 232]], "secondary_deployment_context", "A opção de injeção do sidecar é preservada como contexto, sem ser usada sozinha para provar a malha."),
    ],
    "official_context": [
        {"url": "https://istio.io/latest/docs/ops/deployment/architecture/", "scope": "A documentação primária descreve o plano de controle Istiod e o plano de dados de proxies."},
        {"url": "https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol", "scope": "O protocolo primário documenta a entrega de configuração dinâmica por DiscoveryRequest/DiscoveryResponse. As fontes fixadas são a prova do mecanismo."},
    ],
    "reused_identity_packet": {"artifact": str(identity_path), "sha256": digest(identity_path.read_bytes()), "scope": "Suporte complementar da emissão e distribuição de identidade em Istio no mesmo SHA; não é revisão independente nem prova de implantação."},
    "original_review_state": original["state"],
    "original_review_note": original["notes"],
}

result = {
    "schema_version": "rare-service-mesh-repair/v1",
    "author_lane": {"agent": "/root/rare_oss_sources", "native_type": "default", "model": "gpt-6.1-sol", "reasoning_effort": "xhigh", "routing": "WARM_REUSE", "role": "DEEP_EXPLORE primary-source curation; not an independent review"},
    "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "workspace": str(Path.cwd()),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "review_input": {"artifact": str(review_path), "sha256": digest(review_path.read_bytes()), "matrix_sha256_from_review": review["matrix_sha256"]},
    "write_scope": str(OUTPUT) + "/**",
    "delivery_limits": ["Uma única proposta autoral foi produzida. A integração e a revisão independente pertencem ao curador e ao reviewer.", "Esta lane escreveu somente rare-service-mesh. Nenhuma matriz congelada, fonte global, MDX, configuração, Jira ou produção foi editada por ela.", "Os caches existentes foram consultados primeiro e reutilizados após conferência SHA-256. A montagem apenas relê e confere os artefatos; não executa testes de produto ou builds."],
    "licenses": licenses,
    "concepts": [concept],
}
destination = OUTPUT / "rare-service-mesh-recommendation.json"
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
(OUTPUT / "rare-service-mesh-manifest.json").write_text(json.dumps({"sources": list(sources.values()), "licenses": licenses}, ensure_ascii=False, indent=2) + "\n")
receipt = {"observed_utc": result["observed_utc"], "workspace": result["workspace"], "branch": result["branch"], "head": result["head"], "recommendation_count": 1, "independent_review": "PENDING", "source_count": len(sources), "license_count": len(licenses), "artifact": str(destination), "sha256": digest(destination.read_bytes())}
(OUTPUT / "rare-service-mesh-completion-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
