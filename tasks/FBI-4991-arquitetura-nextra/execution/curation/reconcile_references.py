#!/usr/bin/env python3
"""Render the forty priorities from the canonical per-concept source matrix."""
import json
import collections
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
matrix = json.loads((BASE / 'matrix.json').read_text())
coverage = json.loads((ROOT / 'tasks/architecture-course-2026-10-14/evidence/coverage.json').read_text())
by_id = {row['concept_id']: row for row in matrix['concepts']}
group_slugs = {group['group']: Path(group['reference_path']).stem for group in coverage['groups'] if group['group'] != 18}

def concept_link(row):
    return '/referencia/curadoria/' + group_slugs[row['primary_group']] + '/#' + row['concept_id']

def source_link(source):
    revision = source.get('revision', '')[:8]
    label = source['repo'] + (' @ ' + revision if revision else '')
    return '[' + label + '](' + source['url'] + ')'

text = '''---
title: "Arquitetura na prática: Makershub"
description: Quarenta temas para estudar decisões de arquitetura com casos históricos do MakersHub e modelos financeiros.
diataxis: reference
---

# Arquitetura na prática: Makershub

Use esta seleção de **40 temas prioritários** para escolher uma decisão de arquitetura e chegar ao caso que ajuda a estudá-la. A trilha combina mudanças históricas do MakersHub com modelos financeiros hipotéticos. Cada linha reúne os conceitos do tema, as fontes de estudo e o caso aplicado.

Os números contam coisas diferentes. Esta seleção tem 40 temas, que apontam para **46 conceitos distintos** da [curadoria completa dos 310 conceitos](/referencia/curadoria/). Um tema pode reunir vários conceitos: “Retry + Exponential Backoff + Jitter” ocupa uma linha aqui e reúne três conceitos. A [matriz de conceitos e casos](/jornadas/matriz/) agrupa o catálogo em **15 casos principais**; um mesmo caso pode ajudar a estudar vários temas desta seleção.

Comece pelo caso aplicado para conhecer o problema e a comparação proposta. Depois, consulte as fontes para examinar o mecanismo em uma biblioteca ou em um produto de código aberto. Cada exercício informa o que você pode observar e quais garantias ainda exigem outra experiência. A presença de um conceito nesta seleção não significa que o padrão completo esteja implementado no MakersHub ou no laboratório.

| # | Tema prioritário | Conceitos e fontes completas | Caso aplicado | Base de estudo | Código da aplicação |
| --- | --- | --- | --- | --- | --- |
'''
receipts = []
for priority in coverage['priority_entries']:
    rows = [by_id[key] for key in priority['concept_ids']]
    concepts = '; '.join('[' + row['canonical_name'] + '](' + concept_link(row) + ')' for row in rows)
    journeys = list(dict.fromkeys(row['learning']['destinations']['journey'] for row in rows))
    cases = '; '.join('[Abrir o caso](' + journey + ')' for journey in journeys)
    bases = list(dict.fromkeys(source_link(row['base'][0]) for row in rows))
    applications = list(dict.fromkeys(source_link(row['application'][0]) for row in rows))
    pending = [row['canonical_name'] for row in rows if row['status'] != 'AUTHOR_SOURCE_MATCH']
    status = 'Pendente: ' + ', '.join(pending) if pending else 'Correspondência proposta; revisão independente pendente.'
    text += '| ' + str(priority['priority_id']) + ' | ' + priority['original_label'] + ' | ' + concepts + ' | ' + cases + ' | ' + '; '.join(bases) + ' | ' + '; '.join(applications) + ' |\n'
    receipts.append({'priority_id': priority['priority_id'], 'concept_ids': priority['concept_ids'], 'concept_reference_urls': [concept_link(row) for row in rows], 'pending': pending})
