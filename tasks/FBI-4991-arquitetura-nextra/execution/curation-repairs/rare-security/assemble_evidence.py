from pathlib import Path
import copy
import datetime
import hashlib
import json
import subprocess


ROOT = Path("tasks/FBI-4991-arquitetura-nextra/execution")
OUTPUT = ROOT / "curation-repairs/rare-security"
REVIEW = ROOT / "reviews/curation-second.concepts.json"
TELEPORT = ("gravitational/teleport", "1283425b60ec5f60d509ba4c791183d452923ff7")
ISTIO = ("istio/istio", "4e2c1c576e33a7b411ee7f38ac4bb9dd45c36631")
KEYCLOAK = ("keycloak/keycloak", "8a081db466da3ff8de74efab2f3d9844277c18ba")
SPRING = ("spring-projects/spring-security", "42192f9591763875eb2986bc8fd695a2eebefb02")
SPIFFE = ("spiffe/go-spiffe", "77c6d2e0c1203e36804e26a02faa8f893d72e7e5")
SSH = ("golang/crypto", "cf169cd0986fa0e2e0963ee5f8d234885f869750")


def digest(data):
    return hashlib.sha256(data).hexdigest()


sources = {}
for receipt_path in sorted(OUTPUT.glob("*.receipt.json")):
    item = json.loads(receipt_path.read_text())
    data = Path(item["artifact"]).read_bytes()
    assert digest(data) == item["sha256"]
    assert len(data.splitlines()) == item["line_count"]
    sources[(item["repo"], item["revision"], item["path"])] = item

licenses = {}
for project, path, spdx in [
    (TELEPORT, "LICENSE", "AGPL-3.0-or-later"),
    (ISTIO, "LICENSE", "Apache-2.0"),
    (KEYCLOAK, "LICENSE.txt", "Apache-2.0"),
    (SPRING, "LICENSE.txt", "Apache-2.0"),
    (SPIFFE, "LICENSE", "Apache-2.0"),
    (SSH, "LICENSE", "BSD-3-Clause"),
]:
    item = copy.deepcopy(sources[(*project, path)])
    item["license_spdx"] = spdx
    if project == TELEPORT:
        item["license_basis"] = "O LICENSE contém AGPL versão 3. Os headers dos arquivos lib/srv/authhandlers.go e lib/services/role.go, linhas 5–8, permitem versão 3 ou posterior. A API tem licença própria; não é a superfície selecionada."
    licenses["@".join(project)] = item


def evidence(project, path, ranges, role, proves):
    item = copy.deepcopy(sources[(*project, path)])
    lines = Path(item["artifact"]).read_text().splitlines()
    item["role"] = role
    item["proves"] = proves
    item["inspected_ranges"] = ranges
    item["excerpts"] = []
    for start, end in ranges:
        assert 1 <= start <= end <= len(lines), (path, start, end)
        item["excerpts"].append({"start_line": start, "end_line": end, "url": f'{item["url"]}#L{start}-L{end}', "text": "\n".join(f"{line + 1}: {lines[line]}" for line in range(start - 1, end))})
    return item


K = "services/src/main/java/org/keycloak/"
S = "oauth2/oauth2-client/src/main/java/org/springframework/security/oauth2/client/"

