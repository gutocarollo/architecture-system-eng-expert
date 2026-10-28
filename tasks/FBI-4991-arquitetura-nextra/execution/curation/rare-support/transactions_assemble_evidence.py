"""Assemble source-only TCC, choreography-saga and historical-strangler evidence."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


BASE = Path(__file__).resolve().parent
CURATION = BASE.parent
SOURCE_CACHE = json.loads((CURATION / "sources.json").read_text())
LICENSE_CACHE = json.loads((CURATION / "revision-licenses.json").read_text())
MATRIX = json.loads((CURATION / "matrix.json").read_text())["concepts"]
REVISIONS = {
    "openstack/nova": "2ad1f119019437093f480f0c53b8ca3417560078",
    "mastodon/mastodon": "d0b3f3263ba59da24c4fa179064a160106b90a81",
    "grafana/grafana": "efe95b4c213a64acd9566f658b21fb6c11597b32",
    "rails/rails": "c3466ea00d7121798e3aa3144ffdf7174b81d8cb",
    "eventuate-tram/eventuate-tram-core": "e472ed72b8635d0488a95d0892b8901c0158a7d1",
}


def source(repo, path, ranges, claim, revision=None):
    revision = revision or REVISIONS[repo]
    candidates = [
        item for item in SOURCE_CACHE.values()
        if item.get("repo") == repo and item.get("path") == path
        and item.get("revision") == revision and item.get("http_status") == 200
        and Path(item.get("artifact", "/missing")).is_file()
    ]
    if candidates:
        item = candidates[0]
        receipt = {key: item.get(key) for key in [
            "repo", "path", "revision", "url", "raw_url", "http_status",
            "observed_utc", "sha256", "line_count", "artifact",
        ]}
        receipt["reused_curator_capture"] = True
    else:
        artifact = BASE / ("transactions-" + repo.replace("/", "--") + "--" + path.replace("/", "--"))
        receipt = json.loads(artifact.with_name(artifact.name + ".receipt.json").read_text())
        receipt["reused_curator_capture"] = False
    artifact = Path(receipt["artifact"])
    raw = artifact.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if receipt.get("sha256") and receipt["sha256"] != digest:
        raise ValueError(f"Source bytes changed: {artifact}")
    lines = raw.decode().splitlines()
    result = {
        "kind": "FILE",
        **receipt,
        "inspected_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": digest,
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
    cached_license = LICENSE_CACHE.get(repo + "@" + revision)
    if cached_license and Path(cached_license.get("artifact", "/missing")).is_file():
        result["license"] = cached_license
        Path(cached_license["artifact"]).read_text()
    else:
        paths = {
            "openstack/nova": "ddd-followon-openstack--nova--LICENSE",
            "mastodon/mastodon": "ddd-mastodon--mastodon--LICENSE",
            "grafana/grafana": "transactions-grafana--grafana--LICENSE",
            "rails/rails": "transactions-rails--rails--MIT-LICENSE",
            "eventuate-tram/eventuate-tram-core": "transactions-eventuate-tram--eventuate-tram-core--LICENSE.md",
        }
        license_artifact = BASE / paths[repo]
        result["license"] = {
            **json.loads(license_artifact.with_name(license_artifact.name + ".receipt.json").read_text()),
            "status": "READ",
            "excerpt": "\n".join(license_artifact.read_text().splitlines()[:7]),
        }
    return result


def reused_base(concept_id, terms):
    item = next(row for row in MATRIX if row["concept_id"] == concept_id)["base"][0]
    path = Path(item["artifact"])
    lines = path.read_text().splitlines()
    hits = [(i, line) for i, line in enumerate(lines, 1) if any(term in line for term in terms)]
    return {
        "kind": "REUSED_CURATOR_FRAMEWORK_REFERENCE",
        **{key: item.get(key) for key in ["repo", "path", "revision", "url", "artifact", "sha256", "license"]},
        "inspected_utc": datetime.now(timezone.utc).isoformat(),
        "selected_lines": [{"line": i, "excerpt": line} for i, line in hits[:10]],
    }


def document(slug, fragment):
    receipt = json.loads((BASE / ("transactions-" + slug + ".receipt.json")).read_text())
    path = BASE / ("transactions-" + slug + ".txt")
    lines = path.read_text().splitlines()
    hits = [(i, line) for i, line in enumerate(lines, 1) if fragment.casefold() in line.casefold()]
    return {**receipt, "text_artifact": str(path), "selected_text": [{"line": i, "text": line} for i, line in hits[:3]]}


rows = [
    {
        "concept_id": "tcc-try-confirm-cancel",
        "decision": "RECOMMEND_AUTHOR_SOURCE_MATCH_BOUNDED_TCC_INTERPRETATION",
        "independent_review": "PENDING",
        "application_kind": "PRODUCT_OSS",
        "application_scope": "Reserva, confirmação e reversão de alocações de recursos de compute durante resize/cold migration no Nova.",
        "mechanism": "No Try, o Nova mantém os recursos da origem sob o consumidor migration e reserva os recursos do destino sob o consumidor instance. A tentativa pode falhar antes da mudança ser aceita. No Confirm, a instância fica no destino e o Nova remove a instância antiga e a reserva da origem. No Cancel, o destino é destruído, seu uso local é liberado e a alocação original volta ao consumidor instance, substituindo a alocação do destino. O contexto de migração guarda as versões antiga e nova necessárias à decisão.",
        "classification_basis": "É uma interpretação TCC do ciclo de reservas efetivamente implementado. Os autores do Nova não foram apresentados como usuários do Seata nem como autores desse rótulo.",
        "limits": "O recorte não equivale a uma garantia TCC global sobre todos os recursos de uma nuvem. A documentação distingue alocações Placement dos claims de recursos locais. O código avisa sobre provedores compartilhados no caminho de reversão e admite falhas de limpeza na confirmação. Não foram exercitados recuperação, timeout ou todos os participantes de volumes e redes.",
        "base": [reused_base("tcc-try-confirm-cancel", ["COMMIT_METHOD", "ROLLBACK_METHOD", "commitMethod", "rollbackMethod"])],
        "base_application_relationship": "Seata é a referência de framework para os callbacks TCC; Nova implementa seu próprio ciclo de reservas.",
        "application": [
            source("openstack/nova", "doc/source/contributor/resize-and-cold-migrate.rst", [(53, 67), (74, 89)], "A documentação primária explica reserva dupla, confirmação que libera a origem e reversão que libera o destino."),
            source("openstack/nova", "nova/compute/resource_tracker.py", [(254, 265), (295, 316), (631, 663)], "O tracker emite o ticket de recursos e distingue a liberação da versão antiga e da nova."),
            source("openstack/nova", "nova/compute/manager.py", [(4961, 4985), (5014, 5023), (5059, 5091), (5120, 5136), (5610, 5654), (5690, 5700), (5813, 5838)], "Os caminhos reais confirmam ou revertem o resize e coordenam a destruição e a liberação das reservas correspondentes."),
            source("openstack/nova", "nova/scheduler/client/report.py", [(1635, 1649), (1712, 1731), (2042, 2066), (2068, 2110)], "O cliente cria as reservas de recursos no Placement. Na reversão, a API recebe a remoção da reserva sob migration e a substituição da reserva instance pelos recursos originais."),
        ],
    },
    {
        "concept_id": "choreography-saga",
        "decision": "RECOMMEND_AUTHOR_SOURCE_MATCH_FEDERATED_FOLLOW_COMPENSATION",
        "independent_review": "PENDING",
        "application_kind": "PRODUCT_OSS",
        "application_scope": "Pedido e autorização de follow entre duas instâncias Mastodon, incluindo recusa e cancelamento.",
        "mechanism": "A instância A grava um FollowRequest local e envia Follow ao inbox de B. B decide segundo seu estado local: pode gravar e autorizar a relação e responder Accept, ou recusar por uma regra de negócio e responder Reject. Accept faz A consolidar a relação local. Reject compensa o pedido já gravado em A e pode desfazer uma relação já consolidada. Se A cancela, ela remove seu pedido ou relação e envia Undo; B remove sua cópia correspondente. As mensagens são correlacionadas pela URI do Follow. Os participantes reagem às atividades; o caminho não depende de um coordenador de transação global.",
        "transaction_boundaries": "O lockfile fixa ActiveRecord 8.1.4. Sua implementação envolve save/destroy em transações locais e documenta o limite por conexão. Os métodos de interação do Mastodon criam ou removem registros locais; DeliveryWorker faz um POST HTTP para o inbox remoto. A outra instância modifica seus próprios registros ao tratar a atividade. Isso não coloca as duas bases em uma transação SQL comum.",
        "compensation_cases": [
            {"failure": "B recusa o Follow porque o alvo bloqueia o remetente ou não aceita a operação.", "committed_effect": "A já gravou o pedido local antes de enviar Follow.", "compensation": "B emite Reject; o handler em A chama reject! no pedido ou UnfollowService na relação."},
            {"failure": "A cancela o pedido enquanto B o processa, ou desfaz a relação.", "committed_effect": "Pode haver pedido ou relação persistida em ambos os participantes.", "compensation": "A apaga o estado local e emite Undo; B remove o pedido ou Follow correspondente. O handler também trata a chegada de Undo antes do Follow."},
        ],
        "classification_basis": "A classificação é uma interpretação da coreografia de transações locais com compensações semânticas, sustentada pelo fluxo de código. Não é uma alegação de que Mastodon usa Eventuate ou denomina esse fluxo Saga.",
        "limits": "Não se afirma atomicidade de todo handler, entrega exatamente uma vez, outbox transacional ou recuperação garantida de toda falha. A entrega tem retries finitos e estados de falha. Undo Accept por referência não é implementado no recorte, como o próprio código registra; a prova de compensação escolhida usa Reject e Undo Follow.",
        "base": [
            source("eventuate-tram/eventuate-tram-core", "eventuate-tram-events/src/main/java/io/eventuate/tram/events/subscriber/DomainEventDispatcher.java", [(24, 54)], "O framework de referência despacha eventos por agregado e tipo para handlers registrados. O caminho correto desta revisão é eventuate-tram-events."),
            source("rails/rails", "activerecord/lib/active_record/transactions.rb", [(64, 90), (379, 389)], "A base de persistência realmente declarada pelo aplicativo delimita save/destroy e não oferece uma transação distribuída entre conexões."),
        ],
        "application": [
            source("mastodon/mastodon", "Gemfile.lock", [(69, 80), (663, 676)], "O produto declara Rails e ActiveRecord 8.1.4, correspondentes à implementação de framework verificada."),
            source("mastodon/mastodon", "app/models/concerns/account/interactions.rb", [(46, 68), (97, 100)], "O participante grava seus pedidos e relações locais e oferece a operação de remoção."),
            source("mastodon/mastodon", "app/services/follow_service.rb", [(40, 45), (70, 80), (93, 95)], "O pedido é gravado antes do envio de Follow à instância remota."),
            source("mastodon/mastodon", "app/lib/activitypub/activity/follow.rb", [(7, 38), (41, 44)], "B aplica suas regras locais, persiste o pedido ou emite Reject e pode autorizar automaticamente."),
            source("mastodon/mastodon", "app/services/authorize_follow_service.rb", [(6, 25)], "A autorização local emite Accept ao inbox do solicitante."),
            source("mastodon/mastodon", "app/lib/activitypub/activity/accept.rb", [(4, 12), (18, 33)], "A resposta Accept consolida a relação local do solicitante."),
            source("mastodon/mastodon", "app/lib/activitypub/activity/reject.rb", [(4, 27)], "Reject compensa tanto o pedido pendente quanto uma relação já existente."),
            source("mastodon/mastodon", "app/models/follow_request.rb", [(34, 48), (54, 60)], "O modelo liga a autorização à relação, remove o pedido e define reject! como remoção; a URI identifica o pedido."),
            source("mastodon/mastodon", "app/services/unfollow_service.rb", [(25, 39), (51, 65)], "A remoção local emite Undo Follow ao outro participante."),
            source("mastodon/mastodon", "app/lib/activitypub/activity/undo.rb", [(10, 13), (45, 55), (90, 106)], "A compensação remota remove pedido ou relação e possui caminho para compensação anterior à chegada da atividade original."),
            source("mastodon/mastodon", "app/workers/activitypub/delivery_worker.rb", [(11, 20), (25, 36), (49, 54), (61, 75)], "O transporte assíncrono entrega o evento por HTTP e tem política explícita de retry e falhas."),
        ],
        "primary_docs": [document("mastodon-activitypub", "Undo a previous Follow"), document("saga-definition", "Choreography - each local transaction")],
    },
    {
        "concept_id": "strangler-fig",
        "decision": "RECOMMEND_AUTHOR_SOURCE_MATCH_HISTORICAL_PANEL_REPLACEMENT",
        "independent_review": "PENDING",
        "application_kind": "PRODUCT_OSS",
        "application_scope": "Migração histórica do subsistema de painéis Grafana de AngularJS para React.",
        "mechanism": "A plataforma React foi apresentada como sucessora enquanto plugins Angular continuavam aceitos. Na versão 9.5, um carregador apresenta ambos como PanelPlugin e DashboardPanel escolhe o caminho Angular ou React. A ponte Angular cria o componente legado dentro da fronteira moderna. Na revisão 10.4 capturada pelo curador, o dispatch continua e o carregador também instala um wrapper React quando só há um controller Angular. Assim, painéis novos e antigos coexistem e podem ser substituídos por partes; o plano posterior prevê desligar e remover a tecnologia antiga.",
        "classification_basis": "A documentação primária sustenta a intenção de substituição gradual. Chamar esse recorte de Strangler é a interpretação arquitetural da curadoria; não se atribui esse nome aos autores sem uma fonte.",
        "limits": "O objeto substituído é a apresentação de painéis e seu SDK, não todo o Grafana. A revisão 9.5 e a revisão 10.4 são testemunhos separados da coexistência, e não um único checkout. A documentação de remoção é histórica e não prova uma implantação atual específica. Config migration isolada não foi tratada como prova; o caso contém dispatch e execução real dos dois caminhos.",
        "base": [reused_base("strangler-fig", ["createProxyServer", "target", "web("])],
        "base_application_relationship": "httpxy é a referência de framework para a forma HTTP de mediação. Grafana aplica uma fronteira de componentes e seu próprio carregador de plugins; não se afirma dependência de httpxy.",
        "application": [
            source("grafana/grafana", "public/app/features/plugins/importPanelPlugin.ts", [(36, 52)], "Em 9.5, a mesma fronteira carrega exportações React ou adapta PanelCtrl para PanelPlugin."),
            source("grafana/grafana", "public/app/features/dashboard/dashgrid/DashboardPanel.tsx", [(76, 109)], "Em 9.5, angularPanelCtrl seleciona PanelChromeAngular; o outro caminho usa PanelStateWrapper."),
            source("grafana/grafana", "public/app/features/dashboard/dashgrid/PanelChromeAngular.tsx", [(143, 163)], "A ponte executa o componente Angular legado com o painel, dashboard e dimensões da fronteira comum."),
            source("grafana/grafana", "public/app/features/dashboard/dashgrid/PanelStateWrapper.tsx", [(475, 511)], "O outro caminho instancia o componente React fornecido pelo plugin."),
            source("grafana/grafana", "public/app/plugins/panel/graph/module.ts", [(374, 380)], "O painel Graph legado declara o controller Angular no mesmo snapshot 9.5."),
            source("grafana/grafana", "public/app/plugins/panel/timeseries/module.tsx", [(1, 15)], "O painel TimeSeries declara um componente React no mesmo snapshot 9.5."),
            source("grafana/grafana", "public/app/features/dashboard/dashgrid/DashboardPanel.tsx", [(89, 124)], "A captura 10.4 conserva o dispatch por tecnologia do plugin.", revision="03f502a94d17f7dc4e6c34acdf8428aedd986e4c"),
            source("grafana/grafana", "public/app/features/plugins/importPanelPlugin.ts", [(65, 83)], "Na captura 10.4, o carregador adapta PanelCtrl e instala getAngularPanelReactWrapper para a fronteira de componentes.", revision="03f502a94d17f7dc4e6c34acdf8428aedd986e4c"),
            source("grafana/grafana", "public/app/angular/panel/AngularPanelReactWrapper.tsx", [(21, 51)], "O wrapper React monta e alimenta o componente Angular durante a coexistência.", revision="03f502a94d17f7dc4e6c34acdf8428aedd986e4c"),
        ],
        "primary_history": [
            document("grafana-v7-transition", "Plugins built using Angular still work"),
            document("grafana-angular-removal", "In Grafana 12"),
        ],
    },
]

result = {
    "schema_version": 1,
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Somente TCC, Choreography Saga e Strangler Fig histórico.",
    "classification_owner": "Autor da investigação; nenhuma revisão independente é assinada por este pacote.",
    "proof_level": "Leitura de código, contratos e história primária em revisões fixadas. Nenhuma aplicação foi iniciada e nenhum teste foi executado.",
    "rows": rows,
    "summary": {"recommended_author_source_matches": 3, "independent_reviews_pending": 3},
    "context7": "A consulta de documentação foi tentada e devolveu limite mensal. A implementação Rails 8.1.4 e a documentação oficial foram consultadas diretamente.",
    "write_scope": "Somente execution/curation/rare-support/; matriz e MDX não foram alterados.",
}
target = BASE / "transactions-source-recommendations.json"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
receipt = {
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "artifact": str(target),
    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    **result["summary"],
}
(BASE / "transactions-completion-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
