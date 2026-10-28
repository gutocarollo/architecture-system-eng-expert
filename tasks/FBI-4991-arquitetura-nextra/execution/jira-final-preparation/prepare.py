import copy
import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone

root = pathlib.Path.cwd()
base = root / 'tasks/FBI-4991-arquitetura-nextra/execution'
out = base / 'jira-final-preparation'
observed = datetime.now(timezone.utc).isoformat()

def load(path):
    return json.loads(path.read_text())

def write(name, data):
    (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

preimage = load(out / 'jira-preimage-final-reread.json')
issue = preimage['issue']
original = issue['fields']['customfield_10054']
metadata = load(out / 'jira-story-metadata.json')
assert issue['fields']['issuetype']['id'] == '10006'
assert len(original['content']) == 63
assert any(field['fieldId'] == 'customfield_10054' for field in metadata['response']['fields'])
public = load(base / 'hosting/public-verification.json')
diagnostic = load(base / 'hosting/public-network-diagnostic-verification.json')
terminal = load(base / 'reviews/terminal.json')
assert public['releaseId'] == diagnostic['releaseId']
assert public['origin'] == diagnostic['origin']
assert len(public['anonymous']) == len(public['readBack']) == len(public['anonymousAfterWarm']) == 1397
assert all(item['status'] in (303, 401) for item in public['anonymous'] + public['anonymousAfterWarm'])
assert all(item['status'] == 200 and item['sha256Matches'] for item in public['readBack'])
assert not public['failures'] and not public['pageErrors']
assert public['wrongPasswordRejected'] and public['authenticatedHeading']
assert public['search']['actual'].endswith(public['search']['selected'])
assert public['logout']['redirectedToLogin']
assert not diagnostic['failures'] and not diagnostic['pageErrors']
assert all(item['status'] == 401 or (item['status'] == 404 and item['path'] == '/favicon.ico') for item in diagnostic['httpErrors'])
assert terminal['verdict'] == 'PASS_FOR_PROTECTED_SITE_AND_DRAFT' and not terminal['high_findings']

assessment = {
    'observed_at_utc': observed,
    'kind': 'RECORDED_ARTIFACT_RECONCILIATION_NOT_A_NEW_NETWORK_RUN',
    'verdict': 'FUNCTIONAL_PASS_WITH_RECORDED_CONSOLE_ERRORS',
    'raw_verdict_preserved': public['verdict'],
    'raw_interval_utc': [public['startedAt'], public['completedAt']],
    'diagnostic_interval_utc': [diagnostic['startedAt'], diagnostic['completedAt']],
    'origin': public['origin'],
    'release_id': public['releaseId'],
    'anonymous_denied': 1397,
    'authenticated_sha256_matches': 1397,
    'anonymous_after_cache_warm_denied': 1397,
    'password_wrong_rejected': True,
    'password_correct_authenticated': True,
    'search_destination_matches': True,
    'logout_redirected_to_login': True,
    'functional_failures': public['failures'],
    'page_errors': public['pageErrors'],
    'console_errors': public['consoleErrors'],
    'diagnostic_http_errors': diagnostic['httpErrors'],
    'interpretation': 'The raw FAIL remains preserved. Matching-release diagnostic requests attribute console errors to expected 401 responses from denied requests and the authenticated missing favicon404. This does not establish universal all-green QA or full Story acceptance.'
}
write('public-functional-assessment.json', assessment)
semantic_one = load(base / 'reviews/diagram-semantics-one-recheck.json')
semantic_two = load(base / 'reviews/diagram-semantics-two.recheck.json')
assert semantic_one['verdict'] == semantic_two['verdict'] == 'PASS_BOUNDED'
assert semantic_one['high_open_in_lane'] == semantic_two['unresolved_high'] == 0
assert len(load(base / 'reviews/diagram-semantics-one.json')['items']) == 46
assert semantic_two['scope_count'] == 45

sections = [
    ('h2', 'Resultado da execução e entrega protegida — 15 de outubro de 2026'),
    ('p', 'O curso reúne 181 documentos MDX no Nextra, 18 jornadas e 90 destinos de aprendizado. Sete casos têm origem histórica, sendo seis do MakersHub e um do Airflow; os outros onze são casos financeiros explicitamente hipotéticos. A curadoria de 310 conceitos foi confrontada com julgamentos independentes vinculados às fontes. O recibo de curadoria registra zero pendências de rechecagem, com 14 classificações de nível médio preservadas como limite ou backlog. A contagem de documentos e destinos descreve o material entregue e não certifica, por si só, a totalidade dos critérios de aceite.'),
    ('p', 'O pacote de exercícios oferece 16 executores em um ZIP com 98 arquivos e foi executado após extração sem diretório Git. Dois casos de PostgreSQL usaram um servidor real da versão 16.15 em ambiente isolado, com dados sintéticos: a correção do grão reduziu duas linhas e comissão duplicada de 200 para uma linha e comissão de 100; a comparação de revisão passou a rejeitar a escrita obsoleta. O caso Airflow executou funções históricas com substitutos controlados e demonstrou duas tentativas diante de um lock transitório. Essa prática não executou DAGs, processos Haskell nem conexões de produção.'),
    ('p', 'A base examinada do curso é 623ae1d3d34143df53c571327a508de47ab58951, acrescida das duas correções de diagramas vinculadas aos hashes dos recibos de rechecagem. A publicação registrada anteriormente oferece o site protegido em https://fazcapital-arquitetura-na-pratica.navy-teal-7786.chatgpt.site, com a implementação de acesso 1677c81236d3588736e88597e9589d942b655a25, versão nativa v2 e política pública de revisão 2. Esses recibos antecedem as correções semânticas; a versão final corrigida e sua nova verificação pública ainda precisam ser reconciliadas com a publicação. A opção B aprovada permite entrar com uma senha compartilhada, sem exigir conta ChatGPT. O servidor valida a sessão antes de entregar HTML, arquivos _next, índice _pagefind ou downloads armazenados em R2 privado. A senha e as chaves de sessão são mantidas no Keychain e nos segredos de execução.'),
    ('p', 'Na publicação anterior às correções semânticas, entre 18:13:33 e 18:15:02 UTC de 15 de outubro, a verificação pública registrou bloqueio anônimo nos 1.397 caminhos do manifesto, correspondência SHA256 nos mesmos 1.397 arquivos autenticados e novo bloqueio anônimo após aquecer o cache. O login correto, a rejeição da senha incorreta, a busca e a saída da sessão cumpriram os comportamentos examinados. failures e pageErrors permaneceram vazios. O veredito bruto FAIL foi preservado: o diagnóstico da mesma versão, entre 18:18:28 e 18:18:46 UTC, relacionou os erros de console às respostas 401 de bloqueio e ao favicon ausente com resposta 404. A avaliação funcional desses cenários é aprovada com esses erros registrados; isso não significa uma validação integral sem ressalvas.'),
    ('p', 'A auditoria terminal em reviews/terminal.json aprovou o escopo de site protegido e entrega em rascunho com PASS_FOR_PROTECTED_SITE_AND_DRAFT e zero achados HIGH. Os três julgamentos semânticos desse recibo se somam aos 46 da primeira lane e aos 45 da segunda, totalizando 94 diagramas confrontados com suas fontes ou com o modelo hipotético declarado. As duas rechecagens limitadas aos achados HIGH retornaram PASS_BOUNDED e deixaram zero HIGH aberto. A correção da linhagem recolocou o dashboard entre captação e ranking; a correção do cancelamento identificou a ação injetada pelo laboratório, sem atribuir ao navegador uma causa histórica não demonstrada. Permanecem dois apontamentos médios de comunicação visual e um apontamento baixo nos diagramas, além do backlog da curadoria. A aprovação semântica respeita as versões, os trechos e os snapshots identificados; não prova operação atual em produção, execução de DAGs ou análise causal integral do histórico.'),
    ('p', 'A classificação do histórico abrange 12.697 commits e 595 cards FBI: sete relações tiveram causa relatada e apoio no código, 290 permaneceram como relato, 35 ficaram sem evidência causal e 263 foram classificadas como mudanças às quais essa prova não se aplica. A análise causal integral continua sem confirmação. O repositório privado GitHub gutocarollo/architecture-system-eng-expert permanece fora da lista permitida do catálogo, e a fonte de autoridade para registrar Repository não foi localizada na auditoria delimitada. Existe proposta concreta de Document com patch e ensaios de geração, fora do escopo autorizado de escrita. O bloqueio de catálogo permanece aberto; este complemento mantém a Story em In Progress e a resolução vazia.'),
    ('h2', 'R18 — Entrega com senha compartilhada, sem conta ChatGPT'),
    ('p', 'O estudante que recebeu a senha deve conseguir abrir o endereço publicado sem criar ou usar uma conta ChatGPT. O servidor deve exigir uma sessão válida antes de entregar qualquer conteúdo do curso, inclusive HTML, arquivos de aplicação, índice de busca e ZIP dos exercícios. A navegação autenticada deve permitir estudar, pesquisar e baixar o pacote. A saída da sessão deve devolver o estudante à entrada protegida. Os valores da senha e das chaves de sessão não podem aparecer no código, nos documentos, no Jira ou nos recibos.'),
    ('h2', 'Critério de aceite adicional 19 — Comprovar a entrega protegida'),
    ('p', 'Um recibo identifica o endereço publicado, a versão de código, a versão nativa, a revisão da política de acesso, o manifesto e o horário da verificação. Ele demonstra que uma pessoa sem conta ChatGPT entra com a senha correta, recebe rejeição com senha incorreta, usa a busca e baixa os exercícios; demonstra também que os caminhos do manifesto continuam inacessíveis sem sessão antes e depois do aquecimento do cache e após a saída. As respostas de bloqueio esperadas e as falhas incidentais permanecem identificadas no resultado. Esse critério acrescenta a entrega protegida aos requisitos anteriores e não os substitui.'),
    ('h2', 'Fontes e fronteira deste complemento'),
    ('p', 'Os recibos desta execução estão em tasks/FBI-4991-arquitetura-nextra/execution/: reviews/terminal.json, reviews/diagram-semantics-one.json, reviews/diagram-semantics-one-recheck.json, reviews/diagram-semantics-two.json, reviews/diagram-semantics-two.recheck.json, reviews/root-cases.json, reviews/teaching-recheck.json, curation/summary.json, hosting/lab-bundle-receipt.json, hosting/download-extraction-final.json, hosting/public-access-policy.json, hosting/public-verification.json, hosting/public-network-diagnostic-verification.json, history/history-causal-completion-summary.json e catalog/registration-authority-proposal.json. O resultado funcional reconciliado está em jira-final-preparation/public-functional-assessment.json. Os 63 blocos anteriores, os requisitos R1 a R17 e os critérios 12 a 18 são preservados integralmente. A atualização registra o alcance observado e as pendências; ela não encerra o aceite integral da Story.')
]

url = public['origin']
def content(text):
    if url not in text:
        return [{'type':'text','text':part, **({'marks':[{'type':'link','attrs':{'href':'https://fazcapital.atlassian.net/browse/' + part}}]} if re.fullmatch(r'[A-Z][A-Z0-9]+-\d+', part) else {})} for part in re.split(r'([A-Z][A-Z0-9]+-\d+)',text) if part]
    before, after = text.split(url, 1)
    return [{'type':'text','text':before}, {'type':'text','text':url,'marks':[{'type':'link','attrs':{'href':url}}]}, {'type':'text','text':after}]

appended = [{'type':'heading','attrs':{'level':2},'content':content(text)} if kind == 'h2' else {'type':'paragraph','content':content(text)} for kind, text in sections]
request_adf = copy.deepcopy(original)
request_adf['content'].extend(appended)
assert request_adf['content'][:63] == original['content']
request = {
    'cloudId': '941be6d6-e8c6-481a-9346-6c425e72d22f',
    'issueIdOrKey': 'FBI-4991',
    'contentFormat': 'adf',
    'responseContentFormat': 'adf',
    'fields': {'customfield_10054': request_adf}
}
preview = {
    'hook_event_name': 'PreToolUse',
    'tool_name': 'mcp__codex_apps__atlassian_rovo__legacy__atlassian_rovo_legacy_editjiraissue',
    'metadataSource': {'type': 'live-jira-issue-type-metadata', 'path': 'jira-story-metadata.json', 'captured_at_utc': metadata['captured_at_utc'], 'issueTypeId': '10006', 'descriptionField': 'customfield_10054'},
    'tool_input': request
}
write('jira-update-request.json', request)
write('jira-update-preview.json', preview)
write('request-adf.json', request_adf)
write('appended-adf.json', {'type':'doc','version':1,'content':appended})
(out / 'amendment.md').write_text('\n\n'.join(('## ' if kind == 'h2' else '') + text for kind, text in sections) + '\n')
write('preconditions.json', {
    'prepared_at_utc': observed,
    'publish_authorized_by_this_preparation': False,
    'external_mutations_performed': False,
    'issue_key': issue['key'],
    'expected_current_updated': issue['fields']['updated'],
    'expected_current_adf_sha256_canonical_json': digest(original),
    'proposed_adf_sha256_canonical_json': digest(request_adf),
    'preserved_prefix_blocks': 63,
    'appended_blocks': len(appended),
    'only_mutated_field': 'customfield_10054',
    'current_status': issue['fields']['status']['name'],
    'current_resolution': issue['fields']['resolution'],
    'semantic_review_pending': '94 bounded source-linked judgments complete across terminal3 plus lane46 plus lane45; root-owned final aggregate still to incorporate.',
    'fresh_read_before_write_required': True,
    'precondition_policy': 'Root must reread live issue and compare updated and the canonical JSON hash of customfield10054. On mismatch, rebase appended blocks on new current ADF and rerun both gates. Do not overwrite concurrent edits.',
    'final_readback_required': ['customfield_10054', 'updated', 'status', 'resolution'],
    'pending_draft_pr_url': False,
    'pr_section_policy': 'No PR section is emitted until root supplies an actual draft URL.'
})
source_paths = [
    'reviews/terminal.json', 'reviews/diagram-semantics-one.json', 'reviews/diagram-semantics-one-recheck.json', 'reviews/diagram-semantics-two.json', 'reviews/diagram-semantics-two.recheck.json', 'reviews/root-cases.json', 'reviews/teaching-recheck.json', 'curation/summary.json',
    'hosting/decision.json', 'hosting/lab-bundle-receipt.json', 'hosting/download-extraction-final.json',
    'hosting/public-access-policy.json', 'hosting/public-verification.json', 'hosting/public-network-diagnostic-verification.json',
    'history/history-causal-completion-summary.json', 'catalog/registration-authority-proposal.json'
]
write('evidence-sources.json', {
    'read_at_utc': observed,
    'verification_scope': 'Read and reconcile existing local receipts only; no production, network, PostgreSQL or FazGraph rerun.',
    'sources': [{'path': str((base / path).relative_to(root)), 'sha256': hashlib.sha256((base / path).read_bytes()).hexdigest()} for path in source_paths]
})
gates = []
for name, script in [('catalog','jira-fbi-gate.mjs'),('adf','claude-hook-wrapper.cjs')]:
    path = (pathlib.Path('/Users/augustocarollo/.codex/skills/jira-fbi/scripts') / script).resolve()
    result = subprocess.run(['node', str(path)], input=json.dumps(preview), text=True, capture_output=True)
    output = json.loads(result.stdout) if result.stdout.strip() else None
    decision = output.get('hookSpecificOutput',{}).get('permissionDecision') if output else None
    allowed = result.returncode == 0 and decision != 'deny' and (name == 'adf' or decision == 'allow')
    gates.append({'gate':name,'script':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'validated_at_utc':datetime.now(timezone.utc).isoformat(),'input':'jira-update-preview.json','input_sha256':hashlib.sha256((out/'jira-update-preview.json').read_bytes()).hexdigest(),'execution':'actual JSON preview supplied through stdin','exit_code':result.returncode,'output':output,'stderr':result.stderr,'allowed':allowed})
write('jira-gates.json', gates)
write('preparation-summary.json', {'prepared_at_utc':observed,'verdict':'PREPARED_94_SEMANTIC_JUDGMENTS_PENDING_FINAL_PUBLICATION_AND_ROOT_FRESH_READ','external_mutations':False,'original_blocks':63,'proposed_blocks':len(request_adf['content']),'prefix_unchanged':True,'gates_allow':all(g['allowed'] for g in gates),'gate_metadataSource_enforcement':False,'gate_metadataSource_note':'Current byte-identical .codex/.agents canonical wrappers contain no metadataSource rule; live metadata is preserved as evidence in preview and metadata receipt, not claimed as an enforced script check.','raw_public_verdict':'FAIL','functional_assessment':'FUNCTIONAL_PASS_WITH_RECORDED_CONSOLE_ERRORS','pending':['incorporate root aggregate receipt for94bounded diagram judgments','replace earlier v2deployment and QA statements with final corrected release evidence when available','incorporate actual draftPR URL only after root supplies it','fresh live precondition read by root before write','root owns external write and read-back']})
print(json.dumps({'gates_allow':all(g['allowed'] for g in gates),'original_blocks':63,'proposed_blocks':len(request_adf['content']),'external_mutations':False,'output':str(out)},ensure_ascii=False))