concepts = [
    {
        "concept_id": "zero-trust",
        "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
        "independent_review": "PENDING",
        "base_role": "O mecanismo reutilizável de decisão é RoleSet/checkAccess do Teleport, chamado por accessChecker. Go SSH é a base adicional de autenticação de certificado e prova de posse; a autenticação sozinha não sustenta a classificação.",
        "application_role": "O servidor SSH do Teleport é o produto OSS real. O exemplo é o acesso normal de um usuário a um Node e login de sistema operacional específicos.",
        "mechanism": "O servidor registra PublicKeyCallback e VerifiedPublicKeyCallback no adaptador SSH. O primeiro decodifica a identidade do certificado e autentica sua autoridade e metadados. Para um Node, ele avalia o servidor alvo e o login solicitado. Essa avaliação obtém papéis e atributos da identidade, cria um accessChecker e chama CheckConditionalAccess com o recurso e NewLoginMatcher. RoleSet verifica primeiro as regras de negação e depois exige que namespace, labels e matchers de uma regra de permissão correspondam. Sem permissão, o callback retorna erro e a autenticação é recusada. Quando a decisão tem pré-condições, a callback posterior à prova de posse verifica quais exigem autenticação adicional antes de prosseguir.",
        "review_gap_addressed": "A seleção agora liga a identidade autenticada à política por recurso e login, à decisão de negação e ao callback que controla a entrada no servidor; não se limita ao handshake SSH.",
        "limits": [
            "A interpretação é um recorte de acesso com Zero Trust: identidade e política são avaliadas para o recurso solicitado. Isso não certifica toda uma organização ou uma implantação como aderente à NIST SP 800-207.",
            "O caminho escolhido é o login comum em Node. O código possui uma exceção explícita para ingresso em sessão moderada sob condições específicas e caminhos separados para proxy, OpenSSH e identidades scoped; não se afirma que todos executem a mesma função.",
            "MFA e confiança no dispositivo dependem de política. A seleção mostra a integração das condições, mas não atesta que estejam habilitadas em uma instalação real nem promete revalidação contínua de toda operação durante uma sessão.",
            "A licença dos arquivos lib selecionados é AGPL-3.0-or-later, conforme seus headers no SHA fixado. Não se aplica a eles a licença Apache da API nem se faz afirmação sobre licenças de binários comerciais.",
        ],
        "licenses": ["@".join(TELEPORT), "@".join(SSH)],
        "evidence": [
            evidence(TELEPORT, "lib/services/role.go", [[3030, 3036], [3087, 3123], [3158, 3204], [3221, 3252]], "base", "O avaliador executa deny antes de allow, combina labels do recurso e matchers do login, considera condições de dispositivo e nega quando nenhuma regra permite."),
            evidence(TELEPORT, "lib/services/access_checker.go", [[345, 353], [670, 705]], "identity_policy_bridge", "O accessChecker embute RoleSet e passa username e traits da identidade junto com o recurso e estado de acesso ao avaliador."),
            evidence(TELEPORT, "lib/srv/authhandlers.go", [[388, 420], [521, 537], [618, 644], [1246, 1267], [1270, 1298], [1369, 1377]], "application", "O callback autentica o certificado e vincula a identidade a servidor alvo e login; falha de RBAC retorna erro ao handshake."),
            evidence(TELEPORT, "lib/srv/authhandlers.go", [[716, 738], [750, 783]], "conditional_effect", "O callback após prova de posse trata as pré-condições e encaminha à autenticação adicional quando exigida; condição desconhecida falha fechada."),
            evidence(TELEPORT, "lib/srv/regular/sshserver.go", [[1016, 1026], [1533, 1538]], "real_caller", "O daemon instala os callbacks e recusa um canal quando não consegue construir a identidade autorizada da conexão."),
            evidence(TELEPORT, "lib/sshutils/server.go", [[248, 249], [533, 540]], "transport_bridge", "O adaptador instala as callbacks no ssh.ServerConfig e executa ssh.NewServerConn com a configuração."),
            evidence(SSH, "ssh/certs.go", [[385, 415], [430, 469]], "authentication_framework", "A biblioteca confere autoridade, principal, validade temporal e assinatura do certificado."),
            evidence(SSH, "ssh/server.go", [[809, 820], [878, 899]], "proof_of_possession", "O handshake executa a callback, verifica a assinatura do cliente e chama VerifiedPublicKeyCallback somente após aceitação da chave e prova de posse."),
        ],
        "official_context": [
            {"url": "https://csrc.nist.gov/pubs/sp/800/207/final", "scope": "A definição canônica distingue autenticação de autorização e concentra a decisão no recurso, sem confiança implícita apenas pela localização de rede."},
            {"url": "https://goteleport.com/docs/zero-trust-access/rbac-get-started/", "scope": "A documentação primária explica que o agente verifica papéis para a conexão a cada recurso e nega a conexão sem permissão."},
        ],
    },
    {
        "concept_id": "service-to-service-identity",
        "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
        "independent_review": "PENDING",
        "base_role": "go-spiffe oferece configuração mTLS que valida X509-SVID e autoriza o SPIFFE ID verificado. AuthorizeID permite escolher um ID específico.",
        "application_role": "Istio é o produto OSS de infraestrutura. O recorte acompanha o agente e a CA na emissão e entrega de identidade de uma carga Kubernetes, mais a geração de configuração de validação e autorização para o proxy.",
        "mechanism": "A requisição SDS faz o agente pedir um segredo. O cache constrói uma URI SPIFFE a partir de trust domain, namespace e service account e gera um CSR. CitadelClient envia o pedido à CA com credenciais por RPC. A CA autentica o JWT por TokenReview, exige namespace e service account e constrói a identidade SPIFFE desses valores verificados. Ela usa essa identidade como SubjectIDs do certificado; o gerador de SAN codifica o prefixo spiffe:// como URI, em vez de confiar apenas no nome solicitado no CSR. O agente devolve certificado e chave por SDS ao Envoy. No lado consumidor, ISTIO_MUTUAL configura o certificado local, a raiz e o matcher de SAN do par. A política source.principal é convertida em principal autenticado do RBAC; o builder gera o filtro de autorização que o Envoy aplica.",
        "review_gap_addressed": "A cadeia inclui atestação por JWT, namespace/service account, URI SPIFFE, assinatura com SAN imposto pela CA, SDS e configuração de validação e autorização da identidade do par. Não depende do uso de certificado TLS genérico.",
        "limits": [
            "A identidade Kubernetes deste caminho representa a service account dentro do namespace e trust domain. Diferentes pods que usam a mesma service account compartilham essa identidade lógica; não se alega um identificador exclusivo por processo.",
            "A análise demonstra o caminho Kubernetes em modo sidecar e as configurações geradas para mTLS e políticas de principal. Não demonstra um cluster em execução nem abrange todos os caminhos ambient, VMs ou CAs externas.",
            "mTLS e autorização dependem da configuração. Istio permite modo permissivo e políticas opcionais; não se deduz que qualquer requisição em toda instalação esteja autenticada e autorizada da mesma forma.",
            "A CA possui um ramo de impersonation para agentes de nó explicitamente autorizados. A cadeia descrita usa o ramo padrão sem impersonation.",
            "go-spiffe e Istio são duas implementações do mesmo modelo de identidade. Não se afirma que o código Istio selecionado chame go-spiffe; o caller completo dentro do produto é mostrado separadamente.",
        ],
        "licenses": ["@".join(SPIFFE), "@".join(ISTIO)],
        "evidence": [
            evidence(SPIFFE, "spiffetls/tlsconfig/config.go", [[58, 75], [110, 128], [171, 203]], "base", "A configuração apresenta SVID, valida a cadeia/SPIFFE ID do peer e só então executa o autorizador."),
            evidence(SPIFFE, "spiffetls/tlsconfig/authorizer.go", [[9, 22], [42, 47]], "identity_authorizer", "AuthorizeID aplica MatchID ao ID real extraído do certificado já verificado."),
            evidence(ISTIO, "security/pkg/nodeagent/sds/sdsservice.go", [[129, 150], [270, 276], [380, 397]], "real_caller_and_delivery", "O servidor SDS atende StreamSecrets, pede GenerateSecret e devolve certificado e chave no segredo TLS do Envoy."),
            evidence(ISTIO, "security/pkg/nodeagent/cache/secretcache.go", [[290, 304], [778, 815]], "application", "O agente usa trust domain, namespace e service account para criar a URI do CSR e solicita assinatura à CA."),
            evidence(ISTIO, "security/pkg/nodeagent/caclient/providers/citadel/client.go", [[79, 114], [138, 146]], "ca_caller_bridge", "CSRSign chama CreateCertificate e o cliente gRPC inclui o provedor de credenciais por RPC."),
            evidence(ISTIO, "security/pkg/server/ca/authenticate/kubeauth/kube_jwt.go", [[109, 144]], "attested_identity", "A CA valida o JWT pelo Kubernetes e constrói Caller.Identities a partir de namespace e service account confirmados."),
            evidence(ISTIO, "security/pkg/k8s/tokenreview/k8sauthn.go", [[41, 59], [87, 112]], "tokenreview", "O servidor pede TokenReview com audiência e exige autenticação e identidade de service account antes de extrair namespace e conta."),
            evidence(ISTIO, "pkg/spiffe/spiffe.go", [[80, 81], [94, 110]], "spiffe_identifier", "O formato emitido é spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>."),
            evidence(ISTIO, "security/pkg/server/ca/server.go", [[75, 118], [122, 133]], "issuance_authority", "A CA autentica o caller e usa suas identidades como SANs. O pedido de impersonation exige autorização específica antes de substituí-las."),
            evidence(ISTIO, "security/pkg/pki/ca/ca.go", [[400, 410], [478, 508]], "signer", "O signer leva SubjectIDs autenticados até GenCertFromCSR."),
            evidence(ISTIO, "security/pkg/pki/util/generate_cert.go", [[245, 258], [291, 313]], "certificate_construction", "O certificado é criado com extensão SAN construída dos SubjectIDs recebidos do signer."),
            evidence(ISTIO, "security/pkg/pki/util/san.go", [[70, 96]], "uri_san_encoding", "O gerador reconhece spiffe:// e codifica a identidade como TypeURI."),
            evidence(ISTIO, "pilot/pkg/networking/core/cluster_tls.go", [[142, 156], [453, 466], [498, 505]], "peer_validation_configuration", "ISTIO_MUTUAL usa certificado e raiz por SDS e configura matcher de SAN; quando não há SAN explícito usa as service accounts do serviço."),
            evidence(ISTIO, "pilot/pkg/security/authz/model/model.go", [[124, 135], [182, 210]], "authorization_policy_bridge", "A regra source.principals passa ao gerador de principal e é incluída na política RBAC."),
            evidence(ISTIO, "pilot/pkg/security/authz/model/generator.go", [[244, 253]], "spiffe_principal_matcher", "O matcher de source.principal recebe o prefixo URI SPIFFE."),
            evidence(ISTIO, "pilot/pkg/security/authz/model/principal.go", [[60, 79]], "authenticated_peer", "O principal usa identidade autenticada do Envoy ou o estado io.istio.peer_principal, conforme o modo configurado."),
            evidence(ISTIO, "pilot/pkg/security/authz/builder/builder.go", [[197, 205], [350, 362], [393, 411]], "authorization_effect_configuration", "O builder gera políticas ALLOW/DENY e as coloca em um filtro HTTP RBAC do Envoy, fora do ramo de avaliação apenas em shadow."),
        ],
        "official_context": [{"url": "https://istio.io/latest/docs/concepts/security/", "scope": "As seções Istio identity, certificate management e secure naming explicam a emissão, SDS, verificação de service account do par e autorização no proxy."}],
    },
    {
        "concept_id": "token-exchange",
        "recommendation": "AUTHOR_SOURCE_MATCH_REPAIR",
        "independent_review": "PENDING",
        "base_role": "Spring Security fornece um cliente RFC 8693 real, com TokenExchangeGrantRequest, conversão de parâmetros e POST ao token endpoint.",
        "application_role": "Keycloak Server é o produto OSS real. O recorte é o provider StandardTokenExchangeProvider, ligado a TOKEN_EXCHANGE_STANDARD_V2, para troca interna entre clientes do mesmo realm.",
        "mechanism": "No framework, o provider obtém um subject token, constrói TokenExchangeGrantRequest e chama o cliente HTTP. O conversor envia o grant token-exchange com subject_token, subject_token_type e requested_token_type. No Keycloak, TokenEndpoint autentica o cliente e despacha o grant. TokenExchangeGrantType escolhe o provider compatível e dispara a política do pedido. O provider padrão exige que a funcionalidade esteja habilitada para o cliente e valida o access token de entrada, incluindo assinatura, emissor, validade e revogação pelo verificador. A regra de audiência rejeita cliente público, audiência desabilitada e solicitante ausente da audiência do subject token, salvo troca do próprio token. Depois, ele cria um novo access token com o contexto de escopos, confere as audiências efetivas, aplica políticas da resposta e devolve o novo token codificado com issued_token_type.",
        "review_gap_addressed": "A base anterior de authorization_code foi substituída por código que envia subject_token em grant RFC 8693. O produto tem caller, autenticação do cliente, verificação do token, autorização por audiência/política e emissão da nova resposta.",
        "limits": [
            "O recorte é Standard Token Exchange V2 interno-interno do SHA fixado. Não se atribuem a ele as capacidades do provider legacy V1, como impersonation arbitrária ou troca de tokens externos.",
            "O código exige habilitação de standard token exchange no cliente. Não se infere configuração de qualquer realm real nem se afirma que o recurso esteja ativo em produção.",
            "O pedido de audience filtra e valida audiências efetivamente disponíveis; ele não concede automaticamente uma nova audiência. Os escopos e client policies podem produzir comportamento além de downscoping; não se promete que toda troca reduza privilégios.",
            "Spring e Keycloak são exemplos independentes do protocolo, não uma integração executada. Spring envia subject_token_type=jwt para uma instância Jwt; o provider padrão Keycloak selecionado aceita access_token. Uma composição real precisa escolher o tipo aceito e configurar o cliente.",
            "Não foi executado um fluxo HTTP de teste. A evidência é a cadeia implementada no código fixado e sua documentação primária.",
        ],
        "licenses": ["@".join(SPRING), "@".join(KEYCLOAK)],
        "evidence": [
            evidence(SPRING, S + "endpoint/TokenExchangeGrantRequest.java", [[48, 71], [96, 117]], "base", "A requisição exige grant TOKEN_EXCHANGE e subject token e monta os parâmetros RFC 8693, em vez de authorization_code."),
            evidence(SPRING, S + "TokenExchangeOAuth2AuthorizedClientProvider.java", [[45, 51], [70, 110]], "framework_caller", "O provider resolve subject token, cria a requisição e usa a resposta para obter o novo OAuth2AuthorizedClient."),
            evidence(SPRING, S + "endpoint/RestClientTokenExchangeTokenResponseClient.java", [[21, 39]], "framework_protocol_client", "O cliente declara e implementa a especialização de resposta de TokenExchangeGrantRequest."),
            evidence(SPRING, S + "endpoint/DefaultOAuth2TokenRequestParametersConverter.java", [[65, 83], [100, 102]], "protocol_parameters", "O conversor inclui grant_type e acrescenta os parâmetros específicos da troca de subject token."),
            evidence(SPRING, S + "endpoint/AbstractRestClientOAuth2AccessTokenResponseClient.java", [[86, 100], [129, 145]], "http_effect", "A implementação usa POST no token endpoint e desserializa a nova OAuth2AccessTokenResponse."),
            evidence(KEYCLOAK, K + "protocol/oidc/endpoints/TokenEndpoint.java", [[130, 163], [176, 180], [217, 221], [237, 245]], "real_caller", "O endpoint lê o grant, autentica o cliente e despacha ao provider do grant solicitado."),
            evidence(KEYCLOAK, K + "protocol/oidc/grants/TokenExchangeGrantType.java", [[45, 100]], "grant_and_policy_bridge", "O grant seleciona o provider que suporta o pedido e dispara TokenExchangeRequestContext antes da troca."),
            evidence(KEYCLOAK, K + "protocol/oidc/tokenexchange/StandardTokenExchangeProviderFactory.java", [[30, 39], [57, 70]], "v2_binding", "A factory se identifica como standard e exige TOKEN_EXCHANGE_STANDARD_V2, com prioridade maior que V1."),
            evidence(KEYCLOAK, K + "protocol/oidc/tokenexchange/StandardTokenExchangeProvider.java", [[95, 123], [126, 161], [232, 254], [349, 397], [415, 423]], "application", "O provider exige habilitação e access subject token, valida-o, aplica autorização por audiência e gera uma nova resposta com tipo de token emitido."),
            evidence(KEYCLOAK, K + "services/managers/AuthenticationManager.java", [[1555, 1593]], "subject_token_authentication", "O verificador usa emissor do realm, validade, revogação e um SignatureVerifierContext antes de aceitar o token."),
            evidence(KEYCLOAK, K + "protocol/oidc/tokenexchange/AbstractTokenExchangeProvider.java", [[219, 248]], "audience_dispatch", "A base verifica a audiência antes de escolher o contexto e emitir o token, e rejeita o solicitante fora de aud."),
            evidence(KEYCLOAK, K + "protocol/oidc/TokenManager.java", [[1295, 1299], [1471, 1499]], "token_issuance_effect", "O builder cria um access token a partir do contexto de cliente e o codifica em uma nova AccessTokenResponse."),
        ],
        "official_context": [
            {"url": "https://www.keycloak.org/securing-apps/token-exchange", "scope": "A documentação separa Standard V2 de Legacy V1, descreve os parâmetros e as regras de audiência. As capacidades do exemplo são limitadas pelo código no SHA, pois a URL pública pode evoluir."},
            {"url": "https://docs.spring.io/spring-security/reference/7.0/api/java/org/springframework/security/oauth2/client/endpoint/RestClientTokenExchangeTokenResponseClient.html", "scope": "A API oficial identifica a troca de subject token implementada pelo cliente de framework."},
        ],
    },
]

