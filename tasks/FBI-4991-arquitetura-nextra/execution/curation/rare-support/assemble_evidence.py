"""Assemble bounded, source-backed recommendations without editing the matrix."""

from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path


BASE = Path(__file__).resolve().parent


def source(repository, path, ranges, claim, license_path=None, spdx=None):
    artifact = BASE / (repository.replace("/", "--") + "--" + path.replace("/", "--"))
    receipt = json.loads(artifact.with_name(artifact.name + ".receipt.json").read_text())
    lines = artifact.read_text().splitlines()
    receipt["claim"] = claim
    receipt["evidence"] = [
        {
            "start_line": start,
            "end_line": end,
            "url": receipt["url"] + f"#L{start}-L{end}",
            "excerpt": "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1)),
        }
        for start, end in ranges
    ]
    if license_path:
        license_artifact = BASE / (
            repository.replace("/", "--") + "--" + license_path.replace("/", "--")
        )
        license_receipt = json.loads(
            license_artifact.with_name(license_artifact.name + ".receipt.json").read_text()
        )
        receipt["license"] = {
            "status": "READ",
            "spdx": spdx,
            **license_receipt,
            "excerpt": "\n".join(license_artifact.read_text().splitlines()[:9]),
        }
    elif spdx:
        receipt["license"] = {
            "status": "READ_FILE_HEADER",
            "spdx": spdx,
            "url": receipt["url"] + "#L1-L7",
            "artifact": receipt["artifact"],
            "revision": receipt["revision"],
            "excerpt": "\n".join(lines[:7]),
            "scope": "A licença foi lida no cabeçalho deste arquivo; a API do GitHub não identificou uma licença do repositório inteiro.",
        }
    return receipt


