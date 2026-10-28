"""Assemble the bounded Nova/Neutron and discovery-host follow-up evidence."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


BASE = Path(__file__).resolve().parent


def source(repo, path, ranges, claim, header_license=None, prior_license=False):
    artifact = BASE / ("ddd-followon-" + repo.replace("/", "--") + "--" + path.replace("/", "--"))
    receipt = json.loads(artifact.with_name(artifact.name + ".receipt.json").read_text())
    lines = artifact.read_text().splitlines()
    item = {
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
    }
    if header_license:
        item["license"] = {
            "status": "READ_FILE_HEADER",
            "spdx": header_license,
            "url": receipt["url"] + "#L1-L5",
            "artifact": str(artifact),
            "excerpt": "\n".join(lines[:5]),
        }
    else:
        prefix = "ddd-" if prior_license else "ddd-followon-"
        license_artifact = BASE / (prefix + repo.replace("/", "--") + "--LICENSE")
        license_receipt = json.loads(
            license_artifact.with_name(license_artifact.name + ".receipt.json").read_text()
        )
        item["license"] = {
            **license_receipt,
            "status": "READ",
            "spdx": "Apache-2.0",
            "excerpt": "\n".join(license_artifact.read_text().splitlines()[:5]),
        }
    return item


rfe_artifact = BASE / "ddd-followon-neutron-rfe-bug-tasks.json"
rfe_receipt = json.loads((BASE / "ddd-followon-neutron-rfe-bug-tasks.receipt.json").read_text())
rfe_rows = json.loads(rfe_artifact.read_text())["entries"]
rfe_task = next(row for row in rfe_rows if row["target_link"].endswith("/neutron"))
host_query = json.loads((BASE / "ddd-followon-host-symbol-query.json").read_text())
doc_receipt = json.loads((BASE / "ddd-followon-contextmapper-discovery.receipt.json").read_text())
doc_text = BASE / "ddd-followon-contextmapper-discovery.txt"
doc_lines = doc_text.read_text().splitlines()

customer_supplier = {
    "concept_id": "customer-supplier",
    "decision": "RECOMMEND_SOURCE_MATCH_NOVA_NEUTRON_LIVE_MIGRATION_BINDINGS",
    "independent_review": "PENDING",
    "application_kind": "PRODUCT_OSS",
    "supersedes": "A conclusão KEEP_PENDING_ORGANIZATIONAL_CONTRACT da linha Customer/Supplier no pacote ddd-patterns-evidence.json; o novo caso é Nova/Neutron, não thndr-mcp.",
    "bounded_relationship": {
        "customer_downstream": "Nova, contexto de computação e migração de instâncias.",
        "supplier_upstream": "Neutron, contexto de redes e vínculos de portas.",
        "model_owner": "Neutron controla o sub-recurso bindings, seu estado ativo/inativo e a ação activate, publicados por neutron-lib.",
        "customer_control": "Nova controla quando preparar o destino, iniciar a migração, ativar o vínculo e realizar rollback; o plano Neutron prevê atender os caminhos de rollback que Nova decidir implementar.",
    },
    "mechanism": "Nova precisava conhecer a ligação de rede do destino antes de mover a instância, preservando a ligação ativa na origem. A proposta do Neutron transformou essa necessidade em mudanças de API, modelo de dados e ML2, com responsável e plano de testes. O RFE correspondente registra Fix Released. A especificação aprovada do Nova prevê a adoção da API. No código atual, o conductor prepara as portas no destino; o cliente cria o binding por host e depois pede sua ativação. O Neutron cria o segundo vínculo como inativo, preserva o ativo e oferece a ação que troca a ligação selecionada. Assim, há uma necessidade downstream incorporada ao plano e ao contrato do fornecedor, além de chamadas entre serviços.",
    "limits": "A interpretação Customer/Supplier vale para essa evolução histórica de port binding para migração. Não caracteriza toda a governança OpenStack nem prova execução em produção. A proposta Neutron encontrada está hoje em backlog/pike; não foi tratada como uma especificação Rocky aprovada. O pedido concluído, o plano aprovado do Nova e a implementação atual constituem as provas adicionais. A sintaxe publicada evoluiu: o código atual usa host, enquanto trechos antigos da proposta usam host_id.",
    "base": [
        source("openstack/neutron-lib", "neutron_lib/api/definitions/portbindings_extended.py", [(47, 68), (75, 85), (104, 120)], "A biblioteca pública define o contrato que o fornecedor mantém: binding-extended, host, status e activate por PUT."),
    ],
    "accepted_requirement_and_delivery": {
        **rfe_receipt,
        "scope": "Estado do item público no Launchpad, consultado nesta passada; não é estado de um serviço implantado.",
        "task": {key: rfe_task.get(key) for key in ["title", "status", "target_link", "self_link", "date_fix_released", "date_fix_committed"]},
    },
    "design_sources": [
        source("openstack/neutron-specs", "specs/backlog/pike/portbinding_information_for_nova.rst", [(27, 46), (98, 150), (694, 698), (714, 725), (732, 751)], "O fornecedor descreve a necessidade do cliente, deriva o trabalho, assume suporte aos caminhos de migração escolhidos pelo cliente e nomeia responsável e testes.", header_license="CC-BY-3.0"),
        source("openstack/nova-specs", "specs/queens/approved/neutron-new-port-binding-api.rst", [(8, 15), (91, 112), (326, 354)], "O cliente tem plano aprovado de adoção, responsável, itens de trabalho e dependência explícita das mudanças do Neutron.", header_license="CC-BY-3.0"),
    ],
    "application": [
        source("openstack/nova", "nova/conductor/tasks/live_migrate.py", [(386, 392), (403, 435)], "A etapa real de migração verifica a extensão e prepara os bindings de destino antes de seguir."),
        source("openstack/nova", "nova/network/neutron.py", [(1499, 1510), (1561, 1582), (3215, 3224)], "O cliente detecta a extensão, cria o vínculo por host e solicita sua ativação pelo contrato do fornecedor."),
        source("openstack/neutron", "neutron/extensions/portbindings_extended.py", [(49, 76)], "A extensão registra os recursos e a ação pública no plugin efetivo."),
        source("openstack/neutron", "neutron/plugins/ml2/plugin.py", [(830, 845), (2800, 2828), (2918, 2942), (2949, 2977)], "O fornecedor mantém os vínculos ativos/inativos e implementa a ação de ativação no ML2; a confirmação troca explicitamente os estados dos vínculos antigo e novo."),
    ],
    "framework_category": "neutron-lib é a biblioteca de contrato da implementação. O padrão estratégico é demonstrado pelo planejamento coordenado e pelo contrato aplicado; não se afirma que uma biblioteca produza sozinha a relação entre equipes.",
}

conformist = {
    "concept_id": "conformist",
    "decision": "KEEP_PENDING_DISCOVERY_APPLICATION_HOST_NOT_PROVED",
    "independent_review": "PENDING",
    "previous_evidence_preserved": "A relação DiscoveryLibrary→LanguageCore explicitada na tese e implementada no serializer continua documentada no pacote anterior. Esta passada verificou somente a lacuna de aplicativo hospedeiro.",
    "checked_hosts": [
        {"repo": "ContextMapper/context-mapper-dsl", "revision": "995f486a9cdecb6946257d5c7b6d98ada2978124", "surface": "Registro de comandos Eclipse plugin.xml, manifesto OSGi e build raiz."},
        {"repo": "ContextMapper/vscode-extension", "revision": "cd0363ec33de4f41cc311a715ed5afd01ff8c7f3", "surface": "Registro de comandos src/extension.ts, manifesto da extensão e build do servidor de linguagem."},
        {"repo": "ContextMapper/context-mapper-cli", "revision": "b819362eed75e7dfb0332fa1acdda56f9029b91d", "surface": "main e subcommands, dependências de build e comandos anunciados no README."},
    ],
    "result": "Nos nove arquivos de registro/build explicitamente examinados, não ocorreram ContextMapDiscoverer, ContextMapSerializer ou context-map-discovery. O CLI registra validate e generate; VS Code registra geração, transformações e quick fixes. A documentação oficial de descoberta mantém a classificação prototype e ensina uso direto como biblioteca. Nenhum desses fatos prova ausência global de consumidores; eles não fornecem o chamador real que faltava ao critério.",
    "scope_query": host_query,
    "official_documentation": {
        **doc_receipt,
        "text_artifact": str(doc_text),
        "excerpt_lines": [90, 98],
        "excerpt": "\n".join(f"{i}: {doc_lines[i - 1]}" for i in range(90, 99)),
    },
    "sources": [
        source("ContextMapper/context-mapper-dsl", "org.contextmapper.dsl.ui/plugin.xml", [(840, 866)], "Os comandos Eclipse escolhidos geram representações e contratos; nenhum deles é um chamador de descoberta demonstrado.", prior_license=True),
        source("ContextMapper/context-mapper-dsl", "org.contextmapper.dsl.ui/META-INF/MANIFEST.MF", [(1, 31)], "O manifesto do plugin foi consultado como parte da busca delimitada por uma dependência da biblioteca de descoberta.", prior_license=True),
        source("ContextMapper/vscode-extension", "src/extension.ts", [(15, 41), (44, 72)], "O entrypoint inicia o servidor de linguagem e registra seus comandos reais, sem demonstrar a chamada de descoberta."),
        source("ContextMapper/vscode-extension", "build.gradle", [(23, 31)], "A distribuição embutida é context-mapper-lsp."),
        source("ContextMapper/context-mapper-cli", "src/main/java/org/contextmapper/cli/ContextMapperCLI.java", [(6, 15), (23, 30)], "A aplicação CLI real registra somente ValidateCommand e GenerateCommand nesse entrypoint."),
        source("ContextMapper/context-mapper-cli", "build.gradle", [(18, 34)], "O build consultado declara context-mapper-dsl e Picocli, sem uma chamada demonstrada à biblioteca de descoberta."),
    ],
    "remaining_gate": "Localizar uma aplicação publicada e seu chamador efetivo de context-map-discovery, ou um caso de produto diferente com adoção e controle do modelo upstream documentados. Esta investigação não reclassifica a biblioteca protótipo como aplicativo.",
}

result = {
    "schema_version": 1,
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Follow-on delimitado a Customer/Supplier e Conformist.",
    "rows": [customer_supplier, conformist],
    "summary": {"recommended_source_matches": 1, "kept_pending_with_verified_boundary": 1},
    "proof_level": "Leitura de decisões, item público de planejamento, código e licenças. Nenhum teste ou serviço foi executado.",
    "write_scope": "Somente execution/curation/rare-support/ddd-followon*.",
}
target = BASE / "ddd-followon-evidence.json"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
receipt = {
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "artifact": str(target),
    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    **result["summary"],
}
(BASE / "ddd-followon-completion-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
