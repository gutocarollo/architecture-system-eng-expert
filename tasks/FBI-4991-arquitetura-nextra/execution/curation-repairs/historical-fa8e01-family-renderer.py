# Historical family renderer reconstructed for the fa8e01 matrix.
# Globals are supplied by reconstruct_historical_mdx.py inside a temporary directory.
def safe_mdx_text(value):
    parts = re.split('(`+[^`]*`+)', value)
    return ''.join((part if part.startswith('`') else part.replace('<', '&lt;').replace('>', '&gt;').replace('{', '&#123;').replace('}', '&#125;') for part in parts))

def link_item(item):
    path = item.get('path') or item['repo']
    rev = item.get('revision', '')
    label = item['repo'] + ' / ' + Path(path).name + (' @ ' + rev[:8] if rev else '')
    license = item.get('license', {})
    spdx = license.get('license_expression') or license.get('license_spdx') or 'identificador não determinado'
    suffix = '; licença [' + spdx + '](' + license['url'] + ')' if license.get('url') else '; licença pendente de comprovação'
    return '[' + label + '](' + item['url'] + ')' + suffix
for group, info in group_info.items():
    rows = [e for e in entries if e['primary_group'] == group]
    title = 'Curadoria: ' + info['title']
    text = '---\ntitle: ' + json.dumps(title, ensure_ascii=False) + '\ndescription: ' + json.dumps('Fontes, skills, versões, licenças e lacunas dos conceitos de ' + info['title'] + '.', ensure_ascii=False) + '\ndiataxis: reference\n---\n\n# ' + title + '\n\n'
    text += 'Esta página conserva os conceitos canônicos desta família, com links diretos para as fontes. A contagem de estrelas compara os packs candidatos identificados em cada item. O [método e o recorte datado de tendência](/referencia/curadoria/#como-comparamos-skills) explicam o universo e o período; uma orientação de apoio não implementa o padrão no programa.\n\n'
    text += 'Uma correspondência autoral significa que o autor selecionou o mecanismo e suas fontes. A revisão independente desta nova matriz ainda é um gate separado. Uma pendência continua sendo requisito aberto; nenhum conceito recebeu dispensa por não se aplicar.\n\n'
    for row in rows:
        if heading_slugs[row['concept_id']] != row['concept_id']:
            text += '<span id="' + row['concept_id'] + '" />\n\n'
        text += '## ' + row['canonical_name'] + '\n\n'
        text += 'O identificador canônico é `' + row['concept_id'] + '`. '
        if row['status'] == 'PENDING':
            text += '**A curadoria deste item permanece pendente.** ' + ' '.join((i.get('reason', 'A fonte ou a licença precisa ser verificada.') for i in row['issues'])) + '\n\n'
        elif row['independent_review'] != 'PENDING':
            text += '**A primeira revisão independente aceitou este recorte.** O fingerprint semântico foi preservado; as observações dessa revisão continuam no registro do item.\n\n'
        else:
            text += '**Há uma correspondência autoral reparada com fontes primárias.** A rechecagem independente desta versão continua pendente.\n\n'
        text += safe_mdx_text(row['mechanism']) + '\n\n'
        text += 'A base de estudo é ' + '; '.join((link_item(i) for i in row['base'])) + '. A aplicação ou candidato de aplicação é ' + '; '.join((link_item(i) for i in row['application'])) + '.\n\n'
        skill = row['skill']
        stars = skill['repository_metadata'].get('stars')
        observed = skill['repository_metadata'].get('observed_utc', '')
        text += 'A orientação pública selecionada é ' + link_item(skill) + '. Seu pack tinha **' + str(stars) + ' estrelas** na consulta `' + observed + '`. Ele ocupa a primeira posição por estrelas entre as ' + str(len(row['skill_candidates'])) + ' candidatas de assunto selecionadas para este item; esse recorte não é um ranking de todas as skills existentes.\n\n'
        app_hits = [h for f in row['source_evidence'] if f['role'] == 'application' for h in f['hits']]
        if app_hits:
            h = app_hits[0]
            text += 'Para conferir o mecanismo no produto, comece por [este trecho do código](' + h['url'] + '). ' + safe_mdx_text(h.get('claim', 'O localizador textual ajuda a encontrar o fluxo; ele não substitui a leitura do mecanismo e de seus limites.')) + '\n\n'
        text += safe_mdx_text(row['limits']) + '\n\n'
        for decision in row.get('decision_evidence', []):
            text += 'A decisão pública que sustenta esta leitura está na [fonte do responsável pelo produto](' + decision['url'] + '). ' + safe_mdx_text(decision.get('claim', '')) + '\n\n'
        if row['learning']:
            l = row['learning']
            text += 'No curso, [abra o caso aplicado](' + l['destinations']['journey'] + ') e [consulte a ação e o probe deste conceito](' + l['destinations']['concept'] + '). A prática local ensina o recorte declarado; ela não substitui o código OSS nem comprova uma implantação na nossa stack.\n\n'
    text += 'Volte à [matriz completa da curadoria](/referencia/curadoria/).\n'
    (DEST / (slugs[group] + '.mdx')).write_text(text)