controller_prefix = (
    "opendaylight/md-sal/sal-distributed-datastore/src/main/java/"
    "org/opendaylight/controller/cluster/databroker/actors/dds/"
)
mdsal_prefix = "dom/mdsal-dom-spi/src/main/java/org/opendaylight/mdsal/dom/spi/store/"
result = {
    "schema_version": 1,
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "agent": "/root/rare_oss_sources",
    "actual_role": "default; read-only DEEP_EXPLORE contract; gpt-6.1-sol/xhigh; fork none",
    "scope": "A/B Deployment, PAC, Space-Based Architecture e 3PC; Blackboard já estava resolvido pelo curador e foi preservado.",
    "proof_level": "Leitura de código e licença em revisões fixadas. Nenhum build, teste de execução ou uso em produção foi verificado.",
    "matrix_writes": False,
    "recommendations": [
        {
            "concept_id": "a-b-deployment",
            "decision": "RECOMMEND_AUTHOR_SOURCE_MATCH",
            "application_kind": "PRODUCT_OSS",
            "independent_review": "PENDING",
            "mechanism": "O Flagger usa condições de cabeçalhos ou cookies para selecionar uma população. O roteador produz uma regra Istio para esse grupo e uma regra de fallback para a versão primária. O controller executa runAB, encaminha o grupo à versão em avaliação, conta as iterações e promove a versão após o gate de promoção.",
            "limits": "O trecho prova distribuição e promoção por grupo de requisições. Ele não prova aleatorização de experimento, cálculo de significância estatística ou um teste em produção. Istio é a base de roteamento; Flagger é o operador real que a consome.",
            "base": [source("istio/api", "networking/v1alpha3/virtual_service.proto", [(735, 744), (787, 807)], "HTTPMatchRequest define condições e o mapa de cabeçalhos com StringMatch.", "LICENSE", "Apache-2.0")],
            "application": [
                source("fluxcd/flagger", "pkg/router/istio.go", [(237, 261), (540, 574), (614, 634)], "O operador compõe analysis.Match e service.Match e escreve rotas distintas no VirtualService.", "LICENSE", "Apache-2.0"),
                source("fluxcd/flagger", "pkg/controller/scheduler.go", [(480, 487), (639, 677)], "O dispatcher seleciona runAB, que aplica as rotas, conta iterações e promove.", "LICENSE", "Apache-2.0"),
                source("fluxcd/flagger", "docs/gitbook/usage/deployment-strategies.md", [(166, 175), (186, 196)], "A documentação primária distingue grupo definido por condição de avanço percentual.", "LICENSE", "Apache-2.0"),
            ],
        },
        {
            "concept_id": "pac",
            "decision": "RECOMMEND_AUTHOR_SOURCE_MATCH_WITH_HISTORICAL_LIMIT",
            "application_kind": "PRODUCT_OSS",
            "independent_review": "PENDING",
            "mechanism": "O WengoPhone é um cliente de telefonia e mensagens. O controle raiz cria o controle de perfis; este cria o controle de um perfil; o perfil contém o controle da lista de contatos. Cada controle liga seu modelo à sua apresentação. Ao criar um contato, o modelo emite um evento, CContactList recebe o evento e encaminha a atualização à apresentação Qt. Quando a tela pede uma alteração, ela chama o controle, que altera o modelo.",
            "limits": "É um caso histórico de produto OSS, preservado no repositório do autor Tanguy Krotoff, e não uma recomendação de adoção atual. O WengoPhone usa sua própria infraestrutura PAC e não depende do WakaPAC. Existe um atalho de composição visual: QtContactList.cpp L137-138 obtém a apresentação raiz e registra a lista; portanto não se afirma isolamento formal de toda comunicação entre apresentações. O caminho de dados e a hierarquia de controles citados estão em código.",
            "base": [
                source("quellabs/wakapac", "wakapac.js", [(5807, 5825), (6987, 7010), (9742, 9760)], "O runtime independente mantém abstração, container, mediação de eventos e relações de pai e filhos.", "LICENSE", "MIT"),
                source("tkrotoff/WengoPhone", "wengophone/src/control/Control.h", [(31, 49), (59, 86)], "A infraestrutura interna documenta a mediação modelo/apresentação e a existência do controle raiz.", "wengophone/COPYING", "GPL-2.0-or-later"),
            ],
            "application": [
                source("tkrotoff/WengoPhone", "wengophone/src/control/CWengoPhone.cpp", [(51, 56)], "O controle raiz cria sua apresentação e o controle de perfis.", "wengophone/COPYING", "GPL-2.0-or-later"),
                source("tkrotoff/WengoPhone", "wengophone/src/control/profile/CUserProfileHandler.cpp", [(133, 137)], "O controle de perfis cria o controle do perfil selecionado.", "wengophone/COPYING", "GPL-2.0-or-later"),
                source("tkrotoff/WengoPhone", "wengophone/src/control/profile/CUserProfile.cpp", [(55, 70)], "O controle do perfil contém controles de contatos, telefonia e chat e cria sua apresentação.", "wengophone/COPYING", "GPL-2.0-or-later"),
                source("tkrotoff/WengoPhone", "wengophone/src/control/contactlist/CContactList.cpp", [(51, 59), (70, 91), (211, 233)], "O controle liga eventos do modelo à apresentação e recebe comandos que mudam o modelo.", "wengophone/COPYING", "GPL-2.0-or-later"),
                source("tkrotoff/WengoPhone", "wengophone/src/presentation/qt/contactlist/QtContactList.cpp", [(137, 138), (150, 155), (183, 190), (270, 285)], "A apresentação consulta e altera contatos por meio de CContactList; o atalho visual citado permanece documentado.", "wengophone/COPYING", "GPL-2.0-or-later"),
                source("tkrotoff/WengoPhone", "wengophone/src/model/contactlist/ContactList.cpp", [(95, 110)], "A abstração cria o contato e publica contactAddedEvent.", "wengophone/COPYING", "GPL-2.0-or-later"),
            ],
        },
        {
            "concept_id": "three-phase-commit-3pc",
            "decision": "RECOMMEND_AUTHOR_SOURCE_MATCH_WITH_PROTOCOL_LIMIT",
            "application_kind": "PRODUCT_OSS",
            "independent_review": "PENDING",
            "mechanism": "O OpenDaylight usa um protocolo de três fases para transações do seu armazenamento distribuído. O contrato MD-SAL separa a votação, o pré-commit e o commit. A coordenação executa as fases nessa ordem e tenta abortar quando uma fase falha. Quando uma transação envolve vários participantes, ClientTransaction.ready cria ClientTransactionCommitCohort, que reúne os votos de todos os proxies e envia pedidos reais de votação, pré-commit e commit aos participantes.",
            "limits": "O caso é o armazenamento do controlador de redes OpenDaylight, e não uma demo de carteira. A implementação chama sua coordenação de blocking three-phase commit; as fontes verificadas não provam todas as garantias teóricas do 3PC clássico nem tolerância irrestrita a partições. O código registra que, após pré-commit, o estado foi replicado no backend e será consolidado após timeout. A licença EPL-1.0 dos arquivos MD-SAL foi lida em seus cabeçalhos, pois não havia arquivo raiz de licença na árvore consultada.",
            "base": [
                source("opendaylight/mdsal", mdsal_prefix + "DOMStoreThreePhaseCommitCohort.java", [(14, 20), (22, 63)], "A interface declara explicitamente 3PC e define as três fases e o abort.", spdx="EPL-1.0"),
                source("opendaylight/mdsal", "dom/mdsal-dom-broker/src/main/java/org/opendaylight/mdsal/dom/broker/CommitCoordinationTask.java", [(24, 26), (64, 85)], "A coordenação chama canCommitBlocking, preCommitBlocking e commitBlocking; falhas chamam abortBlocking.", spdx="EPL-1.0"),
            ],
            "application": [
                source("opendaylight/controller", controller_prefix + "ClientTransaction.java", [(104, 121)], "A transação escolhe o cohort multi-participante quando há vários proxies.", "LICENSE", "EPL-1.0"),
                source("opendaylight/controller", controller_prefix + "ClientTransactionCommitCohort.java", [(28, 73)], "As três fases percorrem todos os participantes e agregam seus votos em VotingFuture.", "LICENSE", "EPL-1.0"),
                source("opendaylight/controller", controller_prefix + "AbstractProxyTransaction.java", [(526, 550), (557, 600)], "Os proxies emitem pedidos de rede, verificam respostas e preservam o estado necessário à recuperação.", "LICENSE", "EPL-1.0"),
            ],
        },
        {
            "concept_id": "space-based-architecture",
            "decision": "KEEP_PENDING",
            "independent_review": "PENDING",
            "reason": "A busca delimitada não encontrou uma aplicação OSS real e licenciada que demonstre a composição inteira exigida. Não se afirma que ela não exista.",
            "rejected_candidates": [
                {
                    "repository": "vracks/RealTimePositionEngine",
                    "sources": [source("vracks/RealTimePositionEngine", "README.md", [(19, 19), (434, 434), (448, 450)], "O próprio autor apresenta uma demo sem persistência e a declara sem licença.")],
                    "reason": "A demo financeira tem colocalização, EntryProcessor e consultas contínuas, mas o próprio README a identifica como demo, informa ausência de persistência e termina com Unlicensed demo project. Não resolve REAL_APPLICATION_MISSING.",
                },
                {
                    "source_url": "https://docs.gigaspaces.com/ie-resources/solution-hub/xap-order-management-tutorial.html",
                    "reason": "A documentação do fornecedor declara expressamente que o tutorial de ordens não é uma aplicação real. Serve como referência didática, não como produto OSS.",
                },
                {
                    "repository": "esl/MongooseIM",
                    "revision": "ec856e5e7be117fbff6713c3cea7a74cc1ed278f",
                    "reason": "É um produto real com sessões em RAM via Mnesia e arquivo de mensagens assíncrono. A leitura feita não mostrou que o estado persistido seja a mesma entidade do espaço de sessões. Juntar esses dois mecanismos para declarar a arquitetura completa ampliaria o que o código prova.",
                    "license_note": "COPYING contém GPL versão 2 e uma exceção de ligação com OpenSSL. Não foi adjudicado um identificador SPDX composto; NOASSERTION preserva esse limite.",
                    "sources": [
                        source("esl/MongooseIM", "src/ejabberd_sm_mnesia.erl", [(27, 33), (62, 65)], "A tabela de sessões é configurada com ram_copies e recebe gravações em Mnesia.", "COPYING", "NOASSERTION"),
                        source("esl/MongooseIM", "src/mam/mod_mam_rdbms_arch_async.erl", [(15, 20), (89, 115)], "O arquivo de mensagens usa uma fila e um flush assíncrono distinto da tabela de sessões.", "COPYING", "NOASSERTION"),
                    ],
                },
            ],
            "next_required_evidence": "Um repositório de produto com licença explícita e uma cadeia verificável que una processamento junto aos dados, grade em memória, distribuição/replicação e persistência assíncrona do mesmo estado de negócio.",
        },
    ],
}

(BASE / "source-recommendations.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n"
)

# Preserve the complete upstream inventories in compressed form.
for tree_path in BASE.glob("*-tree.json"):
    raw = tree_path.read_bytes()
    gzip_path = tree_path.with_suffix(".json.gz")
    gzip_path.write_bytes(gzip.compress(raw, mtime=0))
    tree_path.with_suffix(".inventory.json").write_text(json.dumps({
        "artifact": str(gzip_path),
        "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
        "uncompressed_bytes": len(raw),
        "entry_count": len(json.loads(raw).get("tree", [])),
        "truncated": json.loads(raw).get("truncated"),
    }, indent=2) + "\n")
    tree_path.unlink()

print(json.dumps({
    "artifact": str(BASE / "source-recommendations.json"),
    "recommendations": len(result["recommendations"]),
    "recommended_source_matches": sum(r["decision"].startswith("RECOMMEND_") for r in result["recommendations"]),
    "kept_pending": sum(r["decision"] == "KEEP_PENDING" for r in result["recommendations"]),
}))
