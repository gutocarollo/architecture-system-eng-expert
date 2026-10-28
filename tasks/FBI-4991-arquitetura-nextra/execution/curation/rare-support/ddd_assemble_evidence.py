"""Assemble four strategic-DDD evidence rows without changing curation owners' files."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


BASE = Path(__file__).resolve().parent
THNDR = "armaaar/thndr-mcp"
DISCOVERY = "ContextMapper/context-map-discovery"
CORE = "ContextMapper/context-mapper-dsl"
ATPROTO = "bluesky-social/atproto"
MASTODON = "mastodon/mastodon"


def source(repo, path, ranges, claim, license_path="LICENSE", spdx="Apache-2.0"):
    artifact = BASE / ("ddd-" + repo.replace("/", "--") + "--" + path.replace("/", "--"))
    receipt = json.loads(artifact.with_name(artifact.name + ".receipt.json").read_text())
    lines = artifact.read_text().splitlines()
    license_artifact = BASE / (
        "ddd-" + repo.replace("/", "--") + "--" + license_path.replace("/", "--")
    )
    license_receipt = json.loads(
        license_artifact.with_name(license_artifact.name + ".receipt.json").read_text()
    )
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
            "spdx": spdx,
            "excerpt": "\n".join(license_artifact.read_text().splitlines()[:7]),
        },
    }


def paper(slug, printed_pages, summary, quote=None):
    receipt = json.loads((BASE / (slug + ".receipt.json")).read_text())
    result = {**receipt, "printed_pages": printed_pages, "summary": summary}
    if quote:
        result["short_quote"] = quote
    result["observation_scope"] = "Arquivo primário obtido nesta investigação; o hash identifica os bytes locais consultados."
    return result


def web_document(slug, ranges, claim):
    receipt = json.loads((BASE / (slug + ".receipt.json")).read_text())
    text_artifact = BASE / (slug + ".txt")
    lines = text_artifact.read_text().splitlines()
    return {
        **receipt,
        "claim": claim,
        "text_artifact": str(text_artifact),
        "evidence": [
            {
                "text_start_line": start,
                "text_end_line": end,
                "excerpt": "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1)),
            }
            for start, end in ranges
        ],
    }


modeling_base = source(
    CORE,
    "org.contextmapper.dsl/src/org/contextmapper/dsl/ContextMappingDSL.xtext",
    [(99, 126), (136, 164), (489, 492)],
    "CML representa Shared Kernel, Customer/Supplier e o papel Conformist. É um modelo formal de relações; a gramática não cria acordos entre equipes nem comprova sua execução.",
)

rows = [
    {
        "concept_id": "shared-kernel",
        "decision": "RECOMMEND_SOURCE_MATCH_BOUNDED_DOMAIN_KERNEL",
        "application_kind": "PRODUCT_OSS",
        "application": "thndr-mcp, aplicativo MCP e CLI para mercado e carteira de investimentos.",
        "mechanism": "O ADR aceito separa Market Data, Portfolio, Engagement e Identity e reserva um núcleo pequeno de identidade de instrumentos, mercados e moedas. Ticker e AssetId preservam regras de identificação comuns. Os modelos independentes Instrument e Position usam esses tipos; o container mantém os serviços de cada contexto separados. A documentação reconhece que uma alteração no núcleo afeta todos e determina que ele permaneça mínimo.",
        "limits": "O recorte comprovado é AssetId, Ticker, Market e Currency. Money existe no núcleo, mas os dois modelos examinados consomem Currency, não a aritmética da classe Money; não se afirma que os dois contextos executem a mesma aritmética monetária. O caso prova a decisão e o código do aplicativo, sem alegar duas equipes organizacionais ou adoção em produção.",
        "base": [modeling_base],
        "application_sources": [
            source(THNDR, "docs/adr/0015-five-layer-clean-architecture-cqs-and-context-map.md", [(1, 11), (40, 54)], "O ADR aceito identifica os contextos e declara o Shared Kernel."),
            source(THNDR, "docs/domains/README.md", [(101, 116)], "A política do núcleo reconhece seu impacto em todos os contextos e enumera os conceitos de negócio compartilhados."),
            source(THNDR, "src/domain/shared-kernel/ticker.ts", [(1, 28)], "A identificação do instrumento tem normalização e validação únicas no núcleo."),
            source(THNDR, "src/domain/shared-kernel/asset-id.ts", [(1, 32)], "O núcleo valida o identificador de instrumento compartilhado."),
            source(THNDR, "src/domain/market-data/instrument.ts", [(1, 22)], "O contexto de mercado define seu Instrument com os tipos do núcleo."),
            source(THNDR, "src/domain/portfolio/position.ts", [(1, 22)], "O contexto de carteira define outro modelo, Position, com o mesmo núcleo de identidade e moeda."),
            source(THNDR, "src/__tests__/architecture.test.ts", [(190, 200)], "O código entregue contém uma regra para manter o núcleo independente. Essa suíte foi lida e não executada nesta investigação."),
        ],
        "canonical_reference": paper("ddd-evans-reference", [31], "Shared Kernel compartilha uma parte pequena do modelo e do código, com coordenação explícita de mudanças."),
    },
    {
        "concept_id": "customer-supplier",
        "decision": "KEEP_PENDING_ORGANIZATIONAL_CONTRACT",
        "application_kind": "PRODUCT_OSS_CANDIDATE",
        "application": "thndr-mcp: Market Data fornece resolução de instrumentos a Portfolio e Engagement.",
        "mechanism": "O ADR chama Market Data de supplier e os dois outros contextos de customers. InstrumentResolver pertence a Market Data; GetPosition e CreateAlert o consomem. O container conecta os dois consumidores à implementação fornecida pelo contexto de mercado. Essa parte técnica e os responsáveis pelo contrato estão demonstrados.",
        "limits": "A referência primária de Evans exige que prioridades do downstream entrem no planejamento upstream. O material localizado declara os papéis, mas não mostra negociação, compromisso de atendimento ou prioridade de mudança. O ADR também usa Open Host Service; a gramática CML distingue relações Customer/Supplier das relações genéricas com OHS. Não se converte toda dependência técnica ou o rótulo do autor em prova da relação organizacional completa.",
        "base": [modeling_base],
        "application_sources": [
            source(THNDR, "docs/adr/0015-five-layer-clean-architecture-cqs-and-context-map.md", [(40, 54)], "Os papéis pretendidos e os donos dos contextos estão declarados."),
            source(THNDR, "src/application/market-data/services/instrument-resolver.ts", [(8, 43)], "O fornecedor técnico resolve o instrumento e controla a representação retornada."),
            source(THNDR, "src/application/portfolio/queries/get-position.ts", [(34, 45)], "A carteira consome o identificador resolvido pelo contexto de mercado."),
            source(THNDR, "src/application/engagement/commands/create-alert.ts", [(42, 55)], "O contexto de alertas consome o mesmo contrato para outro fluxo de negócio."),
            source(THNDR, "src/container.ts", [(132, 163)], "O ponto de composição conecta o produtor e os dois consumidores efetivos."),
        ],
        "canonical_reference": paper("ddd-evans-reference", [32], "O padrão exige que o planejamento upstream considere prioridades e requisitos negociados com o downstream."),
        "next_required_evidence": "Uma decisão ou discussão pública com compromisso de atendimento a um requisito de Portfolio ou Engagement, acompanhada da mudança do contrato do fornecedor. Alternativamente, outro produto com essa coordenação documentada.",
    },
    {
        "concept_id": "conformist",
        "decision": "KEEP_PENDING_APPLICATION_CATEGORY_WITH_STRATEGIC_PROOF",
        "application_kind": "LIBRARY_PROTOTYPE_CANDIDATE",
        "application": "A biblioteca de descoberta do próprio Context Mapper adota o modelo da linguagem CML.",
        "mechanism": "A tese do autor modela a arquitetura do próprio Context Mapper. A figura 3.1 identifica LanguageCore como upstream e DiscoveryLibrary como downstream Conformist; o texto explica quem controla o modelo. O serializer usa o setup CML, converte os resultados para o metamodelo da linguagem e grava esse modelo. O build fixa a dependência CML em 6.11.0.",
        "limits": "Isso é evidência da relação interna do produto de ferramentas e não o exemplo fictício de seguros. Entretanto, o README da biblioteca ainda a apresenta como prototype e não foi localizado um aplicativo hospedeiro real consumindo essa função. Diante do critério que pede framework e aplicação real distintos em seus papéis, a biblioteca não foi promovida silenciosamente a aplicação. A conversão técnica também deve ser distinguida de uma ACL com linguagem própria. O thndr-mcp foi descartado como Conformist em relação ao Thndr porque declara e implementa uma ACL.",
        "base": [modeling_base],
        "application_sources": [
            source(DISCOVERY, "src/main/java/org/contextmapper/discovery/ContextMapSerializer.java", [(18, 25), (34, 48)], "A saída da descoberta é construída e serializada no modelo CML controlado pelo upstream."),
            source(DISCOVERY, "src/main/java/org/contextmapper/discovery/cml/ContextMapToCMLConverter.java", [(40, 67), (151, 159)], "A conversão preserva os conceitos do metamodelo CML e usa suas factories e relações."),
            source(DISCOVERY, "build.gradle", [(22, 29)], "O downstream depende da biblioteca oficial da linguagem."),
            source(DISCOVERY, "gradle.properties", [(5, 8)], "O projeto declara cmlVersion=6.11.0."),
        ],
        "author_architecture": paper("ddd-contextmapper-thesis", [17, 18, 38], "A tese identifica explicitamente o Conformist na arquitetura que os próprios autores implementam, e limita a influência do downstream sobre a linguagem.", "it acts as a Conformist (CF) and thus conforms to the published language of the core component."),
        "diagram_artifact": str(BASE / "ddd-contextmapper-own-context-map.png"),
        "diagram_pdf_page": 27,
        "canonical_reference": paper("ddd-evans-reference", [33], "Conformist adota o modelo upstream quando não consegue obter um contrato moldado às necessidades downstream."),
        "next_required_evidence": "Um consumidor de produto que use a biblioteca de descoberta, ou outro aplicativo real cuja adoção do modelo upstream e controle de decisão estejam documentados. Não basta reclassificar o exemplo de modelagem como produto.",
    },
    {
        "concept_id": "separate-ways",
        "decision": "RECOMMEND_SOURCE_MATCH_NATIVE_INTEROPERABILITY_BOUNDARY",
        "application_kind": "PRODUCT_OSS",
        "application": "AT Protocol/Bluesky e Mastodon/ActivityPub, no limite de modelo e interoperabilidade nativa.",
        "mechanism": "A documentação oficial do AT Protocol explica a decisão de criar um protocolo separado de ActivityPub, motivada pela portabilidade de contas e por diferenças de modelo que seriam caras de incorporar. O PDS trabalha com identidade DID, coleções e registros em repositórios assinados. O Mastodon mantém seu caminho ActivityPub de atividades, objetos e atores. Os dois produtos têm modelos nativos próprios por uma escolha publicada; a conclusão não decorre de uma busca sem imports.",
        "limits": "A correspondência com Separate Ways é uma interpretação delimitada da decisão de interoperabilidade nativa, e não uma classificação publicada pelos autores com esse nome. Ela não afirma que todas as funções dos produtos estejam isoladas, que nenhuma ponte externa exista ou que os dois protocolos sejam impossíveis de integrar. O caso não usa a proibição Portfolio/Engagement do thndr-mcp como prova, porque esses contextos compartilham o núcleo.",
        "base": [modeling_base],
        "framework_category_constraint": "Separate Ways é uma decisão de limite e custo de integração. Context Mapper serve para estudar e registrar relações; não se encontrou um componente de runtime que implemente essa decisão automaticamente. Não se inventa uma exceção ao critério de framework: o papel da base é modelagem, e o código do produto prova a escolha aplicada.",
        "application_sources": [
            source(ATPROTO, "packages/pds/src/api/com/atproto/repo/putRecord.ts", [(59, 82), (115, 143)], "O PDS recebe registros por coleção e resolve/autentica a identidade do repositório pelo DID.", "LICENSE.txt", "MIT OR Apache-2.0"),
            source(ATPROTO, "packages/repo/src/repo.ts", [(37, 69), (158, 174)], "O modelo nativo gera repositórios e commits assinados associados ao DID.", "LICENSE.txt", "MIT OR Apache-2.0"),
            source(MASTODON, "app/lib/activitypub/activity.rb", [(1, 16), (23, 45)], "O outro produto interpreta tipos de atividades e seus objetos no modelo ActivityPub.", "LICENSE", "AGPL-3.0-or-later"),
            source(MASTODON, "app/lib/activitypub/activity/create.rb", [(3, 27)], "O caminho de criação processa a atividade e interpreta o ator e o objeto nativos desse contexto.", "LICENSE", "AGPL-3.0-or-later"),
            source(MASTODON, "package.json", [(1, 12)], "O manifesto fixa a declaração AGPL-3.0-or-later, complementando o texto integral da licença lido.", "LICENSE", "AGPL-3.0-or-later"),
        ],
        "published_decision": web_document("ddd-atproto-separate-protocol-decision", [(69, 85)], "A decisão oficial identifica ActivityPub, explica o custo de adaptar o modelo e escolhe o protocolo separado."),
        "canonical_reference": paper("ddd-evans-reference", [37], "Separate Ways escolhe independência quando a integração acrescenta custo maior que seu benefício, em vez de supor que todo domínio deve ser integrado."),
    },
]

result = {
    "schema_version": 1,
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Somente quatro relações estratégicas DDD: Shared Kernel, Customer/Supplier, Conformist e Separate Ways.",
    "independent_review": "PENDING",
    "proof_level": "Decisões, código e licenças em revisões fixadas. Nenhum software foi iniciado; a suíte de arquitetura foi apenas lida.",
    "rows": rows,
    "summary": {"recommended_source_matches": 2, "kept_pending_with_primary_evidence": 2},
    "write_scope": "Somente execution/curation/rare-support/ddd*; nenhum MDX, matriz ou seleção do curador foi alterado.",
}
target = BASE / "ddd-patterns-evidence.json"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
receipt = {
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "artifact": str(target),
    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    **result["summary"],
}
(BASE / "ddd-completion-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