text += '''
## Como os mecanismos se combinam

Uma operação pode gravar seu estado e a intenção de publicar um evento na mesma transação local. Uma outbox preserva essa intenção; um publicador ou CDC a transporta depois. O consumidor precisa identificar repetições e delimitar o efeito protegido. Uma saga coordena etapas e compensações quando a operação atravessa participantes. CQRS pode separar os modelos de comando e consulta quando cada caminho tem necessidades diferentes. Essas escolhas podem se combinar, mas não formam uma sequência obrigatória de ferramentas.

O exemplo OSS mostra um mecanismo no recorte de código citado. O laboratório local permite observar uma condição controlada e seu efeito sobre um caso financeiro. Os [recibos do ambiente](/referencia/evidencias/) delimitam o que foi medido na nossa stack, e o [método de curadoria](/referencia/curadoria/#como-comparamos-skills) explica a comparação datada entre os packs públicos.
'''
(ROOT / 'content/referencia/prioritarios.mdx').write_text(text)
(BASE / 'priority-reconciliation.json').write_text(json.dumps({'canonical_concepts': 310, 'priority_entries': receipts}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'priorities_reconciled': len(receipts), 'priority_concept_memberships': sum(len(row['concept_ids']) for row in receipts)}))

def normalized(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', value)

lookup = collections.defaultdict(set)
for concept in coverage['concepts']:
    names = [concept['canonical_name'], *concept['aliases'], *[item['original_label'] for item in concept['source_occurrences']]]
    for group in concept['groups']:
        for name in names:
            lookup[(group, normalized(name))].add(concept['concept_id'])
catalog_receipts = []
for catalog in sorted((ROOT / 'content/referencia/catalogo').glob('[0-9]*.mdx')):
    group = int(catalog.name[:2])
    contents = catalog.read_text()
    sections = re.split(r'(^## .+$)', contents, flags=re.M)
    if group == 10:
        row = by_id['ddd']
        marker = '{/* current-curation:ddd */}'
        if marker not in sections[0]:
            sections[0] += marker + '\n\nA [curadoria de DDD](' + concept_link(row) + ') reúne a modelagem, o aplicativo financeiro, a skill pública e as provas de código e licença do conceito que organiza esta família.\n\n'
        catalog_receipts.append({'file': str(catalog.relative_to(ROOT)), 'heading': 'Page introduction: DDD', 'concept_id': 'ddd', 'curation_url': concept_link(row)})
    for index in range(1, len(sections), 2):
        heading = sections[index][3:]
        candidates = lookup.get((group, normalized(heading)), set())
        if heading in ['Read Replica — replicação', 'Read Replica — leitura']:
            candidates = {'read-replica'}
        if len(candidates) != 1:
            continue
        concept_id = next(iter(candidates))
        row = by_id[concept_id]
        marker = '{/* current-curation:' + concept_id + ' */}'
        if marker not in sections[index + 1]:
            sentence = '\n\n' + marker + '\n\nA [curadoria de ' + row['canonical_name'] + '](' + concept_link(row) + ') reúne a skill pública, o código da base e da aplicação, as versões, as licenças e os limites deste conceito.\n'
            body = sections[index + 1]
            next_anchor = re.search(r'\n<span id="g\d+-e\d+" />\s*$', body)
            if next_anchor:
                sections[index + 1] = body[:next_anchor.start()].rstrip() + sentence + '\n' + body[next_anchor.start():].lstrip('\n')
            else:
                sections[index + 1] = body.rstrip() + sentence + '\n'
        catalog_receipts.append({'file': str(catalog.relative_to(ROOT)), 'heading': heading, 'concept_id': concept_id, 'curation_url': concept_link(row)})
    catalog.write_text(''.join(sections))
missing = sorted(set(by_id) - {row['concept_id'] for row in catalog_receipts})
(BASE / 'catalog-reconciliation.json').write_text(json.dumps({'entries_linked': len(catalog_receipts), 'unique_concepts_linked': len({row['concept_id'] for row in catalog_receipts}), 'concepts_without_catalog_link': missing, 'entries': catalog_receipts}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'catalog_entries_linked': len(catalog_receipts), 'concepts_without_catalog_link': missing}, ensure_ascii=False))