review = json.loads(REVIEW.read_text())
review_by_id = {item["concept_id"]: item for item in review["concepts"]}
for concept in concepts:
    original = review_by_id[concept["concept_id"]]
    concept["original_review_state"] = original["state"]
    concept["original_review_note"] = original["notes"]

result = {
    "schema_version": "rare-security-repairs/v1",
    "author_lane": {"agent": "/root/rare_oss_sources", "native_type": "default", "model": "gpt-6.1-sol", "reasoning_effort": "xhigh", "routing": "WARM_REUSE", "role": "DEEP_EXPLORE primary-source curation; not an independent review"},
    "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "workspace": str(Path.cwd()),
    "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "review_input": {"artifact": str(REVIEW), "sha256": digest(REVIEW.read_bytes()), "matrix_sha256_from_review": review["matrix_sha256"]},
    "write_scope": str(OUTPUT) + "/**",
    "delivery_limits": ["O pacote é uma recomendação autoral. Integração e rechecagem independente pertencem ao curador e ao reviewer.", "As gravações desta lane se limitam a rare-security. Fontes globais, matriz congelada, MDX, Jira, configuração e produção não foram editados por esta lane.", "A captura reutilizou primeiro os caches de curation e curation-repairs, conferindo os hashes. Os novos paths foram buscados em fontes primárias fixadas no mesmo SHA.", "Os antigos paths Spring DefaultTokenExchangeTokenResponseClient e TokenExchangeGrantRequestEntityConverter retornaram 404 no levantamento anterior. O pacote usa os paths atuais confirmados do RestClient e do conversor genérico, que responderam 200.", "Não houve teste de produto, build ou fluxo de autenticação executado. A prova é estática, de código primário e documentação oficial."],
    "licenses": licenses,
    "concepts": concepts,
}
destination = OUTPUT / "rare-security-recommendations.json"
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
(OUTPUT / "rare-security-manifest.json").write_text(json.dumps({"sources": list(sources.values()), "licenses": licenses}, ensure_ascii=False, indent=2) + "\n")
receipt = {"observed_utc": result["observed_utc"], "workspace": result["workspace"], "branch": result["branch"], "head": result["head"], "recommendation_count": len(concepts), "independent_review": "PENDING", "source_count": len(sources), "license_count": len(licenses), "artifact": str(destination), "sha256": digest(destination.read_bytes())}
(OUTPUT / "rare-security-completion-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
