"""Reassess Space-Based against its stated contract and a shipped infrastructure app."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


BASE = Path(__file__).resolve().parent
REPOSITORY = "apache/geode"
REVISION = "7190f09450b091a5892761bfcf8018c6918d13b7"
CORE = "geode-core/src/main/java/org/apache/geode/"


def source(path, ranges, claim):
    artifact = BASE / ("apache--geode--" + path.replace("/", "--"))
    receipt = json.loads(artifact.with_name(artifact.name + ".receipt.json").read_text())
    lines = artifact.read_text().splitlines()
    license_artifact = BASE / "apache--geode--LICENSE"
    license_receipt = json.loads((BASE / "apache--geode--LICENSE.receipt.json").read_text())
    return {
        "kind": "FILE",
        **receipt,
        "claim": claim,
        "evidence": [
            {
                "start_line": start,
                "end_line": end,
                "url": receipt["url"] + f"#L{start}-L{end}",
                "excerpt": "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1)),
            }
            for start, end in ranges
        ],
        "license": {
            **license_receipt,
            "status": "READ",
            "spdx": "Apache-2.0",
            "excerpt": "\n".join(license_artifact.read_text().splitlines()[:4]),
        },
    }


def primary_document(name, ranges, claim):
    receipt = json.loads((BASE / (name + ".receipt.json")).read_text())
    artifact = BASE / (name + ".txt")
    lines = artifact.read_text().splitlines()
    return {
        **receipt,
        "claim": claim,
        "text_artifact": str(artifact),
        "text_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "evidence": [
            {
                "text_start_line": start,
                "text_end_line": end,
                "excerpt": "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1)),
            }
            for start, end in ranges
        ],
    }


# Resolve the repository root without relying on a fixed number of task directories.
root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
catalog = root / "content/referencia/catalogo/01-arquiteturas-de-aplicacao.mdx"
catalog_lines = catalog.read_text().splitlines()
contract_start = next(i for i, line in enumerate(catalog_lines, 1) if line == "## Space-Based Architecture")

result = {
    "schema_version": 1,
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "concept_id": "space-based-architecture",
    "decision": "RECOMMEND_AUTHOR_SOURCE_MATCH_BOUNDED_INFRASTRUCTURE",
    "independent_review": "PENDING",
    "supersedes": "Somente a conclusão KEEP_PENDING do item space-based-architecture em rare-support/source-recommendations.json. As outras três recomendações permanecem históricas e independentes desta rechecagem.",
    "prior_assumption": {
        "verdict": "UNSUPPORTED_EXTRA_REQUIREMENT",
        "assumption": "Exigir persistência assíncrona do mesmo estado como condição obrigatória do item.",
        "correction": "A definição fornecida pelo orquestrador é Estado distribuído em memória; alta escala. A fonte primária GigaSpaces trata persistência externa como opcional. O catálogo local também usa pode ocorrer. Persistência é uma opção e um assunto de limites; sua ausência não basta para reprovar o conceito.",
        "original_definition_provenance": "Mensagem de retomada do orquestrador /root nesta sessão; a definição original foi entregue inline.",
        "local_catalog": {
            "path": str(catalog.relative_to(root)),
            "sha256": hashlib.sha256(catalog.read_bytes()).hexdigest(),
            "start_line": contract_start,
            "end_line": contract_start + 2,
            "excerpt": "\n".join(f"{i}: {catalog_lines[i - 1]}" for i in range(contract_start, contract_start + 3)),
        },
    },
    "application_kind": "PRODUCT_OSS",
    "application_scope": "O servidor de cache Apache Geode e seu caminho entregue de consultas administrativas distribuídas.",
    "role_distinction": "A base é a biblioteca Geode que define regiões e execução por partição. A aplicação é o daemon com main e ciclo de vida ServerLauncher, somado ao serviço administrativo DataQueryEngine/QueryDataFunction que usa a biblioteca. Ambos pertencem ao mesmo produto e repositório; nenhum dos arquivos escolhidos pertence a examples ou tests.",
    "classification_basis": "A correspondência com SBA é uma interpretação desta curadoria baseada na definição primária e na cadeia de código. Não se atribui ao Apache uma declaração de que o produto inteiro, em todas as configurações, tenha o rótulo SBA.",
    "mechanism": "O servidor Geode cria o cache, abre o serviço de rede e pode distribuir e rebalancear buckets. As regiões PARTITION_REDUNDANT mantêm partições de estado e uma cópia adicional em memória entre os membros. No serviço de consultas, DataQueryEngine envia o trabalho aos membros do cluster. QueryDataFunction executa a consulta nos buckets primários locais ou usa a execução por região. O núcleo PartitionedRegion agrupa chaves por bucket e por membro e encaminha a função aos nós que possuem esses dados. Cada servidor reúne dados e processamento; o aumento do número de membros permite distribuir partições e trabalho.",
    "limits": "O recorte é uma aplicação de infraestrutura: servidor de dados e consultas administrativas. A classificação descreve esse caminho e não todas as configurações possíveis do Geode. Regiões sem persistência perdem estado se todas as cópias em memória forem perdidas; persistência e redundância são decisões distintas. A leitura de código demonstra mecanismos de distribuição, não uma medição de capacidade, latência ou desempenho na Faz Capital.",
    "persistence_required_by_verified_contract": False,
    "proof_level": "Código de produto e documentação primária em revisão fixada; nenhuma instância foi iniciada e nenhum benchmark foi executado.",
    "base": [
        source(CORE + "cache/RegionShortcut.java", [(28, 56)], "O contrato distingue regiões particionadas com cópia adicional em memória das variantes persistentes."),
        source(CORE + "cache/DataPolicy.java", [(235, 258)], "withPersistence exclui PARTITION e REPLICATE; withPartitioning aceita PARTITION com ou sem persistência."),
        source(CORE + "internal/cache/execute/PartitionedRegionFunctionExecutor.java", [(214, 230)], "A execução por região delega a função ao motor de partições, em vez de tratar a função como cálculo local desconectado dos dados."),
    ],
    "application": [
        source(CORE + "distributed/ServerLauncher.java", [(259, 269), (813, 844), (1017, 1025), (1048, 1053)], "A aplicação tem main, cria o cache, inicia o servidor e executa assignBuckets/rebalance."),
        source(CORE + "distributed/internal/DefaultServerLauncherCacheProvider.java", [(27, 53)], "O daemon instancia a biblioteca CacheFactory e cria seu cache efetivo."),
        source(CORE + "management/internal/beans/DistributedSystemBridge.java", [(1441, 1452)], "A operação administrativa queryData delega ao motor de consultas entregue no produto."),
        source(CORE + "management/internal/beans/DataQueryEngine.java", [(191, 201), (225, 231)], "O motor envia a função de consulta a um ou vários membros e recolhe seus resultados."),
        source(CORE + "management/internal/beans/QueryDataFunction.java", [(115, 122), (144, 168), (284, 301)], "A consulta aplicada opera nos buckets primários locais ou executa uma função na região e devolve os resultados."),
        source(CORE + "internal/cache/PartitionedRegion.java", [(3590, 3637), (3644, 3656), (3759, 3799)], "O motor agrupa trabalho pelos proprietários dos buckets e executa a função nos membros locais e remotos correspondentes."),
    ],
    "primary_architecture_sources": [
        primary_document("gigaspaces-in-memory-grid", [(245, 246), (341, 350)], "A fonte primária de SBA trata o espaço como estado distribuído e associa sua escalabilidade a unidades de processamento; persistência relacional é usada se necessária."),
        primary_document("gigaspaces-processing-unit", [(73, 80)], "A descrição de unidades de processamento admite unidades somente de dados, somente de lógica e mistas; não exige uma interface de negócio para cada unidade."),
        source("geode-docs/getting_started/product_intro.html.md.erb", [(38, 40), (54, 58), (66, 72)], "A documentação primária Geode explica dados em memória, persistência configurável e execução de funções junto às partições."),
    ],
    "context7": {
        "queries": ["Apache Geode", "Apache Geode distributed in-memory data management"],
        "result": "As duas resoluções devolveram apenas /geode-sdk/docs, que é um SDK de Geometry Dash. Esse resultado foi descartado por produto incompatível. A evidência usa documentação oficial Apache fixada na mesma revisão do código.",
    },
    "writes": "Somente tasks/FBI-4991-arquitetura-nextra/execution/curation/rare-support/.",
}

target = BASE / "space-based-reassessment.json"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
receipt = {
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "cwd": str(root),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "artifact": str(target.relative_to(root)),
    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    "decision": result["decision"],
    "product_revision": REVISION,
    "source_count": len(result["base"]) + len(result["application"]),
}
(BASE / "space-based-reassessment.receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
